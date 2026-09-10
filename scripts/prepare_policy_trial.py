#!/usr/bin/env python3
"""Recreate the policy build fixture without inference or product execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gflo.autonomy import FeaturePolicy
from gflo.broker import SourceBundle
from gflo.ledger import WorkLedger
from gflo.planning import RepositoryFeatureRequest
from gflo.repository import snapshot_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path(".scratch/local-lights-out-factory/policy-build-fixture.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_bytes())
    if fixture["schema_version"] != 1:
        raise ValueError("Unsupported fixture version")
    request = RepositoryFeatureRequest.model_validate_json(json.dumps(fixture["request"]))
    policy = FeaturePolicy.model_validate_json(json.dumps(fixture["policy"]))
    if policy.request_digest != request.digest():
        raise ValueError("Policy does not bind fixture request")
    args.output.mkdir(parents=True, exist_ok=False)
    with WorkLedger(args.output / "ledger.db") as ledger:
        source = snapshot_bundle(ledger.artifacts, SourceBundle(files=fixture["source_files"]))
        if source != request.source:
            raise ValueError("Reconstructed source differs from policy request")
    (args.output / "request.json").write_text(request.canonical() + "\n")
    (args.output / "policy.json").write_text(policy.canonical() + "\n")
    print(
        json.dumps(
            {"database": str(args.output / "ledger.db"), "snapshot_digest": source.artifact_digest},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
