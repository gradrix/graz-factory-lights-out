#!/usr/bin/env python3
"""GFLO serving dependency launcher. Python 3.10+, standard library only."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


class Failure(Exception):
    pass


class NotReady(Failure):
    pass


def require(ok, message):
    if not ok:
        raise Failure(message)


def load(path):
    c = json.loads(Path(path).read_text())
    require(isinstance(c, dict), "Configuration must be an object")
    allowed = {"mode", "base_url", "model", "allow_remote", "api_key_env",
               "request_timeout", "startup_timeout", "managed"}
    require(not set(c) - allowed, "Unknown configuration fields")
    require(c.get("mode") in ("managed", "external"), "mode must be managed or external")
    u = urllib.parse.urlsplit(c.get("base_url", ""))
    require(u.scheme in ("http", "https") and u.hostname and not u.username
            and not u.password and not u.query and not u.fragment, "Invalid base_url")
    require(u.path.rstrip("/").endswith("/v1"), "base_url must end in /v1")
    local = u.hostname in ("localhost", "127.0.0.1", "::1")
    require(local or c.get("allow_remote") is True, "Non-loopback endpoint requires allow_remote=true")
    require(local or u.scheme == "https", "Remote endpoints require HTTPS; use an SSH tunnel for private HTTP servers")
    require(isinstance(c.get("model"), str) and c["model"].strip(), "model is required")
    for field, default in (("request_timeout", 15), ("startup_timeout", 1800)):
        value = c.setdefault(field, default)
        require(type(value) in (int, float) and 0 < value <= 86400, field + " must be in (0, 86400]")
    for env in (c.get("api_key_env", ""),):
        require(isinstance(env, str) and (not env or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env)), "Invalid key environment name")
    c["base_url"] = c["base_url"].rstrip("/")
    if c["mode"] == "external":
        require("managed" not in c, "External mode must not contain managed settings")
        return c
    require(u.scheme == "http" and u.hostname == "127.0.0.1" and u.path == "/v1"
            and u.port is not None, "Managed endpoint must be http://127.0.0.1:PORT/v1")
    require(not c.get("api_key_env"), "Managed mode currently uses loopback binding, not API authentication")
    m = c.get("managed", {})
    require(isinstance(m, dict), "managed must be an object")
    require(not set(m) - {"image", "model_path", "revision", "name", "gpu", "context_length",
                         "memory_fraction", "shm_size", "hf_token_env", "server_options"}, "Unknown managed fields")
    m["image"] = os.environ.get("GFLO_SERVING_IMAGE", m.get("image", ""))
    require(re.fullmatch(r"[^\s]+@sha256:[a-f0-9]{64}", m["image"]), "Set managed.image or GFLO_SERVING_IMAGE to a verified SGLang image@sha256:digest")
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", m.get("model_path", "")), "model_path must be a Hub repository ID")
    require(re.fullmatch(r"[a-f0-9]{40}", m.get("revision", "")), "revision must be a full checkpoint commit hash")
    require(re.fullmatch(r"gflo-[a-z0-9-]+", m.get("name", "")), "Container name must start with gflo-")
    require(re.fullmatch(r"[0-9]+", str(m.get("gpu", ""))), "gpu must identify one NVIDIA GPU index")
    require(type(m.get("context_length")) is int and m["context_length"] > 0, "context_length must be positive")
    require(type(m.get("memory_fraction")) in (float, int) and 0 < m["memory_fraction"] < 1, "memory_fraction must be between 0 and 1")
    require(re.fullmatch(r"[1-9][0-9]*[mg]", m.get("shm_size", "")), "shm_size must use m or g")
    env = m.get("hf_token_env", "")
    require(isinstance(env, str) and (not env or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env)), "Invalid Hub token environment name")
    opts = m.get("server_options", {})
    require(isinstance(opts, dict) and not set(opts) - {"quantization", "kv-cache-dtype", "attention-backend", "reasoning-parser", "tool-call-parser"}, "Unsupported server_options")
    require(all(isinstance(v, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", v) for v in opts.values()), "Invalid server option value")
    return c


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(c, suffix, payload=None):
    headers = {"Accept": "application/json"}
    env = c.get("api_key_env")
    if env:
        require(bool(os.environ.get(env)), "Configured API key environment variable is unset")
        headers["Authorization"] = "Bearer " + os.environ[env]
    body = None if payload is None else json.dumps(payload).encode()
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(c["base_url"] + suffix, data=body, headers=headers)
    # No ambient proxies or redirects: credentials must stay at the configured origin.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=c["request_timeout"]) as response:
            data = response.read(1024 * 1024 + 1)
    except urllib.error.HTTPError as exc:
        error = NotReady if exc.code in (429, 502, 503, 504) else Failure
        code = exc.code
        exc.close()
        raise error("Endpoint returned HTTP " + str(code)) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise NotReady("Endpoint unreachable or request timed out") from None
    require(len(data) <= 1024 * 1024, "Endpoint response too large")
    try:
        return json.loads(data)
    except (ValueError, UnicodeError):
        raise Failure("Endpoint returned invalid JSON") from None


def ready(c):
    data = request(c, "/models")
    require(isinstance(data, dict) and isinstance(data.get("data"), list), "Malformed model-list response")
    require(any(isinstance(m, dict) and m.get("id") == c["model"] for m in data["data"]), "Configured model not advertised by endpoint")
    return {"ready": True, "model": c["model"], "generation_tested": False}


def wait_ready(c):
    deadline = time.monotonic() + c["startup_timeout"]
    while True:
        remaining = deadline - time.monotonic()
        require(remaining > 0, "Startup deadline exceeded; inspect service logs")
        try:
            return ready({**c, "request_timeout": min(c["request_timeout"], remaining)})
        except NotReady:
            if c["mode"] == "managed":
                container = inspect(c)
                require(container is not None and container["State"]["Running"], "Managed server stopped during startup; inspect its logs")
            time.sleep(min(2, max(0, deadline - time.monotonic())))


def smoke(c, structured=False):
    ready(c)
    payload = {"model": c["model"], "messages": [{"role": "user", "content": 'Return only {"ok":true}.'}],
               "max_tokens": 256, "temperature": 0, "stream": False}
    if structured:
        payload["response_format"] = {"type": "json_schema", "json_schema": {"name": "probe", "strict": True,
            "schema": {"type": "object", "properties": {"ok": {"type": "boolean", "enum": [True]}}, "required": ["ok"], "additionalProperties": False}}}
    data = request(c, "/chat/completions", payload)
    try:
        choice = data["choices"][0]
        require(choice["finish_reason"] == "stop", "Smoke response did not finish normally")
        content = json.loads(choice["message"]["content"])
        require(isinstance(content, dict) and set(content) == {"ok"} and content["ok"] is True,
                "Smoke response did not satisfy the requested content")
    except (KeyError, IndexError, TypeError, ValueError):
        raise Failure("Malformed or nonconforming smoke response") from None
    return {"smoke_passed": True, "structured_requested": structured, "model": c["model"],
            "note": "Synthetic probe only; not a coding or full schema-support benchmark"}


def docker(*args, env=None, timeout=60):
    try:
        # Reject remote daemon contexts: localhost HTTP checks and host GPU probes
        # must refer to the same machine as container lifecycle operations.
        host = os.environ.get("DOCKER_HOST") if not os.environ.get("DOCKER_CONTEXT") else None
        if not host:
            context = subprocess.run(["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
                                     text=True, capture_output=True, timeout=15)
            require(context.returncode == 0, "Cannot determine active Docker context")
            host = context.stdout.strip()
        require(host.startswith("unix:///"), "Managed mode requires a local Unix-socket Docker daemon")
        result = subprocess.run(["docker", *args], text=True, capture_output=True, timeout=timeout, env=env)
    except (OSError, subprocess.TimeoutExpired):
        raise Failure("Docker unavailable or command timed out") from None
    require(result.returncode == 0, "Docker command failed: " + args[0] + " (inspect Docker separately; output withheld to protect secrets)")
    return result.stdout.strip()


def inspect(c):
    name = c["managed"]["name"]
    # Successful listing distinguishes absence from daemon/permission failures.
    ids = docker("ps", "-aq", "--filter", "name=^/" + name + "$")
    if not ids:
        return None
    data = json.loads(docker("inspect", ids))[0]
    require((data.get("Config", {}).get("Labels") or {}).get("org.gflo.serving") == name,
            "Container name belongs to an unmanaged service; refusing to touch it")
    return data


def fingerprint(c):
    return hashlib.sha256(json.dumps({"managed": c["managed"], "model": c["model"], "url": c["base_url"]}, sort_keys=True).encode()).hexdigest()


def doctor(c):
    if c["mode"] == "external":
        return ready(c)
    docker("info", "--format", "{{.ServerVersion}}")
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=index,name,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        raise Failure("nvidia-smi unavailable; provision NVIDIA driver/toolkit separately") from None
    require(result.returncode == 0, "NVIDIA driver probe failed")
    require(any(row.split(",")[0].strip() == str(c["managed"]["gpu"]) for row in result.stdout.splitlines()), "Configured GPU index not present")
    return {"host_prerequisites": "visible", "gpu_inventory": result.stdout.strip(),
            "note": "Does not prove container GPU access, model fit, or enforced host resource controls"}


def up(c):
    if c["mode"] == "external":
        return wait_ready(c)
    m = c["managed"]
    existing = inspect(c)
    spec = fingerprint(c)
    if existing:
        match = existing["Config"]["Labels"].get("org.gflo.spec") == spec
        if existing["State"]["Running"]:
            require(match, "Running configuration differs. Drain requests and explicitly down before changing it")
            return wait_ready(c)
        if match:
            doctor(c)
            docker("start", existing["Id"])
            return wait_ready(c)
    doctor(c)
    child_env = os.environ.copy()
    token_env = m.get("hf_token_env")
    if token_env:
        require(bool(child_env.get(token_env)), "Configured Hub token variable is unset")
        child_env["HF_TOKEN"] = child_env[token_env]
    # Pull the exact digest before replacing a stopped, owned container.
    docker("pull", m["image"], timeout=c["startup_timeout"])
    if existing:
        docker("rm", existing["Id"])
    args = ["run", "-d", "--name", m["name"], "--label", "org.gflo.serving=" + m["name"],
            "--label", "org.gflo.spec=" + spec, "--gpus", "device=" + str(m["gpu"]),
            "--restart", "unless-stopped", "--security-opt", "no-new-privileges:true",
            "--cap-drop", "ALL", "--shm-size", m["shm_size"], "--log-opt", "max-size=10m", "--log-opt", "max-file=3",
            "-p", "127.0.0.1:" + str(urllib.parse.urlsplit(c["base_url"]).port) + ":30000",
            "--mount", "type=volume,source=" + m["name"] + "-models,target=/root/.cache/huggingface"]
    if token_env:
        args += ["-e", "HF_TOKEN"]
    args += ["--entrypoint", "python3", m["image"], "-m", "sglang.launch_server", "--model-path", m["model_path"],
             "--revision", m["revision"], "--served-model-name", c["model"], "--host", "0.0.0.0", "--port", "30000",
             "--context-length", str(m["context_length"]), "--mem-fraction-static", str(m["memory_fraction"]),
             "--max-running-requests", "1", "--cuda-graph-max-bs", "1"]
    for key, value in sorted(m.get("server_options", {}).items()):
        args += ["--" + key, value]
    docker(*args, env=child_env)
    return wait_ready(c)


@contextlib.contextmanager
def lock(c):
    path = Path.home() / ".cache" / "gflo-serving"
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (path / (c["managed"]["name"] + ".lock")).open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Failure("Another launcher operation is active for this service") from None
        yield


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["config", "doctor", "up", "status", "smoke-test", "down"])
    parser.add_argument("--config", default="infra/serving/external.example.json")
    parser.add_argument("--structured", action="store_true", help="Request JSON-schema output in the synthetic smoke test")
    args = parser.parse_args(argv)
    try:
        c = load(args.config)
        if args.command == "config":
            output = c
        elif args.command == "doctor":
            output = doctor(c)
        elif args.command == "smoke-test":
            output = smoke(c, args.structured)
        elif args.command == "status":
            container = inspect(c) if c["mode"] == "managed" else None
            output = {"container": container["State"] if container else None, **ready(c)}
        elif args.command == "down":
            require(c["mode"] == "managed", "External mode never stops or modifies its server")
            with lock(c):
                existing = inspect(c)
                if existing and existing["State"]["Running"]:
                    docker("stop", "--time", "30", existing["Id"])
                output = {"stopped": True, "cache_preserved": True}
        else:
            with lock(c) if c["mode"] == "managed" else contextlib.nullcontext():
                output = up(c)
        print(json.dumps(output, indent=2))
        return 0
    except (Failure, OSError, ValueError, TypeError) as exc:
        # Never echo provider bodies, tokens, subprocess output, or malformed configuration values.
        print("error: " + (str(exc) if isinstance(exc, Failure) else "Invalid configuration or local I/O failure"), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
