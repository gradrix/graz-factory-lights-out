#!/usr/bin/env python3
"""Exercise stopped restart and internal vLLM engine death on an owned service.

Deliberately interrupts the configured service. Use a new evidence directory.
Holds launcher and local-worker endpoint locks throughout the experiment.
"""

import argparse
import copy
import fcntl
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import serve

ENGINE_KILL = """
import os, signal
from pathlib import Path
pids = []
for path in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        command = path.read_bytes().split(bytes([0]), 1)[0].strip()
    except FileNotFoundError:
        continue
    if command == b'VLLM::EngineCore':
        pids.append(int(path.parent.name))
if len(pids) != 1 or pids[0] <= 1:
    raise RuntimeError('Expected exactly one internal EngineCore process')
print(pids[0], flush=True)
os.kill(pids[0], signal.SIGKILL)
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = serve.load(args.config)
    serve.require(config["mode"] == "managed", "Managed service required")
    serve.require(config["managed"]["backend"] == "vllm", "vLLM required")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "harness.py").write_bytes(Path(__file__).read_bytes())

    def save(name, value):
        (args.output / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n")

    def snapshot():
        item = serve.inspect(config)
        serve.require(item is not None, "Owned container missing")
        return {
            key: item[key]
            for key in (
                "Id",
                "Image",
                "State",
                "RestartCount",
                "Mounts",
            )
        }

    def same_identity(before, after):
        for key in ("Id", "Image"):
            serve.require(before[key] == after[key], key + " changed")

        def mounts(item):
            return sorted(item["Mounts"], key=lambda mount: mount["Destination"])

        serve.require(mounts(before) == mounts(after), "Mounts changed")
        serve.require(not after["State"]["OOMKilled"], "Container OOM observed")

    lock_root = Path.home() / ".cache/gflo/model-locks"
    lock_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock_path = lock_root / hashlib.sha256(config["base_url"].encode()).hexdigest()
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with serve.lock(config):
            before = snapshot()
            save("config", config)
            save("before", before)
            serve.require(before["State"]["Running"], "Start the service before qualification")
            save("baseline-up", serve.up(config))  # Also refuses configuration drift.
            save("baseline-smoke", serve.smoke(config, structured=True))
            try:
                drift = copy.deepcopy(config)
                drift["managed"]["context_length"] += 1
                try:
                    serve.up(drift)
                except serve.Failure as exc:
                    serve.require("Running configuration differs" in str(exc), str(exc))
                    save("drift-refused", {"reason": str(exc)})
                else:
                    raise serve.Failure("Running configuration drift was accepted")
                started = time.monotonic()
                serve.docker("stop", before["Id"])
                save("stopped", snapshot())
                save("restart-up", serve.up(config))
                after = snapshot()
                save("restarted", after)
                same_identity(before, after)
                save("restart-smoke", serve.smoke(config, structured=True))
                save("restart-result", {"seconds": time.monotonic() - started})
                print("Stopped restart passed", flush=True)

                started = time.monotonic()
                victim = serve.docker("exec", before["Id"], "python3", "-c", ENGINE_KILL)
                save("injected-fault", {"internal_engine_pid": int(victim)})
                deadline = time.monotonic() + config["startup_timeout"]
                observations = []
                while time.monotonic() < deadline:
                    current = snapshot()
                    observations.append(current)
                    save("crash-observations", observations)
                    if current["RestartCount"] > after["RestartCount"]:
                        try:
                            serve.ready(config)
                        except serve.Failure:
                            pass
                        else:
                            break
                    time.sleep(2)
                else:
                    raise serve.Failure("Automatic crash recovery deadline exceeded")
                same_identity(before, current)
                save("crash-smoke", serve.smoke(config, structured=True))
                save(
                    "crash-result",
                    {"seconds": time.monotonic() - started, "automatic_restart": True},
                )
                print("Automatic engine-crash recovery passed", flush=True)
            except Exception as exc:
                save("failure", {"type": type(exc).__name__, "message": str(exc)})
                raise
            finally:
                # Recovery is cleanup, not evidence that automatic restart passed.
                save("final-up", serve.up(config))
                save("final", snapshot())
                (args.output / "server.log").write_text(
                    subprocess.run(
                        ["docker", "logs", "--tail", "1000", before["Id"]],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        check=True,
                        timeout=60,
                    ).stdout
                )
    finally:
        os.close(fd)
    save("result", {"passed": True, "scope": "idle serving lifecycle; no in-flight task"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
