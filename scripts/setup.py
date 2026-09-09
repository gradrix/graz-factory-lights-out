#!/usr/bin/env python3
"""Install GFLO in a virtual environment, prepare a demo, and report local readiness."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROKER = "python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca"


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=ROOT, check=True, text=True, capture_output=capture, timeout=600
    )


def readiness(python: Path) -> dict[str, object]:
    report: dict[str, object] = {
        "python_supported": sys.version_info >= (3, 11),
        "environment": str(python.parent.parent),
        "gflo_installed": False,
        "docker_daemon": False,
        "gpu_execution_ready": "not checked",
    }
    if python.is_file():
        try:
            run(
                [
                    str(python),
                    "-c",
                    "import gflo, pydantic, importlib.metadata; "
                    "print(importlib.metadata.version('gflo'))",
                ],
                capture=True,
            )
            report["gflo_installed"] = True
        except (OSError, subprocess.SubprocessError):
            pass
    if shutil.which("docker"):
        try:
            probe = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            report["docker_daemon"] = bool(probe.stdout.strip())
        except (OSError, subprocess.SubprocessError):
            pass
    return report


def install_environment(target: Path) -> Path:
    if target.exists() and not (target / "pyvenv.cfg").is_file():
        raise ValueError("Refusing an existing directory that is not a virtual environment")
    python = target / "bin/python"
    if not target.exists():
        host_pip = (
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"], capture_output=True, timeout=30
            ).returncode
            == 0
        )
        venv.EnvBuilder(with_pip=not host_pip).create(target)
    else:
        host_pip = (
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"], capture_output=True, timeout=30
            ).returncode
            == 0
        )
    installer = (
        [sys.executable, "-m", "pip", "--python", str(python)]
        if host_pip
        else [str(python), "-m", "pip"]
    )
    run(installer + ["install", "-r", str(ROOT / "requirements-dev.lock"), "-e", str(ROOT)])
    return python


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv", type=Path, default=ROOT / ".venv", help="Virtual environment directory"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Report readiness without installing"
    )
    parser.add_argument(
        "--start-model",
        action="store_true",
        help="Also check and start the configured Docker model service",
    )
    parser.add_argument(
        "--config", type=Path, default=ROOT / "infra/serving/vllm-5090-graphs.example.json"
    )
    parser.add_argument("--demo-dir", type=Path, default=ROOT / ".gflo/demo")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 or newer is required")
    if args.check_only and args.start_model:
        parser.error("--check-only cannot start the model")
    target = args.venv.expanduser().resolve()
    try:
        python = target / "bin/python"
        if not args.check_only:
            python = install_environment(target)
            demo = args.demo_dir.expanduser().resolve()
            demo.mkdir(parents=True, exist_ok=True)
            generated = run(
                [str(python), "examples/prepare_demo.py", "--config", str(args.config.resolve())],
                capture=True,
            )
            plan = demo / "run-plan.json"
            if plan.exists() and plan.read_text() != generated.stdout:
                raise ValueError(
                    "Demo plan differs; choose a new --demo-dir to preserve prior work"
                )
            plan.write_text(generated.stdout)
            run(
                [
                    str(python),
                    "-m",
                    "gflo",
                    "--db",
                    str(demo / "ledger.db"),
                    "submit-run",
                    str(plan),
                ]
            )
            if args.start_model:
                run(
                    [
                        str(python),
                        "scripts/serve.py",
                        "doctor",
                        "--config",
                        str(args.config.resolve()),
                    ]
                )
                run(["docker", "pull", BROKER])
                run([str(python), "scripts/serve.py", "up", "--config", str(args.config.resolve())])
        report = readiness(python)
        demo_db = args.demo_dir.expanduser().resolve() / "ledger.db"
        report["demo_prepared"] = demo_db.is_file()
        print(json.dumps(report, indent=2))
        if report["gflo_installed"]:
            print("CPU setup ready. Inspect the demo with:")
            print(f"{python} -m gflo --db {demo_db} status pilot-v1-01-slug")
            if not args.start_model:
                print("GPU execution still needs the model cache and NVIDIA Docker runtime.")
                print(
                    "See docs/getting-started.md, or rerun with --start-model after provisioning."
                )
        return 0 if report["gflo_installed"] else 1
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Setup stopped: {error}", file=sys.stderr)
        print(
            "Existing files are retained. Fix the reported prerequisite and rerun; "
            "see docs/getting-started.md.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
