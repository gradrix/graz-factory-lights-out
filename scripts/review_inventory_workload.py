#!/usr/bin/env python3
"""Supplement stateful build gates with boundary requests and quoted SKU workflows."""

import argparse
import json
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import DockerBroker, SourceBundle
from gflo.ledger import WorkLedger
from gflo.pilot import IMAGE
from gflo.records import AcceptanceFinding, WorkAtom
from inventory_workload import CLI_DRIVER, REFERENCE, reference_update, state_oracle
from run_inventory_workload import check, make_gate


def workflows():
    rows = []
    for sku in ["A", "quoted'item", "雪"]:
        ops = [{"op": "create", "sku": sku, "stock": 1000000000}]
        for index, quantity in enumerate([True, False, 0, -1, 1.0, "1", 1000000001, None]):
            ops.append(
                {
                    "op": "reserve",
                    "request_id": "invalid-" + str(index),
                    "sku": sku,
                    "quantity": quantity,
                }
            )
        ops += [
            {"op": "reserve", "request_id": 42, "sku": sku, "quantity": 1},
            {"op": "reserve", "request_id": "", "sku": sku, "quantity": 1},
            {"op": "reserve", "request_id": "valid", "sku": sku, "quantity": 1000000000},
            {"op": "reserve", "request_id": "valid", "sku": sku, "quantity": 1000000000},
            {"op": "cancel", "request_id": "valid"},
            {"op": "cancel", "request_id": "valid"},
            {"op": "reserve", "request_id": "valid", "sku": sku, "quantity": 999999999},
            {"op": "reserve", "request_id": "valid", "sku": sku, "quantity": 1000000000},
            {"op": "create", "sku": sku, "stock": 1},
            {"op": "report"},
            {"op": "audit"},
        ]
        rows.append((("python", "-c", CLI_DRIVER), ops, state_oracle(ops)))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    gate = make_gate(workflows())
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "scope": "Additional boundary review, separate from frozen scoring gates",
                "gate": gate.model_dump(mode="json"),
            },
            indent=2,
        )
        + "\n"
    )
    source = SourceBundle(
        files=REFERENCE
        | reference_update("storage-v2", ["storage.py"])
        | reference_update("consumers-v2", ["cli.py", "reports.py"])
    )
    broker = DockerBroker(ArtifactStore(args.output / "control-artifacts"), IMAGE)
    broker.qualify()
    control = check(broker, source, gate)
    (args.output / "control.json").write_text(json.dumps(control, indent=2) + "\n")
    if not control["passed"]:
        raise RuntimeError("Supplemental reference control failed")
    if args.preflight_only:
        print("Additional boundary reference checks passed", flush=True)
        return
    builds = json.loads((args.campaign / "build-reviews.json").read_text())
    rows = []
    with WorkLedger(args.campaign / "ledger.db") as ledger:
        broker = DockerBroker(ledger.artifacts, IMAGE)
        broker.qualify()
        for build in builds:
            source = SourceBundle.model_validate_json(
                ledger.artifacts.read(build["candidate_digest"])
            )
            review = check(broker, source, gate)
            rows.append(
                {"build": build["build"], "candidate_digest": source.digest(), "review": review}
            )
            if not review["passed"]:
                atom_id = f"inventory-build-r{build['build']}-10-consumers-v2"
                state = ledger.status(atom_id)
                atom = WorkAtom.model_validate_json(json.dumps(state["contract"]))
                evidence = ledger.artifacts.publish(json.dumps(review, sort_keys=True).encode())
                ledger.record_finding(
                    AcceptanceFinding(
                        atom_id=atom_id,
                        contract_digest=atom.digest(),
                        candidate_digest=source.digest(),
                        evidence_digest=evidence,
                        reason="Additional stateful boundary workflow contradicted accepted final build",
                    )
                )
            print(json.dumps({"build": build["build"], "passed": review["passed"]}), flush=True)
    (args.output / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
    if not rows or not all(r["review"]["passed"] for r in rows):
        raise RuntimeError("Stateful boundary review failed; findings retained")


if __name__ == "__main__":
    main()
