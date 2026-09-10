"""Compile bounded operator policy, then plan and execute without per-task review."""

from __future__ import annotations

import fcntl
import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import Field

from gflo.artifacts import ArtifactStore
from gflo.broker import DockerBroker
from gflo.contracts import CONTRACT_PROFILES, task_interfaces
from gflo.escalation import pending_review, review_handoff
from gflo.gates import ProcessGate
from gflo.ledger import WorkLedger
from gflo.model import LocalModel, ModelProfile
from gflo.planning import (
    PlanProposal,
    RepositoryFeatureRequest,
    _paths,
    draft_feature,
    validate_tasks,
)
from gflo.preparation import PlanReview, TaskReview
from gflo.progression import FeaturePlan, run_feature
from gflo.records import ContextBudget, Digest, Identifier, Record
from gflo.repository import Repository, SnapshotSource, SourceRef


class FeaturePolicy(Record):
    """Trusted exact-file authorization for one request; never produced by its planner."""

    kind: Literal["feature-policy-v1"] = "feature-policy-v1"
    request_digest: Digest
    file_gates: Annotated[dict[str, ProcessGate], Field(min_length=1, max_length=16)]
    execution_paths: Annotated[tuple[str, ...], Field(min_length=1, max_length=100)]
    planning_paths: Annotated[tuple[str, ...], Field(min_length=1, max_length=16)]
    integration_gates: Annotated[dict[Identifier, ProcessGate], Field(min_length=1, max_length=16)]
    environment_id: Identifier
    model_profile: ModelProfile
    deployment: str
    context_budget: ContextBudget
    max_tasks: Annotated[int, Field(ge=1, le=12)] = 6
    max_attempts: Annotated[int, Field(ge=1, le=10)] = 2
    max_model_turns: Annotated[int, Field(ge=1, le=4)] = 3
    max_reserved_tokens: Annotated[int, Field(ge=1)] = 368640


def _validate_policy(
    store: ArtifactStore, request: RepositoryFeatureRequest, policy: FeaturePolicy
) -> Repository:
    if policy.request_digest != request.digest():
        raise ValueError("Policy does not bind this exact request")
    for selection in (tuple(policy.file_gates), policy.execution_paths, policy.planning_paths):
        _paths(selection)
    if set(policy.file_gates) != set(request.allowed_paths):
        raise ValueError("Policy must supply checks for every exact allowed file")
    if any(a != b and b.startswith(a + "/") for a in policy.file_gates for b in policy.file_gates):
        raise ValueError("Policy allows files, not directory scopes")
    if not set(policy.file_gates) <= set(policy.execution_paths):
        raise ValueError("Execution inputs must include every authorized output file")
    if policy.environment_id not in request.environments:
        raise ValueError("Unknown policy environment")
    # Reserve the maximum across all retries, before spending any inference.
    reserved = 6 * 12288 + (
        policy.max_tasks
        * policy.max_attempts
        * policy.max_model_turns
        * policy.context_budget.total_tokens
    )
    if reserved > policy.max_reserved_tokens:
        raise ValueError("Policy exceeds whole-feature reserved token budget")
    repository = Repository(SnapshotSource(store, request.source))
    paths = set(repository.source.files)
    if any(any(p.startswith(a + "/") for p in paths) for a in policy.file_gates):
        raise ValueError("Authorized output is a directory, not an exact file")
    if not set(policy.execution_paths) <= paths | set(policy.file_gates):
        raise ValueError("Execution input is neither existing source nor authorized output")
    if not set(policy.planning_paths) <= set(policy.execution_paths):
        raise ValueError("Planning inputs must belong to the policy execution selection")
    repository.select(policy.planning_paths, purpose="execution")
    repository.select(tuple(p for p in policy.execution_paths if p in paths), purpose="execution")
    return repository


