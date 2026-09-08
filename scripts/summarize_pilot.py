#!/usr/bin/env python3
"""Summarize retained pilot records without changing scores or rerunning work."""

import argparse
import collections
import hashlib
import json
import statistics
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory
    manifest = json.loads((root / "manifest.json").read_text())
    results = json.loads((root / "results.json").read_text())
    artifacts = root / "ledger.db.artifacts"
    tasks = []
    all_turns = []
    failures = []
    for result in results:
        turns = []
        for attempt in result["state"]["attempts"]:
            for event in attempt["events"]:
                if event["kind"] == "failed":
                    failures.append(
                        {
                            "task": result["task"],
                            "attempt_id": attempt["attempt_id"],
                            "reason": event["details"]["reason"],
                        }
                    )
                if event["kind"] != "observation" or event["details"]["kind"] != "model":
                    continue
                evidence = json.loads((artifacts / event["details"]["digest"]).read_text())
                turn = {
                    "evidence_digest": event["details"]["digest"],
                    "error": evidence.get("error"),
                    "client_seconds": evidence.get("elapsed_seconds"),
                }
                if "turn_digest" in evidence:
                    record = json.loads((artifacts / evidence["turn_digest"]).read_text())
                    turn.update(
                        prompt_tokens=record["prompt_tokens"],
                        completion_tokens=record["completion_tokens"],
                        kind=record["result"]["kind"],
                    )
                generation = next(
                    (e for e in evidence["exchanges"] if e["path"] == "/v1/chat/completions"), None
                )
                if generation:
                    turn["generation_http_seconds"] = generation.get("elapsed_seconds")
                turns.append(turn)
        tasks.append(
            {
                "task": result["task"],
                "category": result["category"],
                "status": result["status"],
                "attempts": result["attempts"],
                "elapsed_seconds": result["elapsed_seconds"],
                "model_turns": turns,
                "error": result["error"],
            }
        )
        all_turns.extend(turns)
    memory = []
    host_available = []
    for line in (root / "resources.jsonl").read_text().splitlines():
        sample = json.loads(line)
        if "gpu_memory_mib_utilization_percent_power_w" in sample:
            memory.append(float(sample["gpu_memory_mib_utilization_percent_power_w"].split(",")[0]))
            host_available.append(int(sample["host_mem_available"].split()[0]))
    counted = [t for t in all_turns if "prompt_tokens" in t]
    generation = [
        t["generation_http_seconds"]
        for t in all_turns
        if t.get("generation_http_seconds") is not None
    ]
    categories = {
        category: dict(collections.Counter(t["status"] for t in tasks if t["category"] == category))
        for category in sorted({t["category"] for t in tasks})
    }
    report = {
        "schema_version": 1,
        "workload": manifest["workload"],
        "fixture_sha256": manifest["fixture_sha256"],
        "tasks_completed": len(tasks),
        "accepted": sum(t["status"] == "accepted" for t in tasks),
        "first_attempt_accepted": sum(
            t["status"] == "accepted" and t["attempts"] == 1 for t in tasks
        ),
        "categories": categories,
        "model_turns": len(all_turns),
        "read_requests": sum(t.get("kind") == "read_file" for t in all_turns),
        "prompt_tokens": sum(t["prompt_tokens"] for t in counted),
        "completion_tokens": sum(t["completion_tokens"] for t in counted),
        "turns_without_validated_token_usage": len(all_turns) - len(counted),
        "max_actual_turn_tokens": max(
            (t["prompt_tokens"] + t["completion_tokens"] for t in counted), default=0
        ),
        "generation_http_seconds_median": statistics.median(generation) if generation else None,
        "generation_http_seconds_max": max(generation, default=0),
        "task_seconds_sum": sum(t["elapsed_seconds"] for t in tasks),
        "sampled_peak_total_gpu_memory_mib": max(memory, default=0),
        "minimum_host_mem_available_kib": min(host_available, default=0),
        "tasks": tasks,
        "failures": failures,
        "engine_comparison_complete": False,
        "limitations": [
            "Development fixtures, one run per task, not a held-out campaign",
            "Test generation is declarative JSON cases evaluated by a trusted immutable driver",
            "One vLLM serving profile; no optimized-engine comparison",
            "Resource samples include desktop/preflight; energy is not attributed to tasks",
        ],
    }
    (root / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    hashes = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name not in (".broker.lock", ".controller.lock", "sha256.json")
    }
    (root / "sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ("tasks", "failures", "limitations")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
