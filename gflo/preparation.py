"""Trusted reviewed-plan preparation; no implicit scheduling or acceptance."""

from __future__ import annotations

import json
from typing import Annotated, Literal

from pydantic import Field

from gflo.artifacts import ArtifactStore
from gflo.broker import SourceBundle
from gflo.controller import RunPlan
from gflo.gates import ProcessGate
from gflo.model import ModelProfile
from gflo.planning import PlanProposal, _paths, validate_tasks
from gflo.planning import RepositoryFeatureRequest as RepositoryFeatureRequest
from gflo.records import ContextBudget, Digest, Identifier, Record, WorkAtom
from gflo.repository import FileEdit, Repository, Selection, SnapshotSource, SourceRef
from gflo.worker import InputSnapshot, within


class TaskReview(Record):
    """Controller-authored inputs and checks; never inferred from proposal prose."""

    execution_paths: Annotated[tuple[str, ...], Field(min_length=1, max_length=100)]
    context_paths: Annotated[tuple[str, ...], Field(max_length=100)]
    gates: Annotated[dict[Identifier, ProcessGate], Field(min_length=1, max_length=16)]
    context_bytes: Annotated[int, Field(ge=1, le=262144)] = 65536
    execution_bytes: Annotated[int, Field(ge=1, le=262144)] = 262144


class PlanReview(Record):
    kind: Literal["plan-review-v1"] = "plan-review-v1"
    request_digest: Digest
    proposal_digest: Digest
    tasks: Annotated[dict[Identifier, TaskReview], Field(min_length=1, max_length=12)]
    model_profile: ModelProfile
    deployment: str
    context_budget: ContextBudget
    max_attempts: Annotated[int, Field(ge=1, le=10)] = 2
    max_model_turns: Annotated[int, Field(ge=1, le=4)] = 3


class PreparedTask(Record):
    kind: Literal["prepared-repository-task-v1"] = "prepared-repository-task-v1"
    request_digest: Digest
    proposal_digest: Digest
    review_digest: Digest
    task_id: Identifier
    source: SourceRef
    context: Selection
    execution: Selection
    run: RunPlan


def prepare_task(
    artifacts: ArtifactStore,
    request: RepositoryFeatureRequest,
    proposal: PlanProposal,
    review: PlanReview,
    task_id: str,
    *,
    current_source: SourceRef,
) -> PreparedTask:
    """Materialize one reviewed root task; publish evidence but do not submit or run."""
    if current_source != request.source:
        raise ValueError("Source advanced since product planning")
    task = next((t for t in proposal.tasks if t.task_id == task_id), None)
    if task is not None and task.depends_on:
        raise ValueError("Dependent task requires accepted-base progression")
    return _materialize(artifacts, request, proposal, review, task_id, current_source, ())


