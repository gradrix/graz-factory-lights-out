#!/usr/bin/env python3
"""Compare explicit reasoning and contract guidance on a seen version-sort failure."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from gflo.broker import DockerBroker
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.ledger import WorkLedger
from gflo.model import LocalModel
from gflo.reporting import cost_report

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--output-tokens", type=int, choices=(2048, 4096), default=2048)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    original = RunPlan.model_validate_json(
        json.dumps(json.loads(args.source_manifest.read_text())["plan"])
    )
    config = json.loads(original.deployment)
    identity = json.loads(
        subprocess.check_output(
            ["docker", "inspect", config["managed"]["name"]], text=True, timeout=15
        )
    )[0]
    image = json.loads(
        subprocess.check_output(
            ["docker", "image", "inspect", config["managed"]["image"]], text=True, timeout=15
        )
    )[0]
    if not identity["State"]["Running"] or identity["Image"] != image["Id"]:
        raise RuntimeError("Expected pinned deployment is not running")
    command = identity["Config"]["Cmd"]
    for flag in ("--revision", "--tokenizer-revision"):
        if command[command.index(flag) + 1] != config["managed"]["revision"]:
            raise RuntimeError("Checkpoint or tokenizer revision differs")
    plans = []
    # Rotate order by repetition; do not change budgets or gates across treatments.
    treatments = ["baseline", "reasoning", "contract-guidance"]
    for repetition in range(3):
        for treatment in treatments[repetition:] + treatments[:repetition]:
            data = original.model_dump(mode="json")
            atom_id = f"version-diagnosis-r{repetition + 1}-{treatment}"
            data["atom"].update(atom_id=atom_id, idempotency_key=atom_id, max_attempts=1)
            data["max_model_turns"] = 1
            data["atom"]["context_budget"]["output_tokens"] = args.output_tokens
            if treatment == "reasoning":
                data["model_profile"]["profile_id"] = "vllm-python-worker-reasoning-v1"
            if treatment == "contract-guidance":
                data["atom"]["objective"] += (
                    " Repair the connection between the existing compare_versions function "
                    "and sorting. The comparator already defines zero-padded numeric equality. "
                    "Preserve that comparison behavior and stable ordering when wiring it "
                    "into sorting; unpadded component-list keys are not equivalent."
                )
            plans.append((treatment, RunPlan.model_validate_json(json.dumps(data))))
    sources = sorted((ROOT / "gflo").glob("*.py")) + [Path(__file__).resolve()]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    manifest = {
        "scope": "Seen failure diagnosis, not held-out qualification or autonomous decomposition",
        "policy": (
            "Three rotated repetitions; one attempt and one model turn per treatment; "
            "fixed gates and budgets"
        ),
        "source_manifest_sha256": hashlib.sha256(args.source_manifest.read_bytes()).hexdigest(),
        "source_sha256": hashes,
        "runtime": {"image_id": image["Id"], "container_id": identity["Id"], "command": command},
        "plans": [{"treatment": t, "plan": p.model_dump(mode="json")} for t, p in plans],
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    results = []
    with WorkLedger(args.output / "ledger.db", reserve_bytes=256 * 1024 * 1024) as ledger:
        broker = DockerBroker(ledger.artifacts, original.broker_image)
        broker.qualify()
        for treatment, plan in plans:
            atom_id = prepare_run(ledger, plan)
            started = time.monotonic()
            state = Controller(
                ledger, LocalModel(ledger.artifacts, plan.model_profile), broker
            ).run(atom_id)
            row = {
                "treatment": treatment,
                "atom_id": atom_id,
                "state": state,
                "cost": cost_report(ledger, atom_id),
                "elapsed_seconds": time.monotonic() - started,
            }
            results.append(row)
            (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
            print(
                json.dumps(
                    {
                        "atom": atom_id,
                        "status": state["status"],
                        "candidate": state.get("candidate_digest"),
                        "elapsed_seconds": row["elapsed_seconds"],
                    }
                ),
                flush=True,
            )
    if any(
        hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
        for name, digest in hashes.items()
    ):
        raise RuntimeError("Source drift during diagnosis")
    (args.output / "completed.json").write_text(
        json.dumps({"source_drift": False, "runs": len(results)}) + "\n"
    )


if __name__ == "__main__":
    main()
