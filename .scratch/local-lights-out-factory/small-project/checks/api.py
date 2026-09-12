"""Independent API/storage checks, outside worker source."""

import importlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import taskdock as api


def invalid(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("invalid input accepted")


with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "tasks.json"
    assert api.list_tasks(path) == []
    assert api.export_markdown(path) == "# Tasks\n"
    assert not path.exists()
    one = api.add_task(str(path), "  Žąsis  ")
    assert one == {"id": 1, "title": "Žąsis", "done": False}
    two = api.add_task(path, "Žąsis")
    assert two == {"id": 2, "title": "Žąsis", "done": False}
    assert api.complete_task(path, 1) == {**one, "done": True}
    assert api.complete_task(path, 1) == {**one, "done": True}
    assert api.list_tasks(path) == [two]
    assert api.list_tasks(path, True) == [{**one, "done": True}, two]
    assert api.add_task(path, "third")["id"] == 3
    assert api.export_markdown(path) == "# Tasks\n- [x] 1: Žąsis\n- [ ] 2: Žąsis\n- [ ] 3: third\n"
    before = path.read_bytes()
    for title in ("", "  ", "a\nb", "a\rb", "x" * 121, 1, None, True):
        invalid(lambda: api.add_task(path, title))
        assert path.read_bytes() == before
    for task_id in (True, False, 0, -1, "1", 999, None, 1.0):
        invalid(lambda: api.complete_task(path, task_id))
        assert path.read_bytes() == before
    # Unsorted valid storage is read without modification.
    path.write_text(json.dumps({"version": 1, "tasks": [two, {**one, "done": True}]}))
    before = path.read_bytes()
    assert [t["id"] for t in api.list_tasks(path, True)] == [1, 2]
    assert path.read_bytes() == before
    good = {"version": 1, "tasks": [one]}
    malformed = [
        "{",
        "null",
        "[]",
        "true",
        json.dumps({**good, "version": True}),
        json.dumps({**good, "extra": 1}),
        json.dumps({**good, "tasks": [one, one]}),
        json.dumps({**good, "tasks": "wrong"}),
    ]
    for change in (
        {"id": True},
        {"id": -1},
        {"done": 1},
        {"title": " untrimmed "},
        {"title": "x\ny"},
        {"title": ""},
        {"extra": 1},
    ):
        malformed.append(json.dumps({"version": 1, "tasks": [{**one, **change}]}))
    for raw in malformed:
        path.write_text(raw)
        for call in (
            lambda: api.list_tasks(path),
            lambda: api.add_task(path, "safe"),
            lambda: api.complete_task(path, 1),
            lambda: api.export_markdown(path),
        ):
            invalid(call)
            assert path.read_text() == raw
    path.write_text(json.dumps(good))
    before = path.read_bytes()
    # Patching before reload also covers `from os import replace` implementations.
    with patch("os.replace", side_effect=OSError("injected replacement failure")) as replacement:
        importlib.reload(api)
        try:
            api.add_task(path, "must not persist")
        except OSError:
            pass
        else:
            raise AssertionError("replacement failure swallowed or atomic replace bypassed")
        assert replacement.called
    importlib.reload(api)
    assert path.read_bytes() == before
    assert {p.name for p in Path(folder).iterdir()} == {"tasks.json"}
print("api-ok")
