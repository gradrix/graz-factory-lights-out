#!/usr/bin/env python3
"""Qualify a new gate against a retained false acceptance; never rescore it."""

import argparse
import json
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import DockerBroker, SourceBundle
from gflo.controller import RunPlan
from gflo.gates import ProcessCase, ProcessGate
from gflo.pilot import IMAGE
from gflo.worker import InputSnapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task", default="heldout-v1-r1-dedupe-last")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((args.campaign / "manifest.json").read_text())
    task = args.task
    name = task.split("-", 3)[-1]
    original = next(p for p in manifest["plans"] if p["atom"]["atom_id"] == task)
    row = next(
        r for r in json.loads((args.campaign / "results.json").read_text()) if r["task"] == task
    )
    bad = SourceBundle.model_validate_json(
        (args.campaign / "ledger.db.artifacts" / row["state"]["candidate_digest"]).read_bytes()
    )
    fixture = next(f for f in manifest["fixtures"] if f["name"] == name)
    reference = SourceBundle(files=fixture["reference"])
    extra = next(
        p
        for p in json.loads((args.campaign / "semantic-probes.json").read_text())["probes"]
        if p["task"] == name
    )
    gate = ProcessGate.model_validate_json(json.dumps(original["gates"]["behavior"]))
    gate = ProcessGate(
        cases=gate.cases
        + tuple(
            ProcessCase(
                command=("python", "main.py"),
                stdin=json.dumps(x) + "\n",
                expected_stdout=json.dumps(y, sort_keys=True) + "\n",
            )
            for x, y in zip(extra["inputs"], extra["expected"], strict=True)
        )
    )
    fields = original.copy()
    fields["source"] = bad.model_dump(mode="json")
    fields["gates"] = {"behavior": gate.model_dump(mode="json")}
    fields["atom"] = original["atom"] | dict(
        atom_id=f"regression-{name}-v1",
        idempotency_key=f"regression-{name}-v1",
        source_revision="retained-false-acceptance-" + bad.digest(),
        required_gates=[dict(gate_id="behavior", validator_digest=gate.digest())],
    )
    fields["atom"]["inputs_digest"] = InputSnapshot(
        source_digest=bad.digest(), source_revision=fields["atom"]["source_revision"]
    ).digest()
    plan = RunPlan.model_validate_json(json.dumps(fields))
    (args.output / "repair-plan.json").write_text(plan.canonical() + "\n")
    (args.output / "manifest.json").write_text(
        json.dumps(
            dict(
                scope="Seen regression; original frozen campaign remains unchanged",
                original_task=task,
                original_candidate=bad.digest(),
                gate=gate.model_dump(mode="json"),
                reference=reference.model_dump(mode="json"),
            ),
            indent=2,
        )
        + "\n"
    )
    store = ArtifactStore(args.output / "artifacts")
    broker = DockerBroker(store, IMAGE)
    broker.qualify()
    observations = []
    for label, bundle in [("retained-bad", bad), ("known-good", reference)]:
        digest = store.publish(bundle.canonical().encode())
        checks = []
        for case in gate.cases:
            checked = broker.execute(
                digest, case.command, stdin=case.stdin, seconds=case.seconds, purpose="validation"
            )
            checks.append(
                dict(
                    passed=checked.outcome == "completed"
                    and checked.exit_code == 0
                    and checked.stdout == case.expected_stdout.encode(),
                    execution=checked.digest(),
                )
            )
        observations.append(
            dict(candidate=label, cases=checks, all_pass=all(c["passed"] for c in checks))
        )
    result = dict(
        qualified=not observations[0]["all_pass"] and observations[1]["all_pass"],
        observations=observations,
    )
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    if not result["qualified"]:
        raise RuntimeError("Regression gate did not distinguish bad and good candidates")


if __name__ == "__main__":
    main()
