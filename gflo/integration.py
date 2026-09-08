"""Prepared integration of accepted edits against an exact immutable base.

No Git/workspace mutation occurs. Current-state checks are admission preconditions,
not an atomic compare-and-swap on an external repository; promotion remains separate.
"""

from __future__ import annotations

import fcntl
import json
import re
from collections.abc import Callable
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from gflo.broker import DockerBroker, SourceBundle
from gflo.controller import RunPlan
from gflo.gates import ProcessGate, run_gate
from gflo.ledger import Conflict, WorkLedger
from gflo.records import Digest, Identifier, Record, RetryPlan, WorkAtom
from gflo.worker import parse_result

OWNER = "prepared-integration-v1"


class AcceptedInput(Record):
    atom_id: Identifier
    contract_digest: Digest
    candidate_digest: Digest


class IntegrationState(Record):
    base_digest: Digest
    contracts: dict[Identifier, Digest]


class IntegrationInputs(Record):
    state: IntegrationState
    contributions: Annotated[tuple[AcceptedInput, ...], Field(min_length=1, max_length=32)]


class IntegrationPlan(Record):
    kind: Literal["prepared-integration-v1"] = "prepared-integration-v1"
    atom: WorkAtom
    base: SourceBundle
    inputs: IntegrationInputs
    gates: dict[Identifier, ProcessGate]
    broker_image: str

    @model_validator(mode="after")
    def bound(self) -> IntegrationPlan:
        if not re.fullmatch(r"(?:[A-Za-z0-9_./:-]+@)?sha256:[a-f0-9]{64}", self.broker_image):
            raise ValueError("Integration requires a pinned broker image")
        if self.inputs.state.base_digest != self.base.digest():
            raise ValueError("Integration base differs from the pinned input")
        if self.atom.inputs_digest != self.inputs.digest():
            raise ValueError("Integration inputs do not bind the atom")
        if len({c.atom_id for c in self.inputs.contributions}) != len(self.inputs.contributions):
            raise ValueError("Duplicate integration contribution")
        if any(c.atom_id == self.atom.atom_id for c in self.inputs.contributions):
            raise ValueError("Integration cannot depend on itself")
        if {k: v.digest() for k, v in self.gates.items()} != {
            g.gate_id: g.validator_digest for g in self.atom.required_gates
        }:
            raise ValueError("Integration gates differ from the atom")
        if set(self.atom.upstream_contracts) != set(self.inputs.state.contracts.values()):
            raise ValueError("Integration dependency contracts differ from the atom")
        required = {self.base.digest(), self.inputs.digest()}
        required.update(c.candidate_digest for c in self.inputs.contributions)
        required.update(self.inputs.state.contracts.values())
        if not required <= set(self.atom.dependency_artifacts):
            raise ValueError("Integration inputs must remain referenced artifacts")
        return self


def _combine(ledger: WorkLedger, plan: IntegrationPlan) -> SourceBundle:
    changes: dict[str, str] = {}
    for contribution in plan.inputs.contributions:
        state = ledger.status(contribution.atom_id)
        contract = WorkAtom.model_validate_json(json.dumps(state["contract"]))
        if (
            state["status"] != "accepted"
            or contract.digest() != contribution.contract_digest
            or state["candidate_digest"] != contribution.candidate_digest
        ):
            raise Conflict("Integration contribution is not the pinned accepted result")
        if not set(contract.upstream_contracts) <= set(plan.inputs.state.contracts.values()):
            raise Conflict("Contribution was built against a different dependency contract")
        original = RunPlan.model_validate_json(ledger.run_plan(contribution.atom_id))
        if original.source.digest() != plan.base.digest():
            raise Conflict("Contribution was built against a different base")
        # Recheck accepted bytes and dependencies, not merely the status label.
        ledger.accept(
            ledger.active_lease(contribution.atom_id), current_inputs_digest=contract.inputs_digest
        )
        candidate = SourceBundle.model_validate_json(
            ledger.artifacts.read(contribution.candidate_digest)
        )
        if not plan.base.files.keys() <= candidate.files.keys():
            raise Conflict("This integration profile does not support deletions")
        edits = {p: text for p, text in candidate.files.items() if plan.base.files.get(p) != text}
        if edits:
            parse_result(json.dumps({"kind": "candidate", "changes": edits}), contract, plan.base)
        if set(changes) & edits.keys():
            raise Conflict("Contributions edit overlapping paths; prepare an explicit repair")
        changes.update(edits)
    if changes:
        parse_result(json.dumps({"kind": "candidate", "changes": changes}), plan.atom, plan.base)
    return SourceBundle(files=plan.base.files | changes)


def integrate(
    ledger: WorkLedger,
    plan: IntegrationPlan,
    broker: DockerBroker,
    current_state: Callable[[], IntegrationState],
) -> dict[str, Any]:
    """Validate, combine and gate accepted edits; safely repeat after interruption."""
    plan = IntegrationPlan.model_validate(plan)
    if (
        broker.artifacts.root.resolve() != ledger.artifacts.root.resolve()
        or broker.image != plan.broker_image
    ):
        raise Conflict("Integration broker differs from its prepared storage/image")

    def fresh() -> None:
        if IntegrationState.model_validate(current_state()) != plan.inputs.state:
            raise Conflict("Integration base or dependency contract changed")

    with (ledger.artifacts.root / ".controller.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fresh()
        ledger.check_storage()
        # Combining performs no product mutation. A rejected plan cannot claim work.
        combined = _combine(ledger, plan)
        ledger.artifacts.publish(plan.base.canonical().encode())
        ledger.artifacts.publish(plan.inputs.canonical().encode())
        ledger.submit(plan.atom)
        ledger.bind_run(plan.atom.atom_id, ledger.artifacts.publish(plan.canonical().encode()))
        broker.reconcile()
        ledger.reconcile()
        state = ledger.status(plan.atom.atom_id)
        if state["status"] == "accepted":
            fresh()
            ledger.accept(
                ledger.active_lease(plan.atom.atom_id), current_inputs_digest=plan.inputs.digest()
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
                    strategy="repeat prepared integration after recovery",
                    new_evidence=ledger.artifacts.publish(json.dumps(prior).encode()),
                )
            lease = ledger.claim(plan.atom.atom_id, OWNER, retry=retry, lease_seconds=1800)
        else:
            lease = ledger.active_lease(plan.atom.atom_id)
            if lease.owner != OWNER:
                raise Conflict("Different controller owns this integration Attempt")
        state = ledger.status(plan.atom.atom_id)
        if state["status"] == "leased":
            ledger.start(lease)
        if ledger.status(plan.atom.atom_id)["status"] == "running":
            fresh()
            ledger.candidate(lease, ledger.artifacts.publish(combined.canonical().encode()))
        if ledger.status(plan.atom.atom_id)["candidate_digest"] != combined.digest():
            raise Conflict("Retained integration candidate differs from prepared inputs")
        for gate_id, gate in plan.gates.items():
            fresh()
            existing = next(
                (
                    r
                    for r in ledger.status(plan.atom.atom_id)["attempts"][-1]["gate_receipts"]
                    if r["gate_id"] == gate_id
                ),
                None,
            )
            receipt = existing or run_gate(ledger, broker, lease, gate_id, gate).model_dump(
                mode="json"
            )
            if receipt["outcome"] != "pass":
                ledger.fail(lease, "Integrated validation did not pass: " + receipt["outcome"])
                return ledger.status(plan.atom.atom_id)
        fresh()
        ledger.accept(lease, current_inputs_digest=plan.inputs.digest())
        return ledger.status(plan.atom.atom_id)
