#!/usr/bin/env python3
"""Verify evidence links in the accumulated matrix; never claim a fresh fault run."""

import argparse
import collections
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(".scratch/local-lights-out-factory/integrity-coverage.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    rows = report["rows"]
    assert len(rows) == 50 and len({r["id"] for r in rows}) == 50
    categories = collections.Counter(r["category"] for r in rows)
    assert len(categories) == 10 and all(n >= 5 for n in categories.values())
    assert all(r["coverage"] == "covered" for r in rows)
    assert report["full_integrity_campaign_passed"] is False
    checks = []
    for row in rows:
        evidence = row["evidence"]
        if "receipt" in evidence:
            path = Path(evidence["receipt"])
            assert hashlib.sha256(path.read_bytes()).hexdigest() == evidence["sha256"]
            checks.append(dict(row=row["id"], receipt=str(path), hash_matches=True))
    result = dict(
        scope="Accumulated coverage metadata and new live-receipt hash checks, not a fresh fault execution",
        rows=50,
        categories=dict(categories),
        new_receipts=checks,
        source_report_sha256=hashlib.sha256(args.report.read_bytes()).hexdigest(),
        fresh_campaign_passed=False,
    )
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(dict(rows=50, categories=10, new_receipts_checked=len(checks))))


if __name__ == "__main__":
    main()
