#!/usr/bin/env python3
"""Observed local-worker trial on a pinned GFLO source snapshot; no promotion."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import DockerBroker, SourceBundle
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.gates import ProcessCase, ProcessGate
from gflo.ledger import WorkLedger
from gflo.model import LocalModel
from gflo.reporting import cost_report
from gflo.worker import InputSnapshot

ROOT = Path(__file__).resolve().parents[1]


def check(broker, source, gate):
    digest = broker.artifacts.publish(source.canonical().encode())
    execution = broker.execute(
        digest, gate.cases[0].command, seconds=60, stdin="", purpose="validation"
    )
    evidence = broker.artifacts.publish(execution.canonical().encode())
    return {
        "passed": execution.exit_code == 0
        and execution.outcome == "completed"
        and execution.stdout == gate.cases[0].expected_stdout.encode(),
        "evidence": evidence,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    files = {
        str(p.relative_to(args.checkout)): p.read_text()
        for p in (args.checkout / "gflo").glob("*.py")
    }
    for name in ["tests/test_controller.py", "examples/work-atom.json", "pyproject.toml"]:
        files[name] = (args.checkout / name).read_text()
    files["tests/test_history_filter.py"] = (
        ROOT / ".scratch/local-lights-out-factory/self-trial/test_history_filter.py"
    ).read_text()
    source = SourceBundle(files=files)
    command = (
        "python",
        "-c",
        "import subprocess,sys; p=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider','tests/test_history_filter.py','tests/test_controller.py'],capture_output=True,text=True); print('checks passed' if p.returncode==0 else p.stdout+p.stderr); sys.exit(p.returncode)",
    )
    gate = ProcessGate(
        cases=(ProcessCase(command=command, expected_stdout="checks passed\n", seconds=60.0),)
    )
    objective = (
        "Add optional --attempt N to gflo history ATOM, where N is a positive one-based "
        "attempt ordinal. With no option, preserve text and JSON output exactly. With "
        "the option, display only that attempt but preserve all task-level metadata and "
        "acceptance warnings in both formats. Reject non-positive, noninteger, or absent "
        "ordinals with a nonzero exit and explanatory stderr. Always call existing "
        "change_history before filtering so all integrity checks still run, including "
        "unselected evidence. Filter the attempts list for presentation; do not change "
        "history storage or other commands. Only gflo/cli.py is writable. Return its "
        "complete replacement, preserving unrelated code. "
        "Provider contract: change_history returns a dictionary whose attempts list contains "
        "dictionaries keyed by ordinal (integer), attempt_id, outcome, failures, candidates, "
        "and gate_receipts. Match ordinal, not attempt_id or list position. If N matches "
        "no ordinal (for example 3 when only ordinals 1 and 2 exist), raise ValueError "
        "with an explanatory message; the existing CLI exception handler emits stderr "
        "and a nonzero exit. Never return success with an empty filtered list. "
        "No --attempt option means display all attempts as before."
    )
    manifest = {
        "source_digest": source.digest(),
        "gate_digest": gate.digest(),
        "objective": objective,
        "image": args.image,
        "repetitions": 3,
        "max_attempts": 2,
        "max_turns_per_attempt": 3,
        "git_base": subprocess.check_output(
            ["git", "-C", str(args.checkout), "rev-parse", "HEAD"], text=True
        ).strip(),
        "runtime_hashes": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / "gflo").glob("*.py")
        },
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    control_broker = DockerBroker(ArtifactStore(args.output / "preflight"), args.image)
    control_broker.qualify()
    baseline = check(control_broker, source, gate)
    reference_files = dict(files)
    reference_files["gflo/cli.py"] = (
        files["gflo/cli.py"]
        .replace(
            '    history.add_argument("atom_id")',
            '    history.add_argument("atom_id")\n    history.add_argument("--attempt", type=int)',
        )
        .replace(
            "                output = change_history(ledger, args.atom_id)",
            '                output = change_history(ledger, args.atom_id)\n                if args.attempt is not None:\n                    selected = [a for a in output["attempts"] if a["ordinal"] == args.attempt]\n                    if args.attempt < 1 or not selected:\n                        raise ValueError("Attempt ordinal does not exist")\n                    output["attempts"] = selected',
        )
    )
    reference = check(control_broker, SourceBundle(files=reference_files), gate)
    (args.output / "preflight.json").write_text(
        json.dumps({"baseline": baseline, "reference": reference}, indent=2)
    )
    if baseline["passed"] or not reference["passed"]:
        raise RuntimeError("Preflight controls failed")
    with WorkLedger(ROOT / ".gflo/evidence/stateful-inventory-feedback-v1/ledger.db") as prior:
        template = json.loads(prior.run_plan("inventory-build-r1-10-consumers-v2"))
    rows = []
    with WorkLedger(args.output / "ledger.db") as ledger:
        broker = DockerBroker(ledger.artifacts, args.image)
        broker.qualify()
        for repetition in range(1, 4):
            identity = f"history-filter-r{repetition}"
            data = json.loads(json.dumps(template))
            revision = manifest["git_base"]
            data.update(
                source=json.loads(source.canonical()),
                gates={"behavior": json.loads(gate.canonical())},
                broker_image=args.image,
                selected_paths=["gflo/cli.py"],
            )
            data["atom"].update(
                atom_id=identity,
                idempotency_key=identity,
                objective=objective,
                source_revision=revision,
                inputs_digest=InputSnapshot(
                    source_digest=source.digest(), source_revision=revision
                ).digest(),
                writable_paths=["gflo/cli.py"],
                prohibited_paths=["tests"],
                upstream_contracts=[],
                required_gates=[{"gate_id": "behavior", "validator_digest": gate.digest()}],
            )
            plan = RunPlan.model_validate_json(json.dumps(data))
            prepare_run(ledger, plan)
            state = Controller(
                ledger, LocalModel(ledger.artifacts, plan.model_profile), broker
            ).run(identity)
            row = {"atom_id": identity, "state": state, "cost": cost_report(ledger, identity)}
            rows.append(row)
            (args.output / "results.json").write_text(json.dumps(rows, indent=2))
            print(
                json.dumps(
                    {
                        "atom_id": identity,
                        "status": state["status"],
                        "attempts": len(state["attempts"]),
                    }
                ),
                flush=True,
            )
            if state["status"] != "accepted":
                break
        summary = {
            "qualified": len(rows) == 3 and all(r["state"]["status"] == "accepted" for r in rows),
            "runs": len(rows),
            "attempts": sum(len(r["state"]["attempts"]) for r in rows),
            "source_drift": any(
                hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != d
                for p, d in manifest["runtime_hashes"].items()
            ),
        }
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
