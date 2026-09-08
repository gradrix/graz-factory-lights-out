#!/usr/bin/env python3
"""Freeze and record the deterministic recovery subset; not the full integrity campaign."""

import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    (
        "model-protocol",
        "tests/test_controller.py::test_model_failure_windows_preserve_evidence_and_bounded_resume",
        5,
    ),
    (
        "gate-controller-interruption",
        "tests/test_controller.py::test_gate_interruption_windows_resume_without_false_acceptance",
        5,
    ),
    (
        "acceptance-commit",
        "tests/test_controller.py::test_acceptance_commit_failure_resumes_without_duplicate_work",
        3,
    ),
    ("storage", "tests/test_storage.py", 9),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    files = sorted((ROOT / "gflo").glob("*.py")) + [
        ROOT / "tests/test_controller.py",
        ROOT / "tests/test_storage.py",
        Path(__file__).resolve(),
    ]
    manifest = {
        "schema_version": 1,
        "name": "deterministic-recovery-subset-v2",
        "scope": (
            "Injected protocol/control-flow/storage faults; "
            "not physical process death or power loss"
        ),
        "full_integrity_campaign": False,
        "cases": CASES,
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
        },
        "python": sys.version,
        "deadline_seconds_per_group": 60,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    groups = []
    for category, selector, expected in CASES:
        xml = root / (category + ".xml")
        command = [sys.executable, "-m", "pytest", "-q", selector, "--junitxml=" + str(xml)]
        try:
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60)
            (root / (category + ".log")).write_text(result.stdout + result.stderr)
            records = []
            for case in ET.parse(xml).iter("testcase"):
                records.append(
                    {
                        "name": case.get("name"),
                        "class": case.get("classname"),
                        "seconds": float(case.get("time", "0")),
                        "outcome": "failed"
                        if case.find("failure") is not None or case.find("error") is not None
                        else "skipped"
                        if case.find("skipped") is not None
                        else "passed",
                    }
                )
            passed = (
                result.returncode == 0
                and len(records) == expected
                and all(r["outcome"] == "passed" for r in records)
            )
            group = {
                "category": category,
                "passed": passed,
                "cases": records,
                "returncode": result.returncode,
            }
        except (subprocess.TimeoutExpired, OSError, ET.ParseError) as exc:
            group = {"category": category, "passed": False, "error": str(exc)}
        groups.append(group)
        (root / "results.json").write_text(json.dumps(groups, indent=2) + "\n")
    summary = {
        "selected_subset_passed": all(g["passed"] for g in groups),
        "full_integrity_campaign_passed": False,
        "groups": groups,
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "selected_subset_passed": summary["selected_subset_passed"],
                "full_integrity_campaign_passed": False,
                "evidence": str(root),
            }
        )
    )
    return 0 if summary["selected_subset_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
