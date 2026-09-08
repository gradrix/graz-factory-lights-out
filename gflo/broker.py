"""Narrow trusted broker for bounded Python process-contract experiments.

No host mounts, Docker socket, model access, secrets or evaluator expectations
enter candidate containers. Only trusted callers may choose commands and images.
"""

from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import os
import re
import selectors
import subprocess
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal

from pydantic import Field, model_validator

from gflo.artifacts import ArtifactStore
from gflo.records import Digest, Record

MAX_OUTPUT = 1_048_576
LABEL = "org.gflo.broker"


class BrokerError(RuntimeError):
    """Evaluator/infrastructure failure; never a passing candidate result."""


class SourceBundle(Record):
    files: dict[str, str]

    @model_validator(mode="after")
    def bounded_files(self) -> SourceBundle:
        if not 1 <= len(self.files) <= 100:
            raise ValueError("Bundle requires 1–100 text files")
        if len(self.canonical().encode()) > 262144:
            raise ValueError("Bundle exceeds 256 KiB")
        for name in self.files:
            if (
                len(name) > 200
                or not re.fullmatch(r"[A-Za-z0-9_./-]+", name)
                or name.startswith("/")
                or any(part in ("", ".", "..") for part in name.split("/"))
                or any(other.startswith(name + "/") for other in self.files)
            ):
                raise ValueError("Bundle requires unambiguous normalized relative paths")
        return self


class Execution(Record):
    candidate_digest: Digest
    image_id: str
    container_id: Annotated[str, Field(min_length=1, max_length=200)]
    command: tuple[str, ...]
    stdin: str
    purpose: Literal["candidate", "validation", "qualification"]
    outcome: Literal["completed", "timeout", "output-limit"]
    exit_code: int
    oom_killed: bool
    stdout_base64: str
    stderr_base64: str
    elapsed_seconds: Annotated[float, Field(ge=0, allow_inf_nan=False)]

    @property
    def stdout(self) -> bytes:
        return base64.b64decode(self.stdout_base64)


# Runs before any candidate import/execution. The complete payload is consumed
# before exec; candidate stdin contains only its explicit process input.
BOOTSTRAP = r"""
import json, os, sys
from pathlib import Path
try:
    lines = Path('/proc/self/status').read_text().splitlines()
    s = dict(line.split(':', 1) for line in lines if ':' in line)
    assert os.getuid() == 65534 and int(s['CapEff'], 16) == 0
    assert s['NoNewPrivs'].strip() == '1' and s['Seccomp'].strip() == '2'
    assert Path('/sys/fs/cgroup/memory.max').read_text().strip() == '134217728'
    assert Path('/sys/fs/cgroup/memory.swap.max').read_text().strip() == '0'
    assert Path('/sys/fs/cgroup/pids.max').read_text().strip() == '32'
    quota, period = map(int, Path('/sys/fs/cgroup/cpu.max').read_text().split())
    assert quota == period and period > 0
    assert sorted(p.name for p in Path('/sys/class/net').iterdir()) == ['lo']
    assert not Path('/var/run/docker.sock').exists()
    assert os.statvfs('/').f_flag & os.ST_RDONLY
    payload = json.load(sys.stdin)
    for name, content in payload['files'].items():
        path = Path('/workspace') / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    Path('/tmp/input').write_text(payload['stdin'])
    fd = os.open('/tmp/input', os.O_RDONLY)
    os.dup2(fd, 0)
    os.close(fd)
    os.chdir('/workspace')
    env = {'PATH':'/usr/local/bin:/usr/bin:/bin', 'HOME':'/tmp', 'LANG':'C.UTF-8'}
    os.execvpe(payload['command'][0], payload['command'], env)
except BaseException as e:
    print('GFLO bootstrap failed: ' + repr(e), file=sys.stderr)
    sys.exit(125)
"""


