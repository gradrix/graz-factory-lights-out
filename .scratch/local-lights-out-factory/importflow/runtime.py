"""Separate versioned runtime audit: fixed resources, no host mounts, exact candidate."""

import argparse
import json
import subprocess
import time
import uuid
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import SourceBundle
from gflo.ledger import WorkLedger

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/importflow-v1")
IMAGE = (HERE / "provision/image-id.txt").read_text().strip()
BOOTSTRAP = """import json,os,sys
from pathlib import Path
assert os.getuid()==65534
assert Path('/sys/fs/cgroup/memory.max').read_text().strip()=='536870912'
assert Path('/sys/fs/cgroup/pids.max').read_text().strip()=='32'
data=json.loads(sys.stdin.buffer.readline())
os.chdir('/workspace')
for name,text in data['files'].items():
    path=Path(name);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
sys.path.insert(0,'/workspace')
exec(compile(data['check'],'<runtime-check>','exec'),{'__name__':'__main__'})
"""


def main(trial, fixed=False, system=False):
    global ROOT, IMAGE
    if fixed:
        ROOT = Path(".gflo/evidence/importflow-prepared-v1")
        IMAGE = (HERE / "provision-sqlite/image-id.txt").read_text().strip()
    if system:
        ROOT = Path(".gflo/evidence/importflow-resume-v1")
        IMAGE = (HERE / "provision-sqlite-system/image-id.txt").read_text().strip()
    prefix = (
        "importflow-runtime-system-v1-"
        if system
        else "importflow-runtime-fixed-v1-"
        if fixed
        else "importflow-runtime-v1-"
    )
    out = Path(".gflo/evidence") / (prefix + trial)
    out.mkdir(parents=True, exist_ok=False)
    artifacts = ArtifactStore(out / "artifacts")
    if trial == "reference":
        paths = (
            "blobs.py",
            "tabular.py",
            "jobs.py",
            "worker.py",
            "api.py",
            "pyproject.toml",
            "README.md",
            "tests/test_importflow.py",
        )
        bundle = SourceBundle(files={p: (HERE / "reference" / p).read_text() for p in paths})
        candidate = artifacts.publish(bundle.canonical().encode())
    else:
        result = json.loads((ROOT / trial / "build/result.json").read_text())
        assert result["status"] == "accepted"
        with WorkLedger(ROOT / trial / "ledger.db") as ledger:
            state = ledger.status(result["feature_result"]["integration_atom"])
            assert not state.get("acceptance_challenged")
            candidate = state["candidate_digest"]
            raw = ledger.artifacts.read(candidate)
            artifacts.publish(raw)
            bundle = SourceBundle.model_validate_json(raw)
    payload = (
        json.dumps(dict(files=bundle.files, check=(HERE / "runtime_check.py").read_text())).encode()
        + b"\n"
    )
    name = "gflo-importflow-audit-" + uuid.uuid4().hex[:12]
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--read-only",
        "--network",
        "none",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--user",
        "65534:65534",
        "--memory",
        "512m",
        "--memory-swap",
        "512m",
        "--pids-limit",
        "32",
        "--cpus",
        "2",
        "--tmpfs",
        "/workspace:rw,nosuid,nodev,noexec,size=16m,uid=65534,gid=65534,mode=0700",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,noexec,size=256m,uid=65534,gid=65534,mode=0700",
        "-i",
        "--entrypoint",
        "python",
        IMAGE,
        "-I",
        "-c",
        BOOTSTRAP,
    ]
    manifest = dict(
        kind="importflow-runtime-audit-v1",
        trial=trial,
        candidate_digest=candidate,
        image=IMAGE,
        command=command,
        payload_digest=artifacts.publish(payload),
        memory_bytes=536870912,
        tmp_bytes=268435456,
        cpus=2,
        pids=32,
    )
    started = time.monotonic()
    try:
        result = subprocess.run(command, input=payload, capture_output=True, timeout=180)
        raw = dict(
            exit_code=result.returncode,
            stdout=result.stdout.decode(errors="replace"),
            stderr=result.stderr.decode(errors="replace"),
            elapsed_seconds=time.monotonic() - started,
        )
        (out / "result.json").write_text(json.dumps(raw, indent=2) + "\n")
        receipt = artifacts.publish(json.dumps(raw, sort_keys=True).encode())
        summary = dict(**manifest, evidence_digest=receipt, exit_code=result.returncode)
        if result.returncode == 0:
            summary["measurements"] = json.loads(raw["stdout"])
        (
            HERE
            / (
                ("runtime-system-" if system else "runtime-fixed-" if fixed else "runtime-")
                + trial
                + ".json"
            )
        ).write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary.get("measurements", raw), indent=2), flush=True)
        assert result.returncode == 0, "runtime audit failed; retained raw output"
    finally:
        subprocess.run(
            ["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial")
    parser.add_argument("--fixed", action="store_true")
    parser.add_argument("--system", action="store_true")
    args = parser.parse_args()
    main(args.trial, args.fixed, args.system)
