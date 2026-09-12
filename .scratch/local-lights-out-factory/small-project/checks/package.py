"""Install offline and execute the installed entry point outside the source tree."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import tomllib

config = tomllib.loads(Path("pyproject.toml").read_text())
assert config["project"]["name"] == "taskdock-local"
assert config["project"]["version"] == "0.1.0"
assert config["project"].get("dependencies", []) == []
assert config["project"]["requires-python"] == ">=3.11"
assert config["project"]["scripts"]["taskdock"] == "taskdock_cli:main"
assert config["build-system"]["build-backend"] == "setuptools.build_meta"
with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    target = root / "installed"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--no-build-isolation",
            "--disable-pip-version-check",
            "--target",
            str(target),
            ".",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    env = {**os.environ, "PYTHONPATH": str(target)}
    # The broker deliberately mounts writable storage noexec. Exercise the installed
    # entry script through its pinned interpreter without relaxing that boundary.
    command = [sys.executable, str(target / "bin/taskdock"), "--file", str(root / "data.json")]
    created = subprocess.run(
        command + ["add", "installed"], cwd=root, env=env, capture_output=True, text=True
    )
    assert created.returncode == 0, created.stderr
    assert json.loads(created.stdout) == {"id": 1, "title": "installed", "done": False}
    listed = subprocess.run(command + ["list"], cwd=root, env=env, capture_output=True, text=True)
    assert listed.returncode == 0 and json.loads(listed.stdout) == [json.loads(created.stdout)]
print("package-ok")