def _materialize(
    artifacts: ArtifactStore,
    request: RepositoryFeatureRequest,
    proposal: PlanProposal,
    review: PlanReview,
    task_id: str,
    source: SourceRef,
    accepted_evidence: tuple[str, ...],
) -> PreparedTask:
    """Internal seam: progression verifies predecessor acceptances before calling."""
    request = RepositoryFeatureRequest.model_validate(request)
    review = PlanReview.model_validate(review)
    proposal = PlanProposal.model_validate(proposal)
    if review.request_digest != request.digest() or review.proposal_digest != proposal.digest():
        raise ValueError("Review does not bind this request and proposal")
    if proposal.questions:
        raise ValueError("Resolve proposal questions before preparation")
    repository = Repository(SnapshotSource(artifacts, source))
    order = validate_tasks(
        proposal,
        request_digest=request.digest(),
        allowed_paths=request.allowed_paths,
        source_paths=repository.source.files.keys(),
        environments=request.environments.keys(),
        requirements=request.requirements.keys(),
    )
    if set(review.tasks) != set(order):
        raise ValueError("Review must cover exactly the proposed tasks")
    task = next((t for t in proposal.tasks if t.task_id == task_id), None)
    if task is None:
        raise ValueError("Unknown task")
    policy = review.tasks[task_id]
    _paths(policy.execution_paths)
    _paths(policy.context_paths)
    if not set(policy.context_paths) <= set(policy.execution_paths):
        raise ValueError("Context must be available in execution inputs")
    required = set(task.read_paths) | {
        p for p in repository.source.files if within(p, task.writable_paths)
    }
    if not required <= set(policy.execution_paths):
        raise ValueError("Execution inputs omit declared reads or existing writable files")
    execution = repository.select(
        policy.execution_paths, purpose="execution", max_bytes=policy.execution_bytes
    )
    context = repository.select(policy.context_paths, max_bytes=policy.context_bytes)
    if context.omitted:
        raise ValueError("Reviewed context exceeds its budget")
    assert execution.bundle is not None
    # Bind the full snapshot in the legacy revision field, without reinterpreting
    # historical InputSnapshot hashes or changing the controller's record schema.
    revision = f"repository-snapshot-v1:{source.artifact_digest}"
    identity = f"prepared-{request.digest()[:16]}-{proposal.digest()[:16]}-{review.digest()[:16]}"
    if source != request.source or accepted_evidence:
        identity += (
            "-"
            + artifacts.publish(
                json.dumps(
                    [source.model_dump(mode="json"), accepted_evidence], sort_keys=True
                ).encode()
            )[:16]
        )
    atom = WorkAtom.model_validate_json(
        json.dumps(
            dict(
                atom_id=f"{identity}/{task.digest()[:16]}",
                graph_revision=proposal.digest(),
                objective=json.dumps(
                    {
                        "product_objective": request.objective,
                        "task_objective": task.objective,
                        "requirements": {k: request.requirements[k] for k in task.requirement_ids},
                        "interfaces": task.interface_contracts,
                        "repository_files": execution.repository_file_count,
                        "execution_is_whole_repository": execution.whole_repository,
                    }
                ),
                non_goals=["Modify omitted repository files", "Accept own work"],
                requirement_ids=task.requirement_ids,
                product_modules=[request.feature_id],
                source_revision=revision,
                inputs_digest=InputSnapshot(
                    source_digest=execution.bundle.digest(), source_revision=revision
                ).digest(),
                writable_paths=task.writable_paths,
                prohibited_paths=[],
                dependency_artifacts=accepted_evidence,
                upstream_contracts=[],
                capability_profile="python-snapshot-v1" if accepted_evidence else "python-pilot-v1",
                network_profile="none-v1",
                credential_profile="none-v1",
                sandbox_profile="pilot-v1",
                allowed_tools=["read", "edit"],
                required_gates=[
                    dict(gate_id=k, validator_digest=v.digest())
                    for k, v in sorted(policy.gates.items())
                ],
                context_budget=review.context_budget.model_dump(),
                max_attempts=review.max_attempts,
                expected_outputs=[
                    dict(
                        name="candidate",
                        schema_digest=artifacts.publish(
                            json.dumps(SourceBundle.model_json_schema(), sort_keys=True).encode()
                        ),
                    )
                ],
                idempotency_key=f"{identity}/{task.digest()[:16]}",
                integration_key=request.feature_id,
            )
        )
    )
    run = RunPlan(
        atom=atom,
        source=execution.bundle,
        gates=policy.gates,
        model_profile=review.model_profile,
        deployment=review.deployment,
        broker_image=request.environments[task.environment_id].image,
        max_model_turns=review.max_model_turns,
        selected_paths=policy.context_paths,
    )
    prepared = PreparedTask(
        request_digest=request.digest(),
        proposal_digest=proposal.digest(),
        review_digest=review.digest(),
        task_id=task_id,
        source=source,
        context=context,
        execution=execution,
        run=run,
    )
    for record in (request, proposal, review, prepared):
        artifacts.publish(record.canonical().encode())
    return prepared


def lift_candidate(
    artifacts: ArtifactStore,
    prepared_digest: str,
    candidate: SourceBundle,
    *,
    current_source: SourceRef,
) -> SourceRef:
    """Lift a task result into a proposed snapshot; this grants no acceptance."""
    prepared = PreparedTask.model_validate_json(artifacts.read(prepared_digest))
    candidate = SourceBundle.model_validate(candidate)
    if current_source != prepared.source:
        raise ValueError("Source advanced since task preparation")
    original = prepared.run.source.files
    if not original.keys() <= candidate.files.keys():
        raise ValueError("Candidate deletes execution inputs")
    repository = Repository(SnapshotSource(artifacts, prepared.source))
    edits = {}
    for path, content in candidate.files.items():
        if path in original and content == original[path]:
            continue
        if path not in original and path in repository.source.files:
            raise ValueError("Candidate overwrites an omitted file")
        prior = prepared.execution.file_identities.get(path)
        edits[path] = FileEdit(
            expected_digest=prior.content_digest if prior else None, content=content
        )
    if not edits:
        repository.source.retain(artifacts)
        return prepared.source
    return repository.apply(
        artifacts,
        edits,
        current_source=current_source,
        writable_paths=prepared.run.atom.writable_paths,
    )
