"""Post-review checks for explicit input-type and raw-title requirements."""

import json
import tempfile
from pathlib import Path

import taskdock

failures = []
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "tasks.json"
    for title in ("\nvalid", "valid\n", "\rvalid", "valid\r"):
        path.unlink(missing_ok=True)
        try:
            taskdock.add_task(path, title)
        except ValueError:
            pass
        else:
            failures.append("raw CR/LF title accepted: " + repr(title))
        if path.exists():
            failures.append("invalid title wrote storage")
    for version in (1.0, True, "1"):
        raw = json.dumps({"version": version, "tasks": []})
        path.write_text(raw)
        for name, call in (
            ("list", lambda: taskdock.list_tasks(path)),
            ("add", lambda: taskdock.add_task(path, "valid")),
            ("export", lambda: taskdock.export_markdown(path)),
        ):
            path.write_text(raw)
            try:
                call()
            except ValueError:
                pass
            else:
                failures.append(f"{name} accepted version {version!r}")
            if path.read_text() != raw:
                failures.append("invalid version storage was overwritten")
assert not failures, failures
print("edge-ok")
