#!/usr/bin/env python3
"""Three bounded repairs of a retained rejected candidate; never reset its history."""

import argparse
import hashlib
import json
from pathlib import Path

from inventory_workload import steps
from run_inventory_workload import check, make_gate, review_workflows

from gflo.broker import DockerBroker, SourceBundle
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.ledger import WorkLedger
from gflo.model import LocalModel
from gflo.records import AcceptanceFinding
from gflo.worker import InputSnapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    with WorkLedger(args.campaign / "ledger.db") as original:
        old = RunPlan.model_validate_json(original.run_plan("inventory-build-r2-10-consumers-v2"))
        source = SourceBundle.model_validate_json(
            original.artifacts.read(
                "a95ccf89b7946d560a21538edcf83ab03606bb0b33068b0216856439e282b5a4"
            )
        )
        contracts = {d: original.artifacts.read(d) for d in old.atom.upstream_contracts}
    manifest = {
        "scope": "Seen failure, three fresh bounded repairs; not held-out qualification",
        "source_digest": source.digest(),
        "gate_digest": old.gates["behavior"].digest(),
        "profile": old.model_profile.model_dump(mode="json"),
        "objective": steps()[-1][3],
        "source_hashes": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                *Path("gflo").glob("*.py"),
                Path(__file__),
                Path("scripts/inventory_workload.py"),
                Path("scripts/run_inventory_workload.py"),
            ]
        },
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    rows = []
    with WorkLedger(args.output / "ledger.db") as ledger:
        for data in contracts.values():
            ledger.artifacts.publish(data)
        broker = DockerBroker(ledger.artifacts, old.broker_image)
        broker.qualify()
        control = check(broker, source, old.gates["behavior"])
        (args.output / "control.json").write_text(json.dumps(control, indent=2))
        if control["passed"]:
            raise RuntimeError("Retained failure unexpectedly passes")
        for repetition in range(1, 4):
            identity = f"migration-repair-r{repetition}"
            revision = "retained-rejected-" + source.digest()
            data = json.loads(old.canonical())
            data["source"] = json.loads(source.canonical())
            data["atom"].update(
                atom_id=identity,
                idempotency_key=identity,
                source_revision=revision,
                inputs_digest=InputSnapshot(
                    source_digest=source.digest(), source_revision=revision
                ).digest(),
                objective=steps()[-1][3],
            )
            plan = RunPlan.model_validate_json(json.dumps(data))
            prepare_run(ledger, plan)
            state = Controller(
                ledger, LocalModel(ledger.artifacts, plan.model_profile), broker
            ).run(identity)
            review = None
            if state["status"] == "accepted":
                candidate = SourceBundle.model_validate_json(
                    ledger.artifacts.read(state["candidate_digest"])
                )
                review = check(broker, candidate, make_gate(review_workflows()))
                if not review["passed"]:
                    evidence = ledger.artifacts.publish(json.dumps(review, sort_keys=True).encode())
                    ledger.record_finding(
                        AcceptanceFinding(
                            atom_id=identity,
                            contract_digest=plan.atom.digest(),
                            candidate_digest=candidate.digest(),
                            evidence_digest=evidence,
                            reason="Migration repair failed supplemental workflow review",
                        )
                    )
            row = {
                "atom_id": identity,
                "status": state["status"],
                "attempts": len(state["attempts"]),
                "candidate_digest": state["candidate_digest"],
                "review": review,
            }
            rows.append(row)
            (args.output / "results.json").write_text(json.dumps(rows, indent=2))
            print(json.dumps(row), flush=True)
            if state["status"] not in ("accepted", "quarantined"):
                raise RuntimeError("Infrastructure halt")


if __name__ == "__main__":
    main()
