"""One prepared, bounded task-to-evidence loop; no autonomous product planning."""

from __future__ import annotations

import fcntl
import hashlib
import json
import re
from typing import Annotated, Any

from pydantic import Field, model_validator

from gflo.broker import BrokerError, DockerBroker, SourceBundle
from gflo.feedback import validation_feedback
from gflo.gates import ProcessGate, run_gate
from gflo.ledger import Conflict, WorkLedger
from gflo.model import LocalModel, ModelError, ModelProfile
from gflo.records import Acceptance, Lease, Record, RetryPlan, WorkAtom
from gflo.worker import (
    CandidateResult,
    Diagnostic,
    InputSnapshot,
    candidate_bundle,
    compose_view,
)

OWNER = "durable-controller-v1"


class RunPlan(Record):
    atom: WorkAtom
    source: SourceBundle
    gates: dict[str, ProcessGate]
    model_profile: ModelProfile
    deployment: str
    broker_image: str
    max_model_turns: Annotated[int, Field(ge=1, le=4)] = 3
    selected_paths: tuple[str, ...] | None = None

    @model_validator(mode="after")
    def bindings(self) -> RunPlan:
        if self.model_profile.profile_id in (
            "vllm-python-worker-escalating-v1",
            "vllm-python-worker-escalating-low-v1",
            "vllm-python-worker-escalating-tools-v1",
        ) and (
            self.atom.max_attempts != 2
            or self.max_model_turns
            != (
                3
                if self.model_profile.profile_id == "vllm-python-worker-escalating-tools-v1"
                else 1
            )
            or self.atom.context_budget.total_tokens != 8192
            or self.atom.context_budget.output_tokens != 4096
        ):
            raise ValueError(
                "Escalation requires its fixed turn allowance, two attempts and an 8K/4K budget"
            )
        if not re.fullmatch(r"(?:[A-Za-z0-9_./:-]+@)?sha256:[a-f0-9]{64}", self.broker_image):
            raise ValueError("Run requires a pinned broker image")
        if (
            InputSnapshot(
                source_digest=self.source.digest(), source_revision=self.atom.source_revision
            ).digest()
            != self.atom.inputs_digest
        ):
            raise ValueError("Run source does not bind the atom inputs")
        if {key: value.digest() for key, value in self.gates.items()} != {
            gate.gate_id: gate.validator_digest for gate in self.atom.required_gates
        }:
            raise ValueError("Run gates do not match the atom validators")
        if (
            hashlib.sha256(self.deployment.encode()).hexdigest()
            != self.model_profile.deployment_digest
        ):
            raise ValueError("Deployment provenance does not match the model profile")
        return self


def prepare_run(ledger: WorkLedger, plan: RunPlan) -> str:
    plan = RunPlan.model_validate(plan)
    ledger.artifacts.publish(plan.source.canonical().encode())
    ledger.artifacts.publish(plan.deployment.encode())
    compose_view(
        ledger.artifacts, plan.atom, plan.source.digest(), selected_paths=plan.selected_paths
    )
    ledger.submit(plan.atom)
    digest = ledger.artifacts.publish(plan.canonical().encode())
    ledger.bind_run(plan.atom.atom_id, digest)
    return plan.atom.atom_id


def verify_predecessors(ledger: WorkLedger, atom: WorkAtom) -> None:
    """Recheck snapshot-worker ancestry, including findings, before execution/reuse."""
    seen: set[str] = set()

    def visit(contract: WorkAtom, depth: int) -> None:
        if contract.capability_profile != "python-snapshot-v1":
            return
        if depth > 12 or len(contract.dependency_artifacts) > 12:
            raise Conflict("Snapshot predecessor graph exceeds its bounded profile")
        for digest in contract.dependency_artifacts:
            if digest in seen:
                continue
            accepted = Acceptance.model_validate_json(ledger.artifacts.read(digest))
            state = ledger.status(accepted.atom_id)
            predecessor = WorkAtom.model_validate_json(json.dumps(state["contract"]))
            if (
                state["status"] != "accepted"
                or predecessor.digest() != accepted.contract_digest
                or state["candidate_digest"] != accepted.candidate_digest
            ):
                raise Conflict("Predecessor differs from its pinned acceptance")
            visit(predecessor, depth + 1)
            if (
                ledger.accept(
                    ledger.active_lease(accepted.atom_id),
                    current_inputs_digest=accepted.inputs_digest,
                )
                != accepted
            ):
                raise Conflict("Predecessor acceptance changed")
            seen.add(digest)

    visit(atom, 0)


