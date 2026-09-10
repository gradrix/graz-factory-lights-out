#!/usr/bin/env python3
"""Recreate the portable reviewed expense fixture; no model or product code runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gflo.broker import SourceBundle
from gflo.ledger import WorkLedger
from gflo.progression import FeaturePlan
from gflo.repository import FileEdit, Repository, SnapshotSource, snapshot_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path(".scratch/local-lights-out-factory/feature-progression-fixture.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_bytes())
    if fixture["schema_version"] != 1:
        raise ValueError("Unsupported fixture version")
    plan = FeaturePlan.model_validate_json(json.dumps(fixture["plan"]))
    initial = SourceBundle(files=fixture["initial_files"])
    omitted = fixture["omitted_file"]
    count = omitted["repetitions"]
    if (
        type(count) is not int
        or count < 1
        or len(omitted["line"].encode()) * count > 8 * 1024 * 1024
    ):
        raise ValueError("Invalid omitted-file size")
    args.output.mkdir(parents=True, exist_ok=False)
    with WorkLedger(args.output / "ledger.db") as ledger:
        source = snapshot_bundle(ledger.artifacts, initial)
        source = Repository(SnapshotSource(ledger.artifacts, source)).apply(
            ledger.artifacts,
            {omitted["path"]: FileEdit(expected_digest=None, content=omitted["line"] * count)},
            current_source=source,
            writable_paths=(omitted["path"],),
        )
        if source != plan.request.source:
            raise ValueError("Reconstructed source differs from reviewed fixture")
    (args.output / "plan.json").write_text(plan.canonical() + "\n")
    (args.output / "request.json").write_text(plan.request.canonical() + "\n")
    (args.output / "profile.json").write_text(plan.review.model_profile.canonical() + "\n")
    (args.output / "deployment.json").write_text(plan.review.deployment)
    print(
        json.dumps(
            {
                "database": str(args.output / "ledger.db"),
                "plan": str(args.output / "plan.json"),
                "snapshot_digest": source.artifact_digest,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
