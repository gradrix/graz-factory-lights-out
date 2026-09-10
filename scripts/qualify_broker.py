#!/usr/bin/env python3
"""Repeat actual broker qualification, retaining each report and first failure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import BrokerError, DockerBroker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Installed pinned Python image")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 100:
        parser.error("repetitions must be 1–100")
    args.output.mkdir(parents=True, exist_ok=False)
    broker = DockerBroker(ArtifactStore(args.output / "artifacts"), args.image)
    rows = []
    for ordinal in range(1, args.repetitions + 1):
        try:
            row = {"ordinal": ordinal, "status": "pass", "report_digest": broker.qualify()}
        except BrokerError as exc:
            row = {"ordinal": ordinal, "status": "halt", "error": str(exc)}
        rows.append(row)
        (args.output / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(json.dumps(row), flush=True)
        if row["status"] != "pass":
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
