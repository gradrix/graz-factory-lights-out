#!/usr/bin/env python3
"""Freeze/preflight/run forty held-out tasks, three fresh repetitions each."""

import argparse
import dataclasses
import datetime
import hashlib
import json
import subprocess
import threading
import time
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import DockerBroker, SourceBundle
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.heldout import fixtures
from gflo.ledger import WorkLedger
from gflo.model import LocalModel
from gflo.pilot import IMAGE, make_plan
from gflo.reporting import cost_report

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New evidence directory")
    parser.add_argument(
        "--config", type=Path, default=ROOT / "infra/serving/vllm-5090-graphs.example.json"
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    config_path = args.config
    deployment = config_path.read_text()
    config = json.loads(deployment)
    identity = json.loads(
        subprocess.check_output(
            ["docker", "inspect", config["managed"]["name"]], text=True, timeout=15
        )
    )[0]
    expected = json.loads(
        subprocess.check_output(
            ["docker", "image", "inspect", config["managed"]["image"]], text=True, timeout=15
        )
    )[0]
    if not identity["State"]["Running"] or identity["Image"] != expected["Id"]:
        raise RuntimeError("Qualified model container/image is not running")
    command = identity["Config"]["Cmd"]
    for flag in ("--revision", "--tokenizer-revision"):
        if command[command.index(flag) + 1] != config["managed"]["revision"]:
            raise RuntimeError("Model revision drift")
    tasks = fixtures()
    plans = [make_plan(task, deployment, ROOT / "examples/work-atom.json") for task in tasks]
    expanded = []
    for repetition in range(1, 4):
        for plan in plans:
            fields = plan.model_dump(mode="json")
            name = plan.atom.atom_id.removeprefix("pilot-v1-")
            fields["atom"]["atom_id"] = f"heldout-v1-r{repetition}-{name}"
            fields["atom"]["idempotency_key"] = fields["atom"]["atom_id"]
            fields["atom"]["max_attempts"] = 10
            expanded.append(RunPlan.model_validate_json(json.dumps(fields)))
    manifest = {
        "schema_version": 1,
        "workload": "forty-task-heldout-v1",
        "frozen_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "fixture_sha256": hashlib.sha256(
            json.dumps([dataclasses.asdict(f) for f in tasks], sort_keys=True).encode()
        ).hexdigest(),
        "fixtures": [dataclasses.asdict(f) for f in tasks],
        "plans": [p.model_dump(mode="json") for p in expanded],
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "gflo").glob("*.py"))
        },
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime": {
            "image_id": identity["Image"],
            "container_id": identity["Id"],
            "command": command,
        },
        "policy": {
            "attempts_per_atom": 10,
            "model_turns_per_attempt": 3,
            "context_total": 8192,
            "output_reserve": 2048,
            "request_deadline_seconds": 120,
            "automatic_infrastructure_retry": False,
            "held_out": True,
            "repetitions": 3,
            "storage_reserve_bytes": 268435456,
            "overall_target": 108,
            "per_class_target": 24,
            "engine_comparison_complete": False,
        },
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    stop = threading.Event()

    def sample():
        with (args.output / "resources.jsonl").open("w") as output:
            while not stop.is_set():
                try:
                    gpu = subprocess.check_output(
                        [
                            "nvidia-smi",
                            "--query-gpu=memory.used,utilization.gpu,power.draw",
                            "--format=csv,noheader,nounits",
                        ],
                        text=True,
                        timeout=5,
                    ).strip()
                    mem = {
                        line.split(":")[0]: line.split(":")[1].strip()
                        for line in Path("/proc/meminfo").read_text().splitlines()
                    }
                    output.write(
                        json.dumps(
                            {
                                "time": time.time(),
                                "gpu_memory_mib_utilization_percent_power_w": gpu,
                                "host_mem_available": mem["MemAvailable"],
                            }
                        )
                        + "\n"
                    )
                    output.flush()
                except Exception as exc:
                    output.write(json.dumps({"time": time.time(), "sample_error": str(exc)}) + "\n")
                stop.wait(1)

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    results = []
    try:
        preflight_store = ArtifactStore(args.output / "preflight.artifacts")
        broker = DockerBroker(preflight_store, IMAGE)
        qualification = broker.qualify()
        preflight = []
        for fixture, plan in zip(tasks, plans, strict=True):
            original = preflight_store.publish(plan.source.canonical().encode())
            reference = preflight_store.publish(
                SourceBundle(files=fixture.reference).canonical().encode()
            )
            baseline_fails = False
            reference_passes = True
            observations = []
            for case in plan.gates["behavior"].cases:
                checked = broker.execute(
                    reference,
                    case.command,
                    stdin=case.stdin,
                    seconds=case.seconds,
                    purpose="validation",
                )
                reference_passes &= (
                    checked.exit_code == 0
                    and checked.outcome == "completed"
                    and checked.stdout == case.expected_stdout.encode()
                )
                observations.append({"reference_execution": checked.digest()})
                if not baseline_fails:
                    bad = broker.execute(
                        original,
                        case.command,
                        stdin=case.stdin,
                        seconds=case.seconds,
                        purpose="candidate",
                    )
                    baseline_fails = (
                        bad.exit_code != 0 or bad.stdout != case.expected_stdout.encode()
                    )
                    observations[-1]["baseline_execution"] = bad.digest()
            item = {
                "task": fixture.name,
                "reference_passes": reference_passes,
                "baseline_fails": baseline_fails,
                "observations": observations,
            }
            preflight.append(item)
            (args.output / "preflight.json").write_text(
                json.dumps({"qualification": qualification, "tasks": preflight}, indent=2) + "\n"
            )
            print(json.dumps({"phase": "preflight", **item}), flush=True)
            if not reference_passes or not baseline_fails:
                raise RuntimeError(
                    "Fixture qualification failed before model scoring: " + fixture.name
                )
        with WorkLedger(args.output / "ledger.db", reserve_bytes=268435456) as ledger:
            model = LocalModel(ledger.artifacts, plans[0].model_profile)
            broker = DockerBroker(ledger.artifacts, IMAGE)
            controller = Controller(ledger, model, broker)
            for fixture, plan in zip(tasks * 3, expanded, strict=True):
                prepare_run(ledger, plan)
                started = time.monotonic()
                error = None
                try:
                    state = controller.run(plan.atom.atom_id)
                except Exception as exc:
                    error = {"type": type(exc).__name__, "message": str(exc)}
                    state = ledger.status(plan.atom.atom_id)
                result = {
                    "task": plan.atom.atom_id,
                    "category": fixture.category,
                    "elapsed_seconds": time.monotonic() - started,
                    "status": state["status"],
                    "attempts": len(state["attempts"]),
                    "error": error,
                    "state": state,
                    "cost": cost_report(ledger, plan.atom.atom_id),
                }
                results.append(result)
                (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
                print(json.dumps({k: v for k, v in result.items() if k != "state"}), flush=True)
            audit = ledger.audit_artifacts()
            (args.output / "audit.json").write_text(
                json.dumps(dataclasses.asdict(audit), indent=2) + "\n"
            )
    finally:
        stop.set()
        thread.join(timeout=6)
    by_class = {
        category: sum(r["status"] == "accepted" for r in results if r["category"] == category)
        for category in sorted({t.category for t in tasks})
    }
    summary = {
        "completed": len(results),
        "accepted": sum(r["status"] == "accepted" for r in results),
        "by_class": by_class,
        "thresholds_met": len(results) == 120
        and sum(by_class.values()) >= 108
        and all(n >= 24 for n in by_class.values()),
        "false_acceptance_review": "pending independent retained-candidate review",
        "scope": "bounded Python atoms; no large-build feasibility claim",
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "completed": len(results),
                "accepted": sum(r["status"] == "accepted" for r in results),
                "evidence": str(args.output),
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
