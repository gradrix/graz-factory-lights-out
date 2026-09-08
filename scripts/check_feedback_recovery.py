#!/usr/bin/env python3
"""Matched diagnostic follow-up on a seen failure; never a held-out score."""

import argparse
import dataclasses
import hashlib
import json
from pathlib import Path

from gflo.feedback import validation_feedback

import gflo.controller as controller_module
from gflo.broker import DockerBroker, SourceBundle
from gflo.controller import OWNER, Controller, RunPlan, prepare_run
from gflo.ledger import WorkLedger
from gflo.model import LocalModel
from gflo.reporting import cost_report
from gflo.worker import Diagnostic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    original = json.loads((args.campaign / "manifest.json").read_text())
    task = "heldout-v1-r1-balanced-brackets"
    fields = next(p for p in original["plans"] if p["atom"]["atom_id"] == task)
    fields["atom"]["max_attempts"] = 3
    plan = RunPlan.model_validate_json(json.dumps(fields))
    row = next(
        r for r in json.loads((args.campaign / "results.json").read_text()) if r["task"] == task
    )
    first = row["state"]["attempts"][0]
    digest = next(e["details"]["digest"] for e in first["events"] if e["kind"] == "candidate")
    seed = SourceBundle.model_validate_json(
        (args.campaign / "ledger.db.artifacts" / digest).read_bytes()
    )
    manifest = dict(
        scope="Seen failure, seeded retained candidate, three pairs with at most two actual model repair attempts each",
        plan=plan.model_dump(mode="json"),
        seed_candidate=seed.digest(),
        modes=["legacy", "readable"],
        repetitions=3,
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path("gflo").glob("*.py"))
        },
    )
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    results = []
    for repetition in range(1, 4):
        for mode in ("legacy", "readable"):
            controller_module.validation_feedback = (
                (
                    lambda observation: (
                        "Validation did not pass. Observations: " + json.dumps(observation)
                    )
                )
                if mode == "legacy"
                else validation_feedback
            )
            root = args.output / f"{mode}-{repetition}"
            root.mkdir()
            with WorkLedger(root / "ledger.db", reserve_bytes=268435456) as ledger:
                prepare_run(ledger, plan)
                lease = ledger.claim(plan.atom.atom_id, OWNER, lease_seconds=1800)
                ledger.start(lease)
                evidence = ledger.artifacts.publish(
                    json.dumps(
                        dict(
                            kind="replayed-heldout-candidate-no-inference",
                            source=str(args.campaign),
                            candidate=digest,
                        )
                    ).encode()
                )
                ledger.observe(
                    lease,
                    "diagnostic",
                    ledger.artifacts.publish(
                        Diagnostic(
                            source_digest=evidence,
                            text="Retained failing candidate seeded without inference for matched repair comparison.",
                        )
                        .canonical()
                        .encode()
                    ),
                )
                ledger.candidate(lease, ledger.artifacts.publish(seed.canonical().encode()))
                controller = Controller(
                    ledger,
                    LocalModel(ledger.artifacts, plan.model_profile),
                    DockerBroker(ledger.artifacts, plan.broker_image),
                )
                state = controller.run(plan.atom.atom_id)
                audit = dataclasses.asdict(ledger.audit_artifacts())
                assert not audit["missing"] and not audit["corrupt"]
                if state["status"] == "accepted":
                    assert controller.run(plan.atom.atom_id) == state
                results.append(
                    dict(
                        mode=mode,
                        repetition=repetition,
                        status=state["status"],
                        state=state,
                        cost=cost_report(ledger, plan.atom.atom_id),
                        audit=audit,
                    )
                )
                (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
                print(
                    json.dumps(
                        dict(
                            mode=mode,
                            repetition=repetition,
                            status=state["status"],
                            attempts=len(state["attempts"]),
                        )
                    ),
                    flush=True,
                )
    controller_module.validation_feedback = validation_feedback
    summary = {
        mode: sum(r["status"] == "accepted" for r in results if r["mode"] == mode)
        for mode in ("legacy", "readable")
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