class DockerBroker:
    def __init__(self, artifacts: ArtifactStore, image: str):
        if not re.fullmatch(r"(?:[A-Za-z0-9_./:-]+@)?sha256:[a-f0-9]{64}", image):
            raise ValueError("Broker requires a pinned local image")
        self.artifacts = artifacts
        self.image = image
        self.owner = hashlib.sha256(str(artifacts.root.resolve()).encode()).hexdigest()
        self.image_id = ""
        self.qualification_digest: str | None = None
        # Resolve the active context once; subsequent calls explicitly pin the socket.
        endpoint = os.environ.get("DOCKER_HOST") if not os.environ.get("DOCKER_CONTEXT") else None
        if not endpoint:
            endpoint = subprocess.check_output(
                ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
                text=True,
                timeout=15,
            ).strip()
        if not endpoint.startswith("unix:///"):
            raise BrokerError("Broker requires a local Unix-socket Docker daemon")
        self.endpoint = endpoint

    def _docker(self, *args: str, timeout: float = 15) -> str:
        result = subprocess.run(
            ["docker", "--host", self.endpoint, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode:
            raise BrokerError(result.stderr.strip()[:4096] or "Docker command failed")
        return result.stdout.strip()

    @contextmanager
    def _lock(self) -> Iterator[None]:
        with (self.artifacts.root / ".broker.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def _remove(self, name: str) -> None:
        # A label is checked before every destructive operation, even after errors.
        ids = self._docker("ps", "-aq", "--filter", f"name=^/{name}$")
        if not ids:
            return
        info = json.loads(self._docker("inspect", name))[0]
        if info["Config"]["Labels"].get(LABEL) != self.owner:
            raise BrokerError("Refusing to remove an unowned container")
        self._docker("rm", "-f", name)

    def _reap(self) -> None:
        for name in self._docker(
            "ps", "-a", "--filter", f"label={LABEL}={self.owner}", "--format", "{{.Names}}"
        ).splitlines():
            self._remove(name)

    def reconcile(self) -> None:
        """Remove this store's interrupted containers while holding its exclusive lock."""
        with self._lock():
            self._reap()

    def _attach(self, name: str, payload: bytes, seconds: float) -> tuple[bytes, bytes, str]:
        process = subprocess.Popen(
            ["docker", "--host", self.endpoint, "start", "--attach", "--interactive", name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdin and process.stdout and process.stderr
        stdout, stderr = bytearray(), bytearray()
        outcome = "completed"
        deadline = time.monotonic() + seconds
        try:
            with selectors.DefaultSelector() as selector:
                for stream, mode in (
                    (process.stdin, selectors.EVENT_WRITE),
                    (process.stdout, selectors.EVENT_READ),
                    (process.stderr, selectors.EVENT_READ),
                ):
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, mode)
                offset = 0
                while selector.get_map():
                    if time.monotonic() >= deadline:
                        outcome = "timeout"
                        break
                    for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                        if key.fileobj is process.stdin:
                            try:
                                offset += os.write(key.fd, payload[offset : offset + 65536])
                            except BrokenPipeError:
                                offset = len(payload)
                            if offset == len(payload):
                                selector.unregister(process.stdin)
                                process.stdin.close()
                        else:
                            chunk = os.read(key.fd, 65536)
                            if not chunk:
                                selector.unregister(key.fileobj)
                                continue
                            target = stdout if key.fileobj is process.stdout else stderr
                            room = MAX_OUTPUT - len(stdout) - len(stderr)
                            target.extend(chunk[:room])
                            if len(chunk) > room:
                                outcome = "output-limit"
                                break
                    if outcome != "completed":
                        break
                if outcome == "completed":
                    try:
                        process.wait(timeout=max(0.01, deadline - time.monotonic()))
                    except subprocess.TimeoutExpired:
                        outcome = "timeout"
            if outcome != "completed":
                # Detach first: a full client output pipe can otherwise hold up
                # Docker's kill acknowledgement while the daemon drains logs.
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
                process.stdout.close()
                process.stderr.close()
                state = json.loads(self._docker("inspect", name))[0]["State"]
                if state["Running"]:
                    try:
                        self._docker("kill", name)
                    except BrokerError:
                        if json.loads(self._docker("inspect", name))[0]["State"]["Running"]:
                            raise
            return bytes(stdout), bytes(stderr), outcome
        except BaseException as exc:
            self.artifacts.publish(
                json.dumps(
                    {
                        "kind": "interrupted-capture",
                        "container_name": name,
                        "error_type": type(exc).__name__,
                        "stdout_base64": base64.b64encode(stdout).decode(),
                        "stderr_base64": base64.b64encode(stderr).decode(),
                    },
                    sort_keys=True,
                ).encode()
            )
            raise
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            process.stdin.close()
            process.stdout.close()
            process.stderr.close()

    def _execute(
        self,
        digest: str,
        command: tuple[str, ...],
        stdin: str,
        seconds: float,
        purpose: Literal["candidate", "validation", "qualification"],
    ) -> Execution:
        bundle = SourceBundle.model_validate_json(self.artifacts.read(digest))
        if (
            not command
            or len(command) > 64
            or any(not isinstance(arg, str) or "\x00" in arg or len(arg) > 65536 for arg in command)
        ):
            raise ValueError("Invalid process command")
        if not isinstance(stdin, str) or len(stdin.encode()) > 65536 or not 0 < seconds <= 60:
            raise ValueError("Execution requires bounded input and a 0–60 second deadline")
        name = "gflo-attempt-" + uuid.uuid4().hex
        started = time.monotonic()
        try:
            container_id = self._docker(
                "create",
                "--pull",
                "never",
                "--name",
                name,
                "--label",
                f"{LABEL}={self.owner}",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--memory",
                "128m",
                "--memory-swap",
                "128m",
                "--pids-limit",
                "32",
                "--cpus",
                "1",
                "--user",
                "65534:65534",
                "--log-driver",
                "none",
                "--restart",
                "no",
                "--tmpfs",
                "/workspace:rw,nosuid,nodev,noexec,size=16m,uid=65534,gid=65534,mode=0700",
                "--tmpfs",
                "/tmp:rw,nosuid,nodev,noexec,size=8m,uid=65534,gid=65534,mode=0700",
                "--interactive",
                "--entrypoint",
                "python",
                self.image_id,
                "-I",
                "-c",
                BOOTSTRAP,
            )
            info = json.loads(self._docker("inspect", name))[0]
            host = info["HostConfig"]
            if (
                info["Image"] != self.image_id
                or info["Mounts"]
                or host["Privileged"]
                or host["NetworkMode"] != "none"
                or not host["ReadonlyRootfs"]
                or host["Memory"] != 134217728
                or host["MemorySwap"] != 134217728
                or host["PidsLimit"] != 32
                or host["NanoCpus"] != 1000000000
                or host["CapDrop"] != ["ALL"]
                or info["Config"]["User"] != "65534:65534"
                or host.get("DeviceRequests")
                or host.get("Devices")
                or host.get("PidMode") not in ("", "private")
                or host.get("IpcMode") not in ("", "private")
                or host.get("UTSMode") not in ("", "private")
            ):
                raise BrokerError("Container controls differ from the required profile")
            stdout, stderr, outcome = self._attach(
                name,
                json.dumps(
                    {
                        "files": bundle.files,
                        "command": command,
                        "stdin": stdin,
                    }
                ).encode(),
                seconds,
            )
            state = json.loads(self._docker("inspect", name))[0]["State"]
            if state["Running"] or state["Error"] or state["ExitCode"] == 125:
                raise BrokerError(
                    "Container execution/bootstrap failed: "
                    + stderr[:4096].decode(errors="replace")
                )
            return Execution(
                candidate_digest=digest,
                image_id=self.image_id,
                container_id=container_id,
                command=command,
                stdin=stdin,
                purpose=purpose,
                outcome=outcome,  # type: ignore[arg-type]
                exit_code=state["ExitCode"],
                oom_killed=state["OOMKilled"],
                stdout_base64=base64.b64encode(stdout).decode(),
                stderr_base64=base64.b64encode(stderr).decode(),
                elapsed_seconds=time.monotonic() - started,
            )
        except BaseException as exc:
            self.artifacts.publish(
                json.dumps(
                    {
                        "kind": "execution-error",
                        "container_name": name,
                        "candidate_digest": digest,
                        "image_id": self.image_id,
                        "command": command,
                        "stdin": stdin,
                        "purpose": purpose,
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:4096],
                    },
                    sort_keys=True,
                ).encode()
            )
            raise
        finally:
            self._remove(name)

    def qualify(self) -> str:
        """Exercise actual bounded memory/PID enforcement before executing candidates."""
        self.qualification_digest = None
        with self._lock():
            self._reap()
            info = json.loads(self._docker("info", "--format", "{{json .}}"))
            if info.get("CgroupVersion") != "2" or not any(
                "seccomp" in value for value in info.get("SecurityOptions", [])
            ):
                raise BrokerError("Cgroup v2 and seccomp are required")
            image = json.loads(self._docker("image", "inspect", self.image))[0]
            if image["Config"].get("Volumes"):
                raise BrokerError("Image-declared volumes are forbidden")
            self.image_id = image["Id"]
            digest = self.artifacts.publish(
                SourceBundle(files={"placeholder": ""}).canonical().encode()
            )
            controls = self._execute(
                digest, ("python", "-I", "-c", "print('controls-ok')"), "", 15, "qualification"
            )
            memory = self._execute(
                digest,
                ("python", "-I", "-c", "a=bytearray(256*1024*1024)"),
                "",
                15,
                "qualification",
            )
            pid_code = """
import errno, subprocess
children=[]
try:
    for i in range(40):
        children.append(subprocess.Popen(['sleep','5']))
except OSError as error:
    if error.errno == errno.EAGAIN:
        print('pids-enforced')
finally:
    for child in children: child.terminate()
    for child in children: child.wait()
"""
            pids = self._execute(digest, ("python", "-I", "-c", pid_code), "", 15, "qualification")
            report = {
                "image_id": self.image_id,
                "docker": info["ServerVersion"],
                "executions": [r.model_dump(mode="json") for r in (controls, memory, pids)],
            }
            report_digest = self.artifacts.publish(json.dumps(report, sort_keys=True).encode())
            if not (
                controls.exit_code == 0
                and controls.stdout == b"controls-ok\n"
                and memory.oom_killed
                and memory.exit_code == 137
                and pids.exit_code == 0
                and pids.stdout == b"pids-enforced\n"
                and all(r.outcome == "completed" for r in (controls, memory, pids))
            ):
                raise BrokerError("Resource enforcement qualification failed: " + report_digest)
            self.qualification_digest = report_digest
            return report_digest

    def execute(
        self,
        digest: str,
        command: tuple[str, ...],
        *,
        stdin: str = "",
        seconds: float = 10,
        purpose: Literal["candidate", "validation"] = "candidate",
    ) -> Execution:
        if self.qualification_digest is None:
            raise BrokerError("Run target qualification before candidate execution")
        with self._lock():
            self._reap()
            result = self._execute(digest, command, stdin, seconds, purpose)
            self.artifacts.publish(result.canonical().encode())
            return result
