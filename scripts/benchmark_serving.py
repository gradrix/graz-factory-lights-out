#!/usr/bin/env python3
"""Synthetic serial serving probes; no generated code or tool calls are executed."""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import threading
import time
from urllib.parse import urlsplit

import serve


def workloads(context_tier):
    schema = {
        "type": "object", "properties": {"ok": {"type": "boolean"}, "value": {"type": "integer"}},
        "required": ["ok", "value"], "additionalProperties": False,
    }
    structured = {"response_format": {"type": "json_schema", "json_schema": {
        "name": "probe", "strict": True, "schema": schema,
    }}}
    return [
        ("plain", "Reply with exactly OK and nothing else.", {}),
        ("json", 'Return exactly this JSON object: {"ok":true,"value":7}', structured),
        ("tool", "Call read_file for the path src/provider.py. Do not answer in prose.", {
            "tools": [{"type": "function", "function": {
                "name": "read_file", "description": "Read a source file", "parameters": {
                    "type": "object", "properties": {"path": {"type": "string"}},
                    "required": ["path"], "additionalProperties": False,
                },
            }}], "tool_choice": "auto",
        }),
        ("long_json", "Synthetic padding follows:\n" + "padding " * (context_tier - 2048)
         + '\nEnd padding. Return exactly this JSON object: {"ok":true,"value":7}', structured),
    ]


def validate(kind, response, context_tier):
    try:
        if len(response["choices"]) != 1:
            return False
        choice = response["choices"][0]
        message = choice["message"]
        usage = response["usage"]
        if any(type(usage.get(key)) is not int or usage[key] <= 0
               for key in ("prompt_tokens", "completion_tokens", "total_tokens")):
            return False
        if usage["total_tokens"] != usage["prompt_tokens"] + usage["completion_tokens"]:
            return False
        expected_finish = "tool_calls" if kind == "tool" else "stop"
        if usage["total_tokens"] > context_tier or choice["finish_reason"] != expected_finish:
            return False
        if kind == "long_json" and usage["prompt_tokens"] < context_tier - 2300:
            return False
        if kind == "tool":
            calls = message["tool_calls"]
            return (len(calls) == 1 and calls[0]["function"]["name"] == "read_file"
                    and json.loads(calls[0]["function"]["arguments"]) == {"path": "src/provider.py"})
        if kind == "plain":
            return message["content"].strip() == "OK"
        value = json.loads(message["content"])
        return (isinstance(value, dict) and set(value) == {"ok", "value"}
                and value["ok"] is True and type(value["value"]) is int and value["value"] == 7)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return False


def memory_samples(stop, samples):
    while not stop.is_set():
        try:
            result = subprocess.run([
                "nvidia-smi", "--id=0", "--query-gpu=memory.used", "--format=csv,noheader,nounits",
            ], capture_output=True, text=True, check=True, timeout=5)
            samples.append({"timestamp": time.time(), "used_mib": int(result.stdout.strip())})
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            samples.append({"timestamp": time.time(), "error": str(exc)})
        stop.wait(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--context-tier", type=int, choices=(8192, 16384), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, choices=range(1, 11), default=3)
    args = parser.parse_args()
    config = serve.load(args.config)
    if config["mode"] != "external" or urlsplit(config["base_url"]).hostname != "127.0.0.1":
        raise ValueError("Benchmark requires an explicit loopback external endpoint")
    args.output.mkdir(parents=True, exist_ok=False)
    summary = {
        "schema_version": 1, "workload_version": "synthetic-serving-v1",
        "context_tier": args.context_tier, "repeats": args.repeats,
        "base_url": config["base_url"], "model": config["model"],
        "concurrency": 1, "thinking": False,
        "limitations": ["Synthetic serving probes, not coding qualification",
                        "VRAM samples include desktop/other GPU processes; one-second sampling"],
    }
    samples, results = [], []
    stop = threading.Event()
    monitor = threading.Thread(target=memory_samples, args=(stop, samples))
    monitor.start()
    try:
        summary["models"] = serve.request(config, "/models")
        cases = workloads(args.context_tier)
        # One explicit warm-up before scored requests; preserve its raw result too.
        for index, (kind, prompt, options) in enumerate([cases[0]] + cases * args.repeats):
            payload = {
                "model": config["model"], "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 128, "temperature": 0, "seed": 42,
                "chat_template_kwargs": {"enable_thinking": False}, **options,
            }
            record = {"kind": kind, "warmup": index == 0, "request": payload}
            start = time.perf_counter()
            try:
                response = serve.request(config, "/chat/completions", payload)
                record["response"] = response
                record["passed"] = validate(kind, response, args.context_tier)
            except serve.Failure as exc:
                record["error"] = str(exc)
                record["passed"] = False
            record["elapsed_seconds"] = time.perf_counter() - start
            (args.output / f"request-{index:02d}.json").write_text(json.dumps(record, indent=2))
            results.append(record)
            print(json.dumps({k: record[k] for k in ("kind", "warmup", "passed", "elapsed_seconds")}), flush=True)
    finally:
        stop.set()
        monitor.join(timeout=6)
        (args.output / "gpu-memory.json").write_text(json.dumps(samples, indent=2))
        measured = [r for r in results if not r["warmup"]]
        summary["passed"] = (len(measured) == 4 * args.repeats and all(r["passed"] for r in results))
        summary["peak_gpu_used_mib"] = max((s["used_mib"] for s in samples if "used_mib" in s), default=None)
        summary["median_seconds"] = {
            kind: statistics.median(r["elapsed_seconds"] for r in measured if r["kind"] == kind)
            for kind in {r["kind"] for r in measured}
        }
        summary["passed_requests"] = sum(r["passed"] for r in measured)
        summary["total_requests"] = len(measured)
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
