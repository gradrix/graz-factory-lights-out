#!/usr/bin/env python3
"""Read back the original container and API without exporting credentials."""
import datetime
import json
import pathlib
import subprocess
import time
import urllib.request

root = pathlib.Path.home() / "benchmark-5090"
original = json.loads((root / "original-container.private.json").read_text())
current = json.loads(subprocess.check_output(["docker", "inspect", "local-vllm"]))[0]
checks = {
    "same_container": current["Id"] == original["Id"],
    "same_image": current["Image"] == original["Image"],
    "same_command": current["Config"]["Cmd"] == original["Config"]["Cmd"],
    "same_environment": current["Config"]["Env"] == original["Config"]["Env"],
    "same_mounts": current["Mounts"] == original["Mounts"],
    "same_port_bindings": current["HostConfig"]["PortBindings"] == original["HostConfig"]["PortBindings"],
    "running": current["State"]["Running"],
    "temporary_container_absent": subprocess.run(
        ["docker", "inspect", "benchmark-5090-server"], capture_output=True
    ).returncode != 0,
}
env = dict(x.split("=", 1) for x in current["Config"]["Env"] if "=" in x)
headers = {"Authorization": "Bearer " + env.get("VLLM_API_KEY", ""), "Content-Type": "application/json"}
base = "http://127.0.0.1:8000"
models = None
for _ in range(180):
    try:
        with urllib.request.urlopen(urllib.request.Request(base + "/v1/models", headers=headers), timeout=5) as response:
            models = json.load(response)
        break
    except Exception:
        time.sleep(2)
checks["api_ready"] = models is not None
revision_check = subprocess.run(
    ["docker", "exec", "local-vllm", "cat",
     "/root/.cache/huggingface/hub/models--Inferact--Qwen3.8-27B-NVFP4/refs/main"],
    capture_output=True, text=True,
)
cached_revision = revision_check.stdout.strip() if revision_check.returncode == 0 else None
checks["same_cached_model_revision"] = cached_revision == "6128240ebaf4eaa7bad2b3d1c72c37d677c5f462"
answer = None
if models:
    model = models["data"][0]["id"]
    body = {"model": model, "messages": [{"role": "user", "content": "Return only the result of 17 + 25."}],
            "temperature": 0, "max_tokens": 32, "chat_template_kwargs": {"enable_thinking": False}}
    with urllib.request.urlopen(urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(body).encode(), headers=headers), timeout=120) as response:
        answer = json.load(response)
    checks["generation_passed"] = answer["choices"][0]["message"]["content"].strip() == "42"
report = {"date": datetime.datetime.now(datetime.timezone.utc).isoformat(), "checks": checks,
          "cached_model_revision": cached_revision,
          "models": models, "synthetic_generation": answer,
          "gpu": subprocess.check_output(["/usr/lib/wsl/lib/nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv"], text=True)}
(root / "restoration-check.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(checks))
raise SystemExit(0 if all(checks.values()) else 1)
