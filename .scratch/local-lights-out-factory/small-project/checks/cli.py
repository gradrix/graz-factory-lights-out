"""Independent real-process workflows."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "tasks.json"

    def run(*args, code=0):
        result = subprocess.run(
            [sys.executable, "-B", "-m", "taskdock_cli", "--file", str(path), *args],
            capture_output=True,
            text=True,
        )
        assert result.returncode == code, (args, result.stdout, result.stderr)
        if code:
            assert result.stderr and not result.stdout and "Traceback" not in result.stderr
        else:
            assert not result.stderr
        return result.stdout

    assert json.loads(run("list")) == [] and not path.exists()
    assert json.loads(run("add", "  Review café  ")) == {
        "id": 1,
        "title": "Review café",
        "done": False,
    }
    assert json.loads(run("done", "1"))["done"] is True
    assert json.loads(run("list")) == []
    assert len(json.loads(run("list", "--all"))) == 1
    assert run("export") == "# Tasks\n- [x] 1: Review café\n"
    before = path.read_bytes()
    for args in (("done", "99"), ("done", "wrong"), ("add", " "), ("unknown",)):
        run(*args, code=2)
        assert path.read_bytes() == before
    path.write_text("invalid json")
    run("list", code=2)
    assert path.read_text() == "invalid json"
    path.unlink()
    path.mkdir()
    run("add", "filesystem failure", code=2)
    help_result = subprocess.run(
        [sys.executable, "-m", "taskdock_cli", "--help"], capture_output=True
    )
    assert help_result.returncode == 0 and help_result.stdout
print("cli-ok")
