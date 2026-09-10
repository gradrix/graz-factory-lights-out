"""Sequential reviewed feature execution with replayed acceptance evidence.

Derived snapshots are internal proposals. No Git promotion or external source CAS.
"""

from __future__ import annotations

import fcntl
import json
from collections.abc import Callable
from typing import Annotated, Any, Literal

from pydantic import Field

from gflo.broker import DockerBroker, SourceBundle
from gflo.controller import Controller, prepare_run
from gflo.gates import ProcessGate, run_gate
from gflo.ledger import Conflict, WorkLedger
from gflo.model import LocalModel
from gflo.planning import PlanProposal, validate_tasks
from gflo.preparation import (
    PlanReview,
    PreparedTask,
    RepositoryFeatureRequest,
    TaskReview,
    _materialize,
    lift_candidate,
)
from gflo.records import Digest, Identifier, Record, RetryPlan, WorkAtom
from gflo.repository import Repository, Selection, SnapshotSource, SourceRef
from gflo.worker import InputSnapshot


class FeaturePlan(Record):
    kind: Literal["reviewed-feature-v1"] = "reviewed-feature-v1"
    request: RepositoryFeatureRequest
    proposal: PlanProposal
    review: PlanReview
    integration: TaskReview
    integration_environment: Identifier


class FeatureCheck(Record):
    kind: Literal["feature-check-v1"] = "feature-check-v1"
    atom: WorkAtom
    source: SourceBundle
    gates: dict[str, ProcessGate]
    broker_image: str


class FeatureResult(Record):
    kind: Literal["feature-result-v1"] = "feature-result-v1"
    plan_digest: Digest
    source: SourceRef
    status: Literal["accepted", "task-halt", "integration-halt"]
    tasks: Annotated[tuple[Digest, ...], Field(max_length=12)]
    integration_atom: str | None = None
    integration_selection: Selection | None = None
    halted_atom: str | None = None


def _accepted(ledger: WorkLedger, prepared: PreparedTask) -> str:
    """Verify durable contract, candidate, receipt bytes and later findings."""
    atom = prepared.run.atom
    if ledger.run_plan(atom.atom_id) != prepared.run.canonical().encode():
        raise Conflict("Retained task differs from reviewed preparation")
    state = ledger.status(atom.atom_id)
    if state["status"] != "accepted" or state["contract"] != atom.model_dump(mode="json"):
        raise Conflict("Provider is not the exact accepted task")
    accepted = ledger.accept(
        ledger.active_lease(atom.atom_id), current_inputs_digest=atom.inputs_digest
    )
    return ledger.artifacts.publish(accepted.canonical().encode())


