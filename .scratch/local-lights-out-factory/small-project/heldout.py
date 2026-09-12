"""Post-acceptance state-sequence audit, never used for worker feedback."""

import importlib
import random
import tempfile
from pathlib import Path
from unittest.mock import patch

import taskdock as api

randomizer = random.Random(90212)
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "heldout.json"
    expected = []
    for step in range(60):
        if expected and randomizer.randrange(3) == 0:
            task = randomizer.choice(expected)
            task["done"] = True
            assert api.complete_task(path, task["id"]) == task
        else:
            task = {"id": len(expected) + 1, "title": f"Darbas 🦉 {step}", "done": False}
            assert api.add_task(path, "  " + task["title"] + "  ") == task
            expected.append(task)
        assert api.list_tasks(path, True) == expected
        assert api.list_tasks(path) == [t for t in expected if not t["done"]]
    before = path.read_bytes()
    with patch("os.replace", side_effect=OSError("held-out completion failure")):
        importlib.reload(api)
        try:
            api.complete_task(path, expected[-1]["id"])
        except OSError:
            pass
        else:
            raise AssertionError("completion did not use atomic replacement")
    importlib.reload(api)
    assert path.read_bytes() == before
    assert {p.name for p in Path(folder).iterdir()} == {path.name}
    assert api.add_task(path, "recovered")["id"] == len(expected) + 1
print("heldout-ok")