def compile_feature(
    store: ArtifactStore,
    request: RepositoryFeatureRequest,
    proposal: PlanProposal,
    policy: FeaturePolicy,
) -> FeaturePlan:
    """Derive trusted task checks from exact write paths; reject unhandled proposals."""
    request = RepositoryFeatureRequest.model_validate(request)
    policy = FeaturePolicy.model_validate(policy)
    proposal = PlanProposal.model_validate(proposal)
    repository = _validate_policy(store, request, policy)
    if policy.model_profile.profile_id in CONTRACT_PROFILES:
        for task in proposal.tasks:
            task_interfaces(
                task.interface_contracts,
                task.read_paths + task.writable_paths,
                task.requirement_ids,
            )
    if proposal.questions:
        raise ValueError("Resolve proposal questions before policy compilation")
    if len(proposal.tasks) > policy.max_tasks:
        raise ValueError("Proposal exceeds policy task budget")
    order = validate_tasks(
        proposal,
        request_digest=request.digest(),
        allowed_paths=request.allowed_paths,
        source_paths=repository.source.files.keys(),
        environments=(policy.environment_id,),
        requirements=request.requirements.keys(),
    )
    tasks = {t.task_id: t for t in proposal.tasks}
    available = set(repository.source.files)
    reviews = {}
    for task_id in order:
        task = tasks[task_id]
        if not set(task.writable_paths) <= policy.file_gates.keys():
            raise ValueError("Task write scope has no exact policy gate")
        if not set(task.read_paths) <= set(policy.execution_paths):
            raise ValueError("Task reads outside policy execution inputs")
        execution = tuple(p for p in policy.execution_paths if p in available)
        context = tuple(
            p for p in execution if p in set(task.read_paths) | set(task.writable_paths)
        )
        reviews[task_id] = TaskReview(
            execution_paths=execution,
            context_paths=context,
            gates={
                f"file-{i}": policy.file_gates[p] for i, p in enumerate(sorted(task.writable_paths))
            },
        )
        available.update(task.writable_paths)
    if not set(policy.execution_paths) <= available:
        raise ValueError("Plan leaves required execution outputs without a producer")
    plan = FeaturePlan(
        request=request,
        proposal=proposal,
        review=PlanReview(
            request_digest=request.digest(),
            proposal_digest=proposal.digest(),
            tasks=reviews,
            model_profile=policy.model_profile,
            deployment=policy.deployment,
            context_budget=policy.context_budget,
            max_attempts=policy.max_attempts,
            max_model_turns=policy.max_model_turns,
        ),
        integration=TaskReview(
            execution_paths=policy.execution_paths, context_paths=(), gates=policy.integration_gates
        ),
        integration_environment=policy.environment_id,
    )
    for record in (request, proposal, policy, plan):
        store.publish(record.canonical().encode())
    store.publish(
        json.dumps(
            {"policy_digest": policy.digest(), "plan_digest": plan.digest()}, sort_keys=True
        ).encode()
    )
    return plan


def build_feature(
    ledger: WorkLedger,
    request: RepositoryFeatureRequest,
    policy: FeaturePolicy,
    output: Path,
    current_source: Callable[[], SourceRef],
    *,
    planner: Callable[..., dict[str, Any]] = draft_feature,
    model_factory: Callable[..., LocalModel] = LocalModel,
    broker_factory: Callable[..., DockerBroker] = DockerBroker,
) -> dict[str, Any]:
    """One pinned build; repeat to replay execution, never silently retry planning.

    Policy is operator input. The output directory is trusted control-plane state,
    separate from worker inputs. Interrupted planning requires a new build directory.
    """
    request = RepositoryFeatureRequest.model_validate(request)
    policy = FeaturePolicy.model_validate(policy)
    repository = _validate_policy(ledger.artifacts, request, policy)
    if current_source() != request.source:
        raise ValueError("External source differs from the authorized request")
    output.mkdir(parents=True, exist_ok=True)
    with (output / ".build.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        binding = {
            "request_digest": request.digest(),
            "policy_digest": policy.digest(),
            "artifact_store": str(ledger.artifacts.root.resolve()),
        }
        manifest = output / "binding.json"
        if manifest.exists():
            if json.loads(manifest.read_text()) != binding:
                raise ValueError("Build directory belongs to a different request, policy or store")
        else:
            manifest.write_text(json.dumps(binding, sort_keys=True) + "\n")
        for record in (request, policy):
            ledger.artifacts.publish(record.canonical().encode())
        planning = output / "planning"
        result: dict[str, Any] = dict(status="planning-halt", **binding)
        if not planning.exists():
            planner(
                request,
                policy.model_profile.model_copy(update={"profile_id": "vllm-python-worker-v1"}),
                planning,
                deployment=policy.deployment,
                repository=repository,
                context_paths=policy.planning_paths,
                **(
                    {"structured_interfaces": True}
                    if policy.model_profile.profile_id in CONTRACT_PROFILES
                    else {}
                ),
            )
        state_path = planning / "result.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        if state.get("questions"):
            result.update(status="needs-info", questions=state["questions"])
        elif state.get("status") == "needs-review":
            proposal = PlanProposal.model_validate_json((planning / "proposal.json").read_bytes())
            if state.get("proposal_digest") != proposal.digest():
                raise ValueError("Retained proposal differs from planning result")
            try:
                plan = compile_feature(ledger.artifacts, request, proposal, policy)
            except ValueError as exc:
                result.update(status="policy-halt", reason=str(exc))
            else:
                (output / "feature-plan.json").write_text(plan.canonical() + "\n")
                # Clear a previous success before rechecking findings or resuming work.
                # If execution raises, retained state must not claim current acceptance.
                result.update(status="execution-interrupted")
                (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
                executed = run_feature(
                    ledger,
                    plan,
                    current_source,
                    model_factory=model_factory,
                    broker_factory=broker_factory,
                )
                result.update(
                    status=executed.status, feature_result=executed.model_dump(mode="json")
                )
        else:
            result["planning_status"] = state.get("status", "interrupted")
        halted = result.get("feature_result", {}).get("halted_atom")
        if halted and (
            ledger.status(halted)["status"] == "quarantined" or pending_review(ledger, halted)
        ):
            packet = review_handoff(ledger, halted)
            payload = json.dumps(packet, indent=2) + "\n"
            (output / "review-handoff.json").write_text(payload)
            result["review_handoff_digest"] = ledger.artifacts.publish(payload.encode())
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        ledger.artifacts.publish(json.dumps(result, sort_keys=True).encode())
        return result
