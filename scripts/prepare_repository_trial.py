#!/usr/bin/env python3
"""Recreate a pinned repository qualification without running repository code."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from gflo.autonomy import FeaturePolicy, compile_feature
from gflo.ledger import WorkLedger
from gflo.planning import PlanProposal, RepositoryFeatureRequest
from gflo.repository import FileEdit, Repository, SnapshotSource, capture_worktree


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--test-followup", action="store_true")
    parser.add_argument("--reviewed-plan", action="store_true")
    args = parser.parse_args()
    if args.reviewed_plan and not args.test_followup:
        raise ValueError("Reviewed plan requires --test-followup")
    fixture = json.loads(args.fixture.read_bytes())
    if fixture["schema_version"] != 1:
        raise ValueError("Unsupported fixture version")
    revision = subprocess.check_output(
        ["git", "-C", str(args.checkout), "rev-parse", "HEAD"], text=True, timeout=15
    ).strip()
    if revision != fixture["revision"]:
        raise ValueError("Checkout does not match the pinned Git revision")
    request = RepositoryFeatureRequest.model_validate_json(json.dumps(fixture["request"]))
    policy = FeaturePolicy.model_validate_json(json.dumps(fixture["policy"]))
    if policy.request_digest != request.digest():
        raise ValueError("Policy does not bind fixture request")
    args.output.mkdir(parents=True, exist_ok=False)
    with WorkLedger(args.output / "ledger.db") as ledger:
        source = capture_worktree(ledger.artifacts, args.checkout)
        if source != request.source:
            raise ValueError("Captured checkout bytes differ from the pinned trial source")
        if args.test_followup:
            followup = fixture["test_followup"]
            repository = Repository(SnapshotSource(ledger.artifacts, source))
            edits = {
                path: FileEdit(
                    expected_digest=(
                        repository.source.files[path].content_digest
                        if path in repository.source.files
                        else None
                    ),
                    content=content,
                )
                for path, content in followup["source_edits"].items()
            }
            source = repository.apply(
                ledger.artifacts, edits, current_source=source, writable_paths=tuple(edits)
            )
            request = RepositoryFeatureRequest.model_validate_json(json.dumps(followup["request"]))
            policy = FeaturePolicy.model_validate_json(json.dumps(followup["policy"]))
            if source != request.source or policy.request_digest != request.digest():
                raise ValueError("Follow-up source or policy differs from the pinned request")
        if args.reviewed_plan:
            proposal = PlanProposal.model_validate_json(json.dumps(fixture["reviewed_proposal"]))
            plan = compile_feature(ledger.artifacts, request, proposal, policy)
            (args.output / "feature-plan.json").write_text(plan.canonical() + "\n")
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
