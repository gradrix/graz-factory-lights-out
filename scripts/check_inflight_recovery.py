#!/usr/bin/env python3
"""Deliberately kill the owned vLLM engine during a live coding request, then resume."""

import argparse
import dataclasses
import hashlib
import http.client
import json
import threading
import time
import urllib.request
from pathlib import Path
from unittest.mock import patch

import serve
from check_serving_recovery import ENGINE_KILL

from gflo.broker import DockerBroker
from gflo.controller import Controller, prepare_run
from gflo.ledger import WorkLedger
from gflo.model import LocalModel
from gflo.pilot import IMAGE, fixtures, make_plan
from gflo.reporting import cost_report
from gflo.worker import ReadFileRequest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--window", choices=("active", "lookup", "tokenize", "between_turns"), default="active"
    )
    args = parser.parse_args()
    config = serve.load(args.config)
    serve.require(
        config["mode"] == "managed" and config["managed"]["backend"] == "vllm",
        "Owned managed vLLM required",
    )
    args.output.mkdir(parents=True, exist_ok=False)

    def save(name, value):
        (args.output / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n")

    plan = make_plan(
        fixtures()[6 if args.window == "between_turns" else 10],
        args.config.read_text(),
        Path("examples/work-atom.json"),
    )
    save(
        "manifest",
        {
            "plan": plan.model_dump(mode="json"),
            "fault": "SIGKILL internal EngineCore",
            "window": args.window,
            "injection_deadline_seconds": 30,
            "recovery_deadline_seconds": 300,
            "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    )
    (args.output / "harness.py").write_bytes(Path(__file__).read_bytes())
    injected = threading.Event()
    stop = threading.Event()
    injection_errors = []
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    with serve.lock(config):
        serve.up(config)  # Enforces ownership and configuration identity before faults.
        before = serve.inspect(config)
        save("before", before)

        def inject():
            try:
                deadline = time.monotonic() + 30
                while not stop.is_set() and time.monotonic() < deadline:
                    with opener.open(config["base_url"][:-3] + "/metrics", timeout=2) as response:
                        metrics = response.read().decode()
                    running = sum(
                        float(line.split()[-1])
                        for line in metrics.splitlines()
                        if line.startswith("vllm:num_requests_running{")
                    )
                    if running > 0:
                        (args.output / "active-metrics.txt").write_text(metrics)
                        victim = serve.docker("exec", before["Id"], "python3", "-c", ENGINE_KILL)
                        save("injection", {"running_requests": running, "pid": int(victim)})
                        injected.set()
                        return
                    stop.wait(0.05)
                raise RuntimeError("No active model request observed within injection window")
            except Exception as exc:
                injection_errors.append(str(exc))

        def boundary_death():
            victim = serve.docker("exec", before["Id"], "python3", "-c", ENGINE_KILL)
            save("injection", {"pid": int(victim), "window": args.window})
            injected.set()
            # Let engine death propagate to the API process, without starting it manually.
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    serve.ready(config)
                except serve.Failure:
                    return
                time.sleep(0.1)
            raise RuntimeError("No API outage observed after engine kill")

        class InterruptedModel(LocalModel):
            completed_read = False

            def turn(self, *args, **kwargs):
                result = super().turn(*args, **kwargs)
                if isinstance(result.result, ReadFileRequest):
                    self.completed_read = True
                return result

            def _request(self, path, payload, deadline, exchanges):
                if args.window != "active":
                    if not injected.is_set():
                        if (args.window == "lookup" and path == "/v1/models") or (
                            args.window == "between_turns"
                            and self.completed_read
                            and path == "/v1/models"
                        ):
                            boundary_death()
                        elif args.window == "tokenize" and path == "/tokenize":
                            request = http.client.HTTPConnection.request

                            def sent(connection, method, url, *positional, **named):
                                result = request(connection, method, url, *positional, **named)
                                if (
                                    method == "POST"
                                    and url == "/tokenize"
                                    and not injected.is_set()
                                ):
                                    boundary_death()
                                return result

                            with patch.object(http.client.HTTPConnection, "request", sent):
                                return super()._request(path, payload, deadline, exchanges)
                    return super()._request(path, payload, deadline, exchanges)

                if path != "/v1/chat/completions":
                    return super()._request(path, payload, deadline, exchanges)
                thread = threading.Thread(target=inject)
                thread.start()
                try:
                    return super()._request(path, payload, deadline, exchanges)
                finally:
                    stop.set()
                    thread.join(timeout=65)
                    if thread.is_alive():
                        raise RuntimeError("Fault injector did not terminate")

        try:
            with WorkLedger(args.output / "ledger.db") as ledger:
                prepare_run(ledger, plan)
                broken = Controller(
                    ledger,
                    InterruptedModel(ledger.artifacts, plan.model_profile),
                    DockerBroker(ledger.artifacts, IMAGE),
                ).run(plan.atom.atom_id)
                save("interrupted", broken)
                save("interrupted-cost", cost_report(ledger, plan.atom.atom_id))
                serve.require(
                    injected.is_set() and not injection_errors,
                    "Injection failed: " + repr(injection_errors),
                )
                serve.require(
                    broken["status"] == "retry-ready", "Expected a retained retryable failure"
                )
                serve.require(len(broken["attempts"]) == 1, "Unexpected retry before recovery")
                serve.require(
                    broken["candidate_digest"] is None, "Candidate published after interruption"
                )
                started = time.monotonic()
                while time.monotonic() - started < 300:
                    current = serve.inspect(config)
                    if current["RestartCount"] > before["RestartCount"]:
                        try:
                            serve.ready(config)
                        except serve.Failure:
                            pass
                        else:
                            break
                    time.sleep(2)
                else:
                    raise RuntimeError("Automatic service recovery deadline exceeded")
                serve.require(current["Id"] == before["Id"], "Container replaced unexpectedly")
                save(
                    "recovered-service",
                    {"seconds": time.monotonic() - started, "container": current},
                )
                controller = Controller(
                    ledger,
                    LocalModel(ledger.artifacts, plan.model_profile),
                    DockerBroker(ledger.artifacts, IMAGE),
                )
                result = controller.run(plan.atom.atom_id)
                save("resumed", result)
                save("resumed-cost", cost_report(ledger, plan.atom.atom_id))
                serve.require(result["status"] == "accepted", "Resumed task did not accept")
                serve.require(
                    result["attempts"][0] == broken["attempts"][0], "Failed history changed"
                )
                repeated = controller.run(plan.atom.atom_id)
                serve.require(repeated == result, "Repeated resume changed accepted history")
                audit = ledger.audit_artifacts()
                save("audit", dataclasses.asdict(audit))
                serve.require(not audit.missing and not audit.corrupt, "Evidence audit failed")
                save(
                    "result",
                    {
                        "passed": True,
                        "attempts": len(result["attempts"]),
                        "automatic_service_recovery": True,
                        "resume": "harness-triggered after readiness; no candidate repair",
                    },
                )
        except Exception as exc:
            save("failure", {"type": type(exc).__name__, "message": str(exc)})
            raise
        finally:
            stop.set()
            save("final-ready", serve.up(config))
    print("In-flight server death, recovery, task resume and idempotence passed", flush=True)


if __name__ == "__main__":
    main()
