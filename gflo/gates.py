"""Trusted black-box process gates; expected results never enter containers."""

from __future__ import annotations

import base64
import json
import subprocess
from typing import Annotated, Any, Literal

from pydantic import Field

from gflo.broker import MAX_OUTPUT, BrokerError, DockerBroker, Execution
from gflo.ledger import Conflict, WorkLedger
from gflo.records import GateEvidence, Lease, Record, WorkAtom


class ProcessCase(Record):
    command: Annotated[tuple[str, ...], Field(min_length=1, max_length=64)]
    stdin: Annotated[str, Field(max_length=65536)] = ""
    expected_stdout: Annotated[str, Field(max_length=65536)]
    seconds: Annotated[float, Field(gt=0, le=60, allow_inf_nan=False)] = 10.0


class ProcessGate(Record):
    cases: Annotated[tuple[ProcessCase, ...], Field(min_length=1, max_length=32)]


def run_gate(
    ledger: WorkLedger,
    broker: DockerBroker,
    lease: Lease,
    gate_id: str,
    plan: ProcessGate,
) -> GateEvidence:
    """Execute a controller-owned plan against the exact stored candidate bytes.

    Only the control plane calls this function. A generated test script printing
    'pass' cannot supply a receipt. Plans are prebound to the Work-atom contract;
    the controller compares actual output with its own expected values.
    """
    plan = ProcessGate.model_validate(plan)
    ledger.check_lease(lease)
    snapshot = ledger.status(lease.atom_id)
    spec = next(
        (g for g in snapshot["contract"]["required_gates"] if g["gate_id"] == gate_id), None
    )
    if (
        snapshot["status"] != "validating"
        or snapshot["active_attempt"] != lease.attempt_id
        or spec is None
        or spec["validator_digest"] != plan.digest()
    ):
        raise Conflict("Gate plan does not bind the active validation contract")
    if broker.artifacts.root.resolve() != ledger.artifacts.root.resolve():
        raise ValueError("Broker and ledger must use the same artifact store")
    results = []
    outcome: Literal["pass", "fail", "inconclusive"] = "pass"
    error = None
    seen_containers: set[str] = set()
    try:
        if broker.qualification_digest is None or not broker.image_id:
            raise ValueError("Gate broker is not qualified")
        ledger.artifacts.verify(broker.qualification_digest)
        for case in plan.cases:
            ledger.check_lease(lease)
            result = broker.execute(
                snapshot["candidate_digest"],
                case.command,
                stdin=case.stdin,
                seconds=case.seconds,
                purpose="validation",
            )
            if not isinstance(result, Execution):
                raise ValueError("Malformed execution report: " + repr(result)[:4096])
            results.append(result.model_dump(mode="json"))
            result = Execution.model_validate(result)
            if (
                result.candidate_digest != snapshot["candidate_digest"]
                or result.command != case.command
                or result.stdin != case.stdin
                or result.purpose != "validation"
                or result.image_id != broker.image_id
                or result.container_id in seen_containers
            ):
                raise ValueError(
                    "Execution report does not bind this candidate/case/clean container"
                )
            seen_containers.add(result.container_id)
            stdout = base64.b64decode(result.stdout_base64, validate=True)
            stderr = base64.b64decode(result.stderr_base64, validate=True)
            if len(stdout) + len(stderr) > MAX_OUTPUT:
                raise ValueError("Execution report exceeds the output bound")
            if (
                result.outcome != "completed"
                or result.exit_code != 0
                or result.oom_killed
                or stdout != case.expected_stdout.encode()
            ):
                outcome = "fail"
                break
    except (BrokerError, OSError, ValueError, subprocess.SubprocessError) as exc:
        outcome = "inconclusive"
        error = str(exc)
    evidence = ledger.artifacts.publish(
        RecordReport(
            plan=plan,
            plan_digest=plan.digest(),
            qualification_digest=broker.qualification_digest,
            executions=results,
            error=error,
        )
        .canonical()
        .encode()
    )
    receipt = GateEvidence(
        attempt_id=lease.attempt_id,
        contract_digest=ledger_contract_digest(snapshot["contract"]),
        inputs_digest=snapshot["contract"]["inputs_digest"],
        candidate_digest=snapshot["candidate_digest"],
        gate_id=gate_id,
        validator_digest=plan.digest(),
        outcome=outcome,
        evidence_digest=evidence,
        runner_id="python-process-gate-v2",
    )
    ledger.record_gate(lease, receipt)
    return receipt


# Plans and executions are embedded; the separate qualification artifact is
# retained by the store's no-GC policy.
class RecordReport(Record):
    plan: ProcessGate
    plan_digest: str
    qualification_digest: str | None
    executions: list[dict[str, Any]]
    error: str | None


def ledger_contract_digest(contract: dict[str, Any]) -> str:
    return WorkAtom.model_validate_json(json.dumps(contract)).digest()
