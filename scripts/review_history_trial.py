#!/usr/bin/env python3
"""Run the complete existing CPU suite in bounded candidate containers, plus new cases."""

import argparse
import base64
import json
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.ledger import WorkLedger
from gflo.records import AcceptanceFinding, WorkAtom

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((args.campaign / "manifest.json").read_text())
    results = json.loads((args.campaign / "results.json").read_text())
    test_files = {
        str(p.relative_to(args.checkout)): p.read_text()
        for p in (args.checkout / "tests").glob("test_*.py")
    }
    for p in (ROOT / ".scratch/local-lights-out-factory/self-trial").glob("test_*.py"):
        test_files["tests/" + p.name] = p.read_text()
    rows = []
    with WorkLedger(args.campaign / "ledger.db") as ledger:
        broker = DockerBroker(ledger.artifacts, manifest["image"])
        broker.qualify()
        for run in results:
            state = run["state"]
            if state["status"] != "accepted":
                continue
            candidate = SourceBundle.model_validate_json(
                ledger.artifacts.read(state["candidate_digest"])
            )
            base = {p: s for p, s in candidate.files.items() if not p.startswith("tests/")}
            for test, content in test_files.items():
                files = dict(base)
                files[test] = content
                if test == "tests/test_findings.py":
                    files["tests/test_integration.py"] = test_files["tests/test_integration.py"]
                if test.startswith("tests/test_history_filter"):
                    files["tests/test_controller.py"] = test_files["tests/test_controller.py"]
                    files["tests/test_history_filter.py"] = test_files[
                        "tests/test_history_filter.py"
                    ]
                if any(name in test for name in ["serving", "target"]):
                    for script in ["serve.py", "benchmark_serving.py", "check_target.py"]:
                        files["scripts/" + script] = (
                            args.checkout / "scripts" / script
                        ).read_text()
                bundle = SourceBundle(files=files)
                digest = ledger.artifacts.publish(bundle.canonical().encode())
                execution = broker.execute(
                    digest,
                    ("python", "-m", "pytest", "-q", "-p", "no:cacheprovider", test),
                    stdin="",
                    seconds=60,
                    purpose="validation",
                )
                evidence = ledger.artifacts.publish(execution.canonical().encode())
                passed = execution.outcome == "completed" and execution.exit_code == 0
                row = {
                    "atom_id": state["atom_id"],
                    "candidate_digest": state["candidate_digest"],
                    "test": test,
                    "passed": passed,
                    "execution_digest": evidence,
                    "stdout": execution.stdout.decode(errors="replace")[-1500:],
                    "stderr": base64.b64decode(execution.stderr_base64).decode(errors="replace")[
                        -1500:
                    ],
                }
                rows.append(row)
                (args.output / "results.json").write_text(json.dumps(rows, indent=2))
                print(
                    json.dumps({"atom": state["atom_id"], "test": test, "passed": passed}),
                    flush=True,
                )
                if not passed:
                    atom = WorkAtom.model_validate_json(json.dumps(state["contract"]))
                    ledger.record_finding(
                        AcceptanceFinding(
                            atom_id=atom.atom_id,
                            contract_digest=atom.digest(),
                            candidate_digest=state["candidate_digest"],
                            evidence_digest=evidence,
                            reason="Supervised history trial regression review failed: " + test,
                        )
                    )
                    raise RuntimeError("Review failed; finding retained")


if __name__ == "__main__":
    main()