class Controller:
    def __init__(self, ledger: WorkLedger, model: LocalModel, broker: DockerBroker):
        self.ledger, self.model, self.broker = ledger, model, broker

    def _diagnostic(self, lease: Lease, text: str, details: Any) -> str:
        raw = self.ledger.artifacts.publish(
            json.dumps(
                {
                    "attempt_id": lease.attempt_id,
                    "observation": details,
                },
                sort_keys=True,
            ).encode()
        )
        diagnostic = Diagnostic(source_digest=raw, text=text[:8192] or "Unspecified failure")
        digest = self.ledger.artifacts.publish(diagnostic.canonical().encode())
        self.ledger.observe(lease, "diagnostic", digest)
        return digest

    def _failure(self, lease: Lease, text: str, details: Any) -> None:
        self._diagnostic(lease, text, details)
        self.ledger.fail(lease, text[:2000])

    def _retry(self, snapshot: dict[str, Any]) -> RetryPlan:
        prior = snapshot["attempts"][-1]
        failure = prior["events"][-1]
        diagnostics = [
            event["details"]["digest"]
            for event in prior["events"]
            if event["kind"] == "observation" and event["details"]["kind"] == "diagnostic"
        ]
        evidence = (
            diagnostics[-1]
            if diagnostics
            else self.ledger.artifacts.publish(
                Diagnostic(
                    source_digest=self.ledger.artifacts.publish(
                        json.dumps(failure, sort_keys=True).encode()
                    ),
                    text=(
                        "The previous attempt expired. Rebuild from the immutable source; "
                        "its environment was reconciled."
                    ),
                )
                .canonical()
                .encode()
            )
        )
        return RetryPlan(
            failure_event=failure["event_id"],
            strategy="repair from retained diagnostic",
            new_evidence=evidence,
        )

    def _validate(self, plan: RunPlan, lease: Lease) -> str:
        verify_predecessors(self.ledger, plan.atom)
        snapshot = self.ledger.status(lease.atom_id)
        if not any(
            e["kind"] == "observation" and e["details"]["kind"] == "candidate-execution"
            for e in snapshot["attempts"][-1]["events"]
        ):
            smoke = next(iter(plan.gates.values())).cases[0]
            result = self.broker.execute(
                snapshot["candidate_digest"],
                smoke.command,
                stdin=smoke.stdin,
                seconds=smoke.seconds,
                purpose="candidate",
            )
            digest = self.ledger.artifacts.publish(result.canonical().encode())
            self.ledger.observe(lease, "candidate-execution", digest)
        # A smoke result cannot replace any independent validation gate.
        for gate_id, gate in plan.gates.items():
            snapshot = self.ledger.status(lease.atom_id)
            existing = next(
                (r for r in snapshot["attempts"][-1]["gate_receipts"] if r["gate_id"] == gate_id),
                None,
            )
            receipt = existing or run_gate(
                self.ledger, self.broker, lease, gate_id, gate
            ).model_dump(mode="json")
            if receipt["outcome"] != "pass":
                raw = json.loads(self.ledger.artifacts.read(receipt["evidence_digest"]))
                # Project observations, excluding the trusted plan/expected outputs.
                observation = {
                    "gate_id": gate_id,
                    "outcome": receipt["outcome"],
                    "executions": raw.get("executions", []),
                    "error": raw.get("error"),
                }
                self._failure(
                    lease,
                    validation_feedback(observation),
                    observation,
                )
                return "halt" if receipt["outcome"] == "inconclusive" else "retry"
        verify_predecessors(self.ledger, plan.atom)
        self.ledger.accept(lease, current_inputs_digest=plan.atom.inputs_digest)
        return "accepted"

    def _attempt(self, plan: RunPlan, lease: Lease, diagnostic: str | None) -> str:
        if self.ledger.status(lease.atom_id)["status"] == "leased":
            self.ledger.start(lease)
        selected = plan.selected_paths
        source_digest = plan.source.digest()
        diagnostics = (diagnostic,) if diagnostic else ()
        for turn_index in range(plan.max_model_turns):
            verify_predecessors(self.ledger, plan.atom)
            self.ledger.check_lease(lease)
            try:
                turn = self.model.turn(
                    plan.atom,
                    source_digest,
                    current_inputs=lambda: plan.atom.inputs_digest,
                    selected_paths=selected,
                    diagnostic_digests=diagnostics,
                    remaining_model_turns=plan.max_model_turns - turn_index,
                )
            finally:
                if self.model.last_evidence_digest is not None:
                    self.ledger.observe(lease, "model", self.model.last_evidence_digest)
            if isinstance(turn.result, CandidateResult):
                candidate = candidate_bundle(plan.source, turn.result)
                digest = self.ledger.artifacts.publish(candidate.canonical().encode())
                self.ledger.candidate(lease, digest)
                return self._validate(plan, lease)
            # Only a verified bundle path can reach this branch. Expansion is a
            # fresh view, not an accumulating chat; required coverage is rechecked.
            already = set(selected) if selected is not None else set(plan.source.files)
            if turn.result.path in already:
                raise ValueError("Worker repeated a read for a file already in its view")
            selected = tuple(sorted(already | {turn.result.path}))
        raise ValueError("Bounded model-turn allowance exhausted without a candidate")

    def run(self, atom_id: str) -> dict[str, Any]:
        with (self.ledger.artifacts.root / ".controller.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise Conflict("Another controller owns this factory run") from exc
            plan = RunPlan.model_validate_json(self.ledger.run_plan(atom_id))
            verify_predecessors(self.ledger, plan.atom)
            if self.model.profile != plan.model_profile or self.broker.image != plan.broker_image:
                raise Conflict("Execution services differ from the immutable run plan")
            if (
                self.model.artifacts.root.resolve() != self.ledger.artifacts.root.resolve()
                or self.broker.artifacts.root.resolve() != self.ledger.artifacts.root.resolve()
            ):
                raise Conflict("Controller services must share the ledger's artifact store")
            if plan.atom.atom_id != atom_id or self.ledger.status(atom_id)[
                "contract"
            ] != plan.atom.model_dump(mode="json"):
                raise Conflict("Run plan differs from the durable atom contract")
            self.broker.reconcile()
            self.ledger.reconcile()
            snapshot = self.ledger.status(atom_id)
            if snapshot["status"] == "accepted":
                self.ledger.accept(
                    self.ledger.active_lease(atom_id), current_inputs_digest=plan.atom.inputs_digest
                )
                return snapshot
            if snapshot["status"] == "quarantined":
                return snapshot
            self.ledger.check_storage()
            # Infrastructure qualification occurs before consuming a new attempt.
            self.broker.qualify()
            if snapshot["status"] in ("leased", "running", "validating"):
                lease = self.ledger.active_lease(atom_id)
                if lease.owner != OWNER:
                    raise Conflict("Cannot resume an attempt owned by another controller")
                if snapshot["status"] == "running":
                    self._failure(
                        lease,
                        (
                            "Controller interrupted before durable candidate publication; "
                            "rebuild using retained history."
                        ),
                        snapshot["attempts"][-1],
                    )
                elif snapshot["status"] == "validating":
                    outcome = self._validate(plan, lease)
                    if outcome != "retry":
                        return self.ledger.status(atom_id)
            while True:
                snapshot = self.ledger.status(atom_id)
                if snapshot["status"] in ("accepted", "quarantined"):
                    return snapshot
                self.ledger.check_storage()
                retry = self._retry(snapshot) if snapshot["status"] == "retry-ready" else None
                if snapshot["status"] == "leased" and snapshot["attempts"][-1]["retry_plan"]:
                    retry = RetryPlan.model_validate_json(
                        json.dumps(snapshot["attempts"][-1]["retry_plan"])
                    )
                lease = (
                    self.ledger.active_lease(atom_id)
                    if snapshot["status"] == "leased"
                    else self.ledger.claim(atom_id, OWNER, lease_seconds=1800, retry=retry)
                )
                try:
                    outcome = self._attempt(plan, lease, retry.new_evidence if retry else None)
                except (ModelError, BrokerError, OSError) as exc:
                    self._failure(
                        lease, "Infrastructure/protocol failure: " + str(exc), {"error": str(exc)}
                    )
                    return self.ledger.status(atom_id)
                except Conflict:
                    raise
                except ValueError as exc:
                    self._failure(lease, "Invalid worker result: " + str(exc), {"error": str(exc)})
                    outcome = "retry"
                if outcome != "retry":
                    return self.ledger.status(atom_id)
