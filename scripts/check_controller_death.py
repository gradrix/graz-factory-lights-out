#!/usr/bin/env python3
"""SIGKILL a dedicated fixture controller at dispatch, candidate and validation boundaries."""

import argparse
import dataclasses
import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from check_execution_death import ScriptedModel

from gflo.broker import LABEL, DockerBroker
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.ledger import WorkLedger
from gflo.model import ModelTurn
from gflo.worker import ReadFileRequest

WINDOWS = (
    "before_launch",
    "during_case",
    "between_cases",
    "before_receipt",
    "after_receipt",
    "after_candidate_commit",
    "before_request",
    "read_expansion",
)


def save(path, value):
    with path.open("w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def child(root, window):
    plan = RunPlan.model_validate_json((root / "plan.json").read_bytes())

    def crash(details=None):
        save(root / "death.json", {"window": window, "pid": os.getpid(), "details": details})
        os.kill(os.getpid(), signal.SIGKILL)

    with WorkLedger(root / "ledger.db") as ledger:
        broker = DockerBroker(ledger.artifacts, plan.broker_image)
        execute, attach, record = broker.execute, broker._attach, ledger.record_gate
        candidate = ledger.candidate

        def committed_candidate(*args, **kwargs):
            result = candidate(*args, **kwargs)
            if window == "after_candidate_commit":
                crash({"candidate_committed": True})
            return result

        ledger.candidate = committed_candidate
        validation_calls = 0

        def interrupted_execute(*args, **kwargs):
            nonlocal validation_calls
            if kwargs.get("purpose") == "validation":
                validation_calls += 1
                if window == "between_cases" and validation_calls == 2:
                    crash({"completed_cases_without_receipt": 1})
            return execute(*args, **kwargs)

        def interrupted_attach(name, payload, seconds):
            if validation_calls == 0 or not broker.qualification_digest:
                return attach(name, payload, seconds)
            if window == "before_launch":
                crash({"created_container": name})
            if window != "during_case":
                return attach(name, payload, seconds)
            stop = threading.Event()
            errors = []

            def kill_when_running():
                try:
                    deadline = time.monotonic() + 5
                    while not stop.is_set() and time.monotonic() < deadline:
                        info = json.loads(broker._docker("inspect", name))[0]
                        if info["State"]["Running"]:
                            processes = broker._docker("top", name, "-eo", "pid,args")
                            if "time.sleep(2)" in processes:
                                crash({"container_id": info["Id"], "processes": processes})
                        stop.wait(0.05)
                    errors.append("No active fixture observed")
                except Exception as exc:
                    errors.append(str(exc))

            thread = threading.Thread(target=kill_when_running)
            thread.start()
            try:
                return attach(name, payload, seconds)
            finally:
                stop.set()
                thread.join(timeout=20)
                if errors or thread.is_alive():
                    raise RuntimeError(str(errors) or "Injector did not terminate")

        def interrupted_record(*args, **kwargs):
            if window == "before_receipt":
                crash({"receipt_committed": False})
            result = record(*args, **kwargs)
            if window == "after_receipt":
                crash({"receipt_committed": True})
            return result

        broker.execute, broker._attach = interrupted_execute, interrupted_attach
        ledger.record_gate = interrupted_record

        class DispatchModel(ScriptedModel):
            def turn(self, *args, **kwargs):
                if window == "before_request":
                    crash({"model_request_started": False})
                if window == "read_expansion":
                    if "helper.py" in kwargs.get("selected_paths", ()):
                        crash({"expanded_paths": list(kwargs["selected_paths"])})
                    digest = self.artifacts.publish(b'{"kind":"scripted-read","elapsed_seconds":0}')
                    self.last_evidence_digest = digest
                    return ModelTurn(
                        manifest_digest=digest,
                        response_digest=digest,
                        result=ReadFileRequest(kind="read_file", path="helper.py"),
                        prompt_tokens=0,
                        completion_tokens=0,
                        elapsed_seconds=0,
                    )
                return super().turn(*args, **kwargs)

        Controller(ledger, DispatchModel(ledger, plan), broker).run(plan.atom.atom_id)
    raise RuntimeError("Expected SIGKILL was not injected")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--only", choices=WINDOWS)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--child-window", choices=WINDOWS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child_window:
        child(args.output, args.child_window)
        return
    if args.plan is None:
        parser.error("--plan is required")
    plan = RunPlan.model_validate_json(args.plan.read_bytes())
    if len(plan.gates) != 1 or len(next(iter(plan.gates.values())).cases) != 2:
        parser.error("Fixture requires one gate with two cases")
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    save(
        root / "manifest.json",
        {
            "schema_version": 1,
            "windows": [args.only] if args.only else WINDOWS,
            "plan": plan.model_dump(mode="json"),
            "child_deadline_seconds": 60,
            "proposal": "scripted print(42), no model inference",
            "source_sha256": {
                str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(Path("gflo").glob("*.py"))
            },
            "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scripted_model_sha256": hashlib.sha256(
                Path(__file__).with_name("check_execution_death.py").read_bytes()
            ).hexdigest(),
        },
    )
    results = []
    for window in [args.only] if args.only else WINDOWS:
        directory = root / window
        directory.mkdir()
        save(directory / "plan.json", plan.model_dump(mode="json"))
        with WorkLedger(directory / "ledger.db") as ledger:
            prepare_run(ledger, plan)
        try:
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--output",
                str(directory),
                "--child-window",
                window,
            ]
            process = subprocess.run(command, capture_output=True, text=True, timeout=60)
            (directory / "child.log").write_text(process.stdout + process.stderr)
            assert process.returncode == -signal.SIGKILL, process.returncode
            assert json.loads((directory / "death.json").read_text())["window"] == window
            with WorkLedger(directory / "ledger.db") as ledger:
                before = ledger.status(plan.atom.atom_id)
                save(directory / "interrupted.json", before)
                dispatch_death = window in ("before_request", "read_expansion")
                assert before["status"] == ("running" if dispatch_death else "validating")
                if dispatch_death:
                    assert before["candidate_digest"] is None
                    observed = [
                        e
                        for e in before["attempts"][0]["events"]
                        if e["kind"] == "observation" and e["details"]["kind"] == "model"
                    ]
                    assert len(observed) == (1 if window == "read_expansion" else 0)
                assert ledger._db.execute("SELECT count(*) FROM acceptances").fetchone()[0] == 0
                broker = DockerBroker(ledger.artifacts, plan.broker_image)
                save(
                    directory / "leftovers.json",
                    broker._docker(
                        "ps", "-aq", "--filter", f"label={LABEL}={broker.owner}"
                    ).splitlines(),
                )

                class NoNewProposal(ScriptedModel):
                    def turn(self, *args, **kwargs):
                        raise AssertionError("Resume unexpectedly regenerated candidate")

                controller = Controller(
                    ledger,
                    (ScriptedModel if dispatch_death else NoNewProposal)(ledger, plan),
                    broker,
                )
                accepted = controller.run(plan.atom.atom_id)
                save(directory / "accepted.json", accepted)
                assert accepted["status"] == "accepted"
                assert len(accepted["attempts"]) == (2 if dispatch_death else 1)
                prior_events = before["attempts"][0]["events"]
                assert accepted["attempts"][0]["events"][: len(prior_events)] == prior_events
                assert controller.run(plan.atom.atom_id) == accepted
                assert ledger._db.execute("SELECT count(*) FROM acceptances").fetchone()[0] == 1
                assert not broker._docker("ps", "-aq", "--filter", f"label={LABEL}={broker.owner}")
                audit = ledger.audit_artifacts()
                assert not audit.missing and not audit.corrupt
                save(directory / "audit.json", dataclasses.asdict(audit))
                results.append({"window": window, "passed": True, "child_exit": process.returncode})
                save(root / "results.json", results)
                print(json.dumps(results[-1]), flush=True)
        except BaseException as exc:
            save(directory / "failure.json", {"type": type(exc).__name__, "message": str(exc)})
            raise
        finally:
            with WorkLedger(directory / "ledger.db") as ledger:
                DockerBroker(ledger.artifacts, plan.broker_image).reconcile()


if __name__ == "__main__":
    main()
