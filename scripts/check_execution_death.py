#!/usr/bin/env python3
"""Kill disposable candidate/validation containers and verify durable recovery.

Uses a scripted candidate proposal to isolate execution recovery from model quality.
No inference service is interrupted; only broker-owned fixture containers are killed.
"""

import argparse
import dataclasses
import hashlib
import json
import threading
import time
from pathlib import Path

from gflo.broker import LABEL, DockerBroker, SourceBundle
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.ledger import WorkLedger
from gflo.model import ModelTurn
from gflo.pilot import IMAGE, fixtures, make_plan
from gflo.worker import CandidateResult

FIXTURE_CODE = (
    "import signal,sys,time; signal.signal(signal.SIGTERM,lambda *_:sys.exit(143)); "
    'time.sleep(2); exec(open("main.py").read())'
)


class ScriptedModel:
    def __init__(self, ledger, plan):
        self.artifacts = ledger.artifacts
        self.profile = plan.model_profile
        self.last_evidence_digest = None

    def turn(self, *args, **kwargs):
        result = CandidateResult(kind="candidate", changes={"main.py": "print(42)\n"})
        digest = self.artifacts.publish(
            b'{"kind":"scripted-fixture-no-inference","elapsed_seconds":0}'
        )
        self.last_evidence_digest = digest
        return ModelTurn(
            manifest_digest=digest,
            response_digest=digest,
            result=result,
            prompt_tokens=0,
            completion_tokens=0,
            elapsed_seconds=0,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    template = make_plan(
        fixtures()[0],
        Path("infra/serving/vllm-5090-graphs.example.json").read_text(),
        Path("examples/work-atom.json"),
    )
    fields = template.model_dump(mode="json")
    source = SourceBundle(files={"main.py": "print(0)\n"})
    from gflo.gates import ProcessCase, ProcessGate
    from gflo.worker import InputSnapshot

    gate = ProcessGate(
        cases=(
            ProcessCase(
                command=(
                    "python",
                    "-c",
                    FIXTURE_CODE,
                ),
                expected_stdout="42\n",
                seconds=10,
            ),
        )
    )
    fields.update(
        source=source.model_dump(mode="json"),
        selected_paths=["main.py"],
        gates={"behavior": gate.model_dump(mode="json")},
    )
    fields["atom"].update(
        writable_paths=["main.py"],
        prohibited_paths=[],
        required_gates=[{"gate_id": "behavior", "validator_digest": gate.digest()}],
    )
    fields["atom"]["inputs_digest"] = InputSnapshot(
        source_digest=source.digest(), source_revision=fields["atom"]["source_revision"]
    ).digest()
    plan = RunPlan.model_validate_json(json.dumps(fields))
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "plan": plan.model_dump(mode="json"),
                "proposal": "scripted print(42), no model calls",
                "variations": [
                    "candidate-KILL",
                    "candidate-TERM",
                    "validation-KILL",
                    "validation-TERM",
                ],
                "injection_deadline_seconds": 5,
                "execution_deadline_seconds": 10,
                "source_sha256": {
                    str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(Path("gflo").glob("*.py"))
                },
                "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            },
            indent=2,
        )
        + "\n"
    )
    results = []
    for purpose in ("candidate", "validation"):
        for signal in ("KILL", "TERM"):
            root = args.output / (purpose + "-" + signal)
            root.mkdir()
            with WorkLedger(root / "ledger.db") as ledger:
                prepare_run(ledger, plan)
                broker = DockerBroker(ledger.artifacts, IMAGE)
                original = broker._attach
                errors, injections = [], []

                def attach(name, payload, seconds):
                    # Qualification calls _execute directly; arm only user execution.
                    if not broker.qualification_digest or injections:
                        return original(name, payload, seconds)
                    # Candidate smoke is first after qualification; validation is next.
                    current = ledger.status(plan.atom.atom_id)
                    is_validation = any(
                        e["kind"] == "observation" and e["details"]["kind"] == "candidate-execution"
                        for e in current["attempts"][-1]["events"]
                    )
                    if (purpose == "validation") != is_validation:
                        return original(name, payload, seconds)
                    stop = threading.Event()

                    def kill():
                        try:
                            deadline = time.monotonic() + 5
                            while not stop.is_set() and time.monotonic() < deadline:
                                target = json.loads(broker._docker("inspect", name))[0]
                                if target["State"]["Running"] and "time.sleep(2)" in broker._docker(
                                    "top", name, "-eo", "pid,args"
                                ):
                                    if target["Config"]["Labels"].get(LABEL) != broker.owner:
                                        raise RuntimeError("Unowned kill target")
                                    victim = broker._docker(
                                        "exec",
                                        target["Id"],
                                        "python",
                                        "-c",
                                        "import os,signal,sys; from pathlib import Path; "
                                        "wanted=sys.argv[1].encode(); "
                                        "pids=[int(p.parent.name) "
                                        "for p in Path('/proc').glob('[0-9]*/cmdline') "
                                        "if int(p.parent.name)!=os.getpid() "
                                        "and wanted in p.read_bytes().split(bytes([0]))]; "
                                        "assert pids==[1],pids; print(pids[0],flush=True)",
                                        FIXTURE_CODE,
                                    )
                                    broker._docker("kill", "--signal", signal, target["Id"])
                                    injections.append(
                                        {
                                            "container_id": target["Id"],
                                            "signal": signal,
                                            "victim_pid": int(victim),
                                            "purpose": purpose,
                                        }
                                    )
                                    return
                                stop.wait(0.05)
                            raise RuntimeError("No running fixture observed")
                        except Exception as exc:
                            errors.append(str(exc))

                    thread = threading.Thread(target=kill)
                    thread.start()
                    try:
                        return original(name, payload, seconds)
                    finally:
                        stop.set()
                        thread.join(timeout=20)
                        if thread.is_alive():
                            raise RuntimeError("Injector did not stop")

                broker._attach = attach
                controller = Controller(ledger, ScriptedModel(ledger, plan), broker)
                try:
                    state = controller.run(plan.atom.atom_id)
                    (root / "state.json").write_text(json.dumps(state, indent=2) + "\n")
                    assert len(injections) == 1 and not errors, (injections, errors)
                    assert state["status"] == "accepted"
                    assert len(state["attempts"]) == (2 if purpose == "validation" else 1)
                    first = state["attempts"][0]
                    if purpose == "validation":
                        receipt = first["gate_receipts"][0]
                        assert receipt["outcome"] == "fail"
                        execution = json.loads(ledger.artifacts.read(receipt["evidence_digest"]))[
                            "executions"
                        ][0]
                    else:
                        digest = next(
                            e["details"]["digest"]
                            for e in first["events"]
                            if e["kind"] == "observation"
                            and e["details"]["kind"] == "candidate-execution"
                        )
                        execution = json.loads(ledger.artifacts.read(digest))
                    assert execution["exit_code"] == (137 if signal == "KILL" else 143)
                    assert execution["container_id"] == injections[0]["container_id"]
                    assert controller.run(plan.atom.atom_id) == state
                    assert ledger._db.execute("SELECT count(*) FROM acceptances").fetchone()[0] == 1
                    audit = ledger.audit_artifacts()
                    assert not audit.missing and not audit.corrupt
                    assert not broker._docker(
                        "ps", "-aq", "--filter", f"label={LABEL}={broker.owner}"
                    )
                    result = {
                        "variation": root.name,
                        "passed": True,
                        "injections": injections,
                        "attempts": len(state["attempts"]),
                        "audit": dataclasses.asdict(audit),
                    }
                except BaseException as exc:
                    (root / "failure.json").write_text(
                        json.dumps(
                            {
                                "type": type(exc).__name__,
                                "message": str(exc),
                                "injections": injections,
                                "injection_errors": errors,
                            },
                            indent=2,
                        )
                        + "\n"
                    )
                    raise
                finally:
                    broker.reconcile()
                results.append(result)
                (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
                print(json.dumps({k: v for k, v in result.items() if k != "audit"}), flush=True)


if __name__ == "__main__":
    main()
