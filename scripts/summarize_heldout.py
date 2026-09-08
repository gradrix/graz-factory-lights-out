#!/usr/bin/env python3
"""Summarize frozen held-out results without excluding failures or changing scores."""

import argparse
import collections
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def summarize(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    rows = json.loads((directory / "results.json").read_text())
    expected = {p["atom"]["atom_id"] for p in manifest["plans"]}
    actual = [r["task"] for r in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected or len(rows) != 120:
        raise ValueError("Missing, duplicate or unexpected task runs")
    drift = [
        name
        for name, digest in manifest["source_sha256"].items()
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
    ]
    reviewed = json.loads((directory / "semantic-review/results.json").read_text())
    expected_review = {
        r["task"] for r in rows if r["status"] == "accepted" and r["category"] != "test-generation"
    }
    if {r["task"] for r in reviewed} != expected_review or len(reviewed) != len(expected_review):
        raise ValueError("Semantic review omitted or duplicated accepted task runs")
    domain_review = json.loads((directory / "test-generation-domain-review.json").read_text())
    expected_tests = sum(
        r["status"] == "accepted" and r["category"] == "test-generation" for r in rows
    )
    if domain_review["reviewed"] != expected_tests or domain_review["domain_problems"]:
        raise ValueError("Test-generation domain review is incomplete or found invalid cases")
    bad = {r["task"] for r in reviewed if not r["passed"]}
    groups = {}
    for category in sorted({r["category"] for r in rows}):
        group = [r for r in rows if r["category"] == category]
        groups[category] = dict(
            runs=len(group),
            accepted=sum(r["status"] == "accepted" for r in group),
            verified=sum(r["status"] == "accepted" and r["task"] not in bad for r in group),
            false_acceptances=sum(r["task"] in bad for r in group),
            first_attempt=sum(r["status"] == "accepted" and r["attempts"] == 1 for r in group),
            attempts=sum(r["attempts"] for r in group),
        )
    totals = collections.Counter()
    observations = []
    for row in rows:
        for key, value in row["cost"]["totals"].items():
            if type(value) in (int, float):
                totals[key] += value
        observations.extend(o for a in row["cost"]["attempts"] for o in a["observations"])
    review = json.loads((directory / "semantic-review/summary.json").read_text())
    audit = json.loads((directory / "audit.json").read_text())
    accepted = sum(r["status"] == "accepted" for r in rows)
    failures = [
        dict(
            task=r["task"],
            status=r["status"],
            error=r["error"],
            failure_reasons=[f for a in r["cost"]["attempts"] for f in a["failures"]],
        )
        for r in rows
        if r["status"] != "accepted"
    ]
    result = dict(
        workload=manifest["workload"],
        distinct_tasks=40,
        repetitions=3,
        runs=120,
        gate_accepted=accepted,
        independently_verified=accepted - len(bad),
        false_acceptance_runs=sorted(bad),
        by_class=groups,
        totals=dict(totals),
        attempts_histogram=dict(collections.Counter(r["attempts"] for r in rows)),
        median_atom_seconds=statistics.median(r["elapsed_seconds"] for r in rows),
        cumulative_atom_seconds=sum(r["elapsed_seconds"] for r in rows),
        max_validated_prompt_tokens=max(o["prompt_tokens"] or 0 for o in observations),
        output_reserved_tokens=2048,
        factory_source_drift=drift,
        semantic_review=review,
        failures=failures,
        raw_receipts={
            name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
            for name in [
                "manifest.json",
                "preflight.json",
                "results.json",
                "audit.json",
                "semantic-probes.json",
                "semantic-review/results.json",
                "test-generation-domain-review.json",
            ]
        },
        numerical_thresholds_met=accepted - len(bad) >= 108
        and all(g["verified"] >= 24 for g in groups.values()),
        progression_qualified=accepted - len(bad) >= 108
        and all(g["verified"] >= 24 for g in groups.values())
        and review["discrepancies"] == 0
        and not drift
        and not audit["missing"]
        and not audit["corrupt"],
        limits=[
            "Forty distinct small Python tasks; repetitions are not independent new tasks.",
            "Test generation is JSON test-data generation with known-good and three seeded defects per task.",
            "Semantic probes cover accepted implementation, repair and migration outputs; finite checks cannot prove absence of bugs.",
            "One 8K context policy on the qualified 16K server; no 4K/16K/32K policy comparison.",
            "Prepared atoms, not autonomous product decomposition or general large-build feasibility.",
        ],
    )
    (directory / "evaluation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    summarize(parser.parse_args().directory)
