#!/usr/bin/env python3
"""Explicit local-model coding smoke; fixed synthetic fixture, no repository upload."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.gates import ProcessCase, ProcessGate, run_gate
from gflo.ledger import WorkLedger
from gflo.model import LocalModel, ModelProfile
from gflo.records import WorkAtom
from gflo.worker import CandidateResult, InputSnapshot, candidate_bundle

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New evidence directory")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    config_path = ROOT / "infra/serving/vllm-5090.example.json"
    config = json.loads(config_path.read_bytes())
    runtime = json.loads(
        subprocess.check_output(
            ["docker", "inspect", config["managed"]["name"]], text=True, timeout=15
        )
    )[0]
    image = json.loads(
        subprocess.check_output(
            ["docker", "image", "inspect", config["managed"]["image"]], text=True, timeout=15
        )
    )[0]
    if not runtime["State"]["Running"] or runtime["Image"] != image["Id"]:
        raise RuntimeError("Expected pinned vLLM service is not running")
    command = runtime["Config"]["Cmd"]
    for flag in ("--revision", "--tokenizer-revision"):
        if command[command.index(flag) + 1] != config["managed"]["revision"]:
            raise RuntimeError("Serving checkpoint/tokenizer pin differs")
    runtime_identity = {
        "image_id": runtime["Image"],
        "command": command,
        "container_id": runtime["Id"],
        "started_at": runtime["State"]["StartedAt"],
    }
    (args.output / "runtime.json").write_text(json.dumps(runtime_identity, indent=2) + "\n")
    cases = [([3, 1, 3, 2, 1], [3, 1, 2]), ([], []), ([-2, 0, -2, 4, 0], [-2, 0, 4])]
    plan = ProcessGate(
        cases=tuple(
            ProcessCase(
                command=("python", "main.py"),
                stdin=json.dumps(given) + "\n",
                expected_stdout=json.dumps(expected) + "\n",
            )
            for given, expected in cases
        )
    )
    with WorkLedger(args.output / "ledger.db") as ledger:
        source = SourceBundle(
            files={
                "main.py": (
                    "import json\nimport sys\n"
                    "print(json.dumps(sorted(set(json.load(sys.stdin)))))\n"
                )
            }
        )
        source_digest = ledger.artifacts.publish(source.canonical().encode())
        fields = json.loads((ROOT / "examples/work-atom.json").read_text())
        fields.update(
            atom_id="worker-coding-smoke-v1",
            idempotency_key="worker-coding-smoke-v1",
            objective=(
                "Repair main.py: read a JSON array of integers from stdin; "
                "output the unique integers in first-occurrence order using "
                "print(json.dumps(result)). Handle empty input arrays and negative integers. "
                "Use Python standard library only. Propose the complete corrected main.py file."
            ),
            source_revision="worker-coding-smoke-v1",
            writable_paths=["main.py"],
            prohibited_paths=[],
            allowed_tools=["edit"],
            required_gates=[{"gate_id": "behavior", "validator_digest": plan.digest()}],
            expected_outputs=[
                {
                    "name": "candidate",
                    "schema_digest": hashlib.sha256(
                        json.dumps(SourceBundle.model_json_schema(), sort_keys=True).encode()
                    ).hexdigest(),
                }
            ],
        )
        fields["inputs_digest"] = InputSnapshot(
            source_digest=source_digest, source_revision=fields["source_revision"]
        ).digest()
        atom = WorkAtom.model_validate_json(json.dumps(fields))
        ledger.submit(atom)
        lease = ledger.claim(atom.atom_id, "trusted-smoke-controller", lease_seconds=300)
        ledger.start(lease)
        profile = ModelProfile(
            base_url=config["base_url"],
            model=config["model"],
            deployment_digest=ledger.artifacts.publish(config_path.read_bytes()),
        )
        client = LocalModel(ledger.artifacts, profile)
        report = {
            "schema_version": 1,
            "workload": "worker-coding-smoke-v1",
            "pilot_complete": False,
            "atom": atom.model_dump(mode="json"),
            "profile": profile.model_dump(mode="json"),
        }
        try:
            turn = client.turn(atom, source_digest, current_inputs=lambda: atom.inputs_digest)
            report["turn"] = turn.model_dump(mode="json")
            if not isinstance(turn.result, CandidateResult):
                raise RuntimeError("Smoke expected a candidate proposal")
            candidate = candidate_bundle(source, turn.result)
            candidate_digest = ledger.artifacts.publish(candidate.canonical().encode())
            ledger.candidate(lease, candidate_digest)
            broker = DockerBroker(
                ledger.artifacts,
                "python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca",
            )
            report["broker_qualification_digest"] = broker.qualify()
            baseline = broker.execute(
                source_digest, ("python", "main.py"), stdin="[3, 1, 3, 2, 1]\n"
            )
            report["baseline_wrong_output_verified"] = baseline.stdout != b"[3, 1, 2]\n"
            receipt = run_gate(ledger, broker, lease, "behavior", plan)
            report["gate"] = receipt.model_dump(mode="json")
            if receipt.outcome == "pass" and report["baseline_wrong_output_verified"]:
                report["acceptance"] = ledger.accept(
                    lease, current_inputs_digest=atom.inputs_digest
                ).model_dump(mode="json")
            else:
                ledger.fail(lease, "Coding smoke did not pass its independent gate")
        except Exception as exc:
            report["error"] = {"type": type(exc).__name__, "message": str(exc)}
            ledger.fail(lease, "Coding smoke failed: " + str(exc)[:1000])
        finally:
            report["model_evidence_digest"] = client.last_evidence_digest
            report["status"] = ledger.status(atom.atom_id)["status"]
            (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "evidence": str(args.output / "summary.json"),
                    "error": report.get("error"),
                },
                indent=2,
            )
        )
        return 0 if report["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