def _check(
    ledger: WorkLedger,
    plan: FeatureCheck,
    broker: DockerBroker,
    fresh: Callable[[], None],
) -> dict[str, Any]:
    """Validation-only final task, retained separately from model RunPlans."""
    with (ledger.artifacts.root / ".controller.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fresh()
        ledger.artifacts.publish(plan.source.canonical().encode())
        ledger.submit(plan.atom)
        ledger.bind_run(plan.atom.atom_id, ledger.artifacts.publish(plan.canonical().encode()))
        broker.reconcile()
        ledger.reconcile()
        state = ledger.status(plan.atom.atom_id)
        if state["status"] == "accepted":
            ledger.accept(
                ledger.active_lease(plan.atom.atom_id),
                current_inputs_digest=plan.atom.inputs_digest,
            )
            return state
        if state["status"] == "quarantined":
            return state
        broker.qualify()
        fresh()
        if state["status"] in ("ready", "retry-ready"):
            retry = None
            if state["status"] == "retry-ready":
                prior = state["attempts"][-1]
                retry = RetryPlan(
                    failure_event=prior["events"][-1]["event_id"],
                    strategy="Repeat reviewed final validation after recovery",
                    new_evidence=ledger.artifacts.publish(json.dumps(prior).encode()),
                )
            lease = ledger.claim(
                plan.atom.atom_id, "feature-check-v1", retry=retry, lease_seconds=1800
            )
        else:
            lease = ledger.active_lease(plan.atom.atom_id)
            if lease.owner != "feature-check-v1":
                raise Conflict("Different owner holds final validation")
        if ledger.status(plan.atom.atom_id)["status"] == "leased":
            ledger.start(lease)
        if ledger.status(plan.atom.atom_id)["status"] == "running":
            ledger.candidate(lease, plan.source.digest())
        if ledger.status(plan.atom.atom_id)["candidate_digest"] != plan.source.digest():
            raise Conflict("Final candidate differs from reviewed source")
        for gate_id, gate in plan.gates.items():
            fresh()
            receipts = ledger.status(plan.atom.atom_id)["attempts"][-1]["gate_receipts"]
            receipt = next((r for r in receipts if r["gate_id"] == gate_id), None)
            if receipt is None:
                receipt = run_gate(ledger, broker, lease, gate_id, gate).model_dump(mode="json")
            if receipt["outcome"] != "pass":
                ledger.fail(lease, "Combined feature validation did not pass")
                return ledger.status(plan.atom.atom_id)
        fresh()
        ledger.accept(lease, current_inputs_digest=plan.atom.inputs_digest)
        return ledger.status(plan.atom.atom_id)


def run_feature(
    ledger: WorkLedger,
    plan: FeaturePlan,
    current_source: Callable[[], SourceRef],
    *,
    model_factory: Callable[..., LocalModel] = LocalModel,
    broker_factory: Callable[..., DockerBroker] = DockerBroker,
) -> FeatureResult:
    """Run/replay one reviewed graph in deterministic order; stop on any failed task.

    Caller owns the original source and review. The callback checks that external
    source stays pinned; cumulative internal snapshots advance only through verified
    accepted tasks. Repeating this call reconstructs progress from durable evidence.
    """
    plan = FeaturePlan.model_validate(plan)
    store = ledger.artifacts
    request, proposal, review = plan.request, plan.proposal, plan.review
    if review.request_digest != request.digest() or review.proposal_digest != proposal.digest():
        raise Conflict("Feature review does not bind request/proposal")
    if proposal.questions:
        raise Conflict("Resolve feature questions before execution")
    if plan.integration_environment not in request.environments:
        raise Conflict("Unknown combined validation environment")
    root = Repository(SnapshotSource(store, request.source))
    order = validate_tasks(
        proposal,
        request_digest=request.digest(),
        allowed_paths=request.allowed_paths,
        source_paths=root.source.files.keys(),
        environments=request.environments.keys(),
        requirements=request.requirements.keys(),
    )
    if set(review.tasks) != set(order):
        raise Conflict("Review must cover exactly the proposed tasks")
    completed: list[PreparedTask] = []
    evidence: list[str] = []

    def fresh() -> None:
        if SourceRef.model_validate(current_source()) != request.source:
            raise Conflict("External source advanced during feature execution")
        for package, digest in zip(completed, evidence, strict=True):
            if _accepted(ledger, package) != digest:
                raise Conflict("Accepted predecessor evidence changed")

    def finish(
        status: Literal["accepted", "task-halt", "integration-halt"],
        source: SourceRef,
        *,
        integration_atom: str | None = None,
        integration_selection: Selection | None = None,
        halted_atom: str | None = None,
    ) -> FeatureResult:
        result = FeatureResult(
            plan_digest=plan.digest(),
            source=source,
            status=status,
            tasks=tuple(p.digest() for p in completed),
            integration_atom=integration_atom,
            integration_selection=integration_selection,
            halted_atom=halted_atom,
        )
        store.publish(result.canonical().encode())
        return result

    with (store.root / ".feature.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fresh()
        store.publish(plan.canonical().encode())
        source = request.source
        for task_id in order:
            fresh()
            package = _materialize(
                store, request, proposal, review, task_id, source, tuple(evidence)
            )
            prepare_run(ledger, package.run)
            controller = Controller(
                ledger,
                model_factory(store, review.model_profile),
                broker_factory(store, package.run.broker_image),
            )
            state = controller.run(package.run.atom.atom_id)
            fresh()
            if state["status"] != "accepted":
                return finish("task-halt", source, halted_atom=package.run.atom.atom_id)
            accepted_digest = _accepted(ledger, package)
            candidate = SourceBundle.model_validate_json(store.read(state["candidate_digest"]))
            source = lift_candidate(store, package.digest(), candidate, current_source=source)
            completed.append(package)
            evidence.append(accepted_digest)
        fresh()
        selection = Repository(SnapshotSource(store, source)).select(
            plan.integration.execution_paths,
            purpose="execution",
            max_bytes=plan.integration.execution_bytes,
        )
        assert selection.bundle is not None
        # All feature policy, accepted evidence and final source participate in identity.
        binding = store.publish(
            json.dumps(
                [plan.digest(), source.model_dump(mode="json"), evidence], sort_keys=True
            ).encode()
        )
        fields = completed[-1].run.atom.model_dump(mode="json")
        revision = "feature-final-v1:" + binding
        fields.update(
            atom_id="feature-final-" + binding,
            idempotency_key="feature-final-" + binding,
            objective="Independently validate the combined feature",
            source_revision=revision,
            inputs_digest=InputSnapshot(
                source_digest=selection.bundle.digest(), source_revision=revision
            ).digest(),
            dependency_artifacts=evidence,
            upstream_contracts=[],
            max_attempts=2,
            required_gates=[
                dict(gate_id=k, validator_digest=v.digest())
                for k, v in plan.integration.gates.items()
            ],
        )
        check = FeatureCheck(
            atom=WorkAtom.model_validate_json(json.dumps(fields)),
            source=selection.bundle,
            gates=plan.integration.gates,
            broker_image=request.environments[plan.integration_environment].image,
        )
        state = _check(ledger, check, broker_factory(store, check.broker_image), fresh)
        fresh()
        return finish(
            "accepted" if state["status"] == "accepted" else "integration-halt",
            source,
            integration_atom=check.atom.atom_id,
            integration_selection=selection,
        )
