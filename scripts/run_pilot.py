#!/usr/bin/env python3
"""Freeze/preflight/run the twelve development tasks on the qualified local profile."""

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
from gflo.controller import Controller, prepare_run
from gflo.ledger import WorkLedger
from gflo.model import LocalModel
from gflo.pilot import IMAGE, fixtures, make_plan

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New evidence directory")
    parser.add_argument(
        "--config", type=Path, default=ROOT / "infra/serving/vllm-5090.example.json"
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
    manifest = {
        "schema_version": 1,
        "workload": "twelve-task-development-pilot-v1",
        "frozen_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "fixture_sha256": hashlib.sha256(
            json.dumps([dataclasses.asdict(f) for f in tasks], sort_keys=True).encode()
        ).hexdigest(),
        "fixtures": [dataclasses.asdict(f) for f in tasks],
        "plans": [p.model_dump(mode="json") for p in plans],
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
            "attempts_per_atom": 3,
            "model_turns_per_attempt": 3,
            "context_total": 8192,
            "output_reserve": 2048,
            "request_deadline_seconds": 120,
            "automatic_infrastructure_retry": False,
            "held_out": False,
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
        with WorkLedger(args.output / "ledger.db") as ledger:
            model = LocalModel(ledger.artifacts, plans[0].model_profile)
            broker = DockerBroker(ledger.artifacts, IMAGE)
            controller = Controller(ledger, model, broker)
            for fixture, plan in zip(tasks, plans, strict=True):
                prepare_run(ledger, plan)
                started = time.monotonic()
                error = None
                try:
                    state = controller.run(plan.atom.atom_id)
                except Exception as exc:
                    error = {"type": type(exc).__name__, "message": str(exc)}
                    state = ledger.status(plan.atom.atom_id)
                result = {
                    "task": fixture.name,
                    "category": fixture.category,
                    "elapsed_seconds": time.monotonic() - started,
                    "status": state["status"],
                    "attempts": len(state["attempts"]),
                    "error": error,
                    "state": state,
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
