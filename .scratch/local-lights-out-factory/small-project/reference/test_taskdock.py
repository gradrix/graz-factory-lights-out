import json

import pytest
import taskdock as api


def test_persistence(tmp_path):
    p = tmp_path / "tasks.json"
    task = api.add_task(p, "one")
    assert api.list_tasks(p) == [task]
    assert json.loads(p.read_text())["tasks"] == [task]


def test_filter(tmp_path):
    p = tmp_path / "tasks.json"
    api.add_task(p, "one")
    api.complete_task(p, 1)
    assert api.list_tasks(p) == []
    assert api.list_tasks(p, True)[0]["done"] is True


def test_ids(tmp_path):
    p = tmp_path / "tasks.json"
    api.add_task(p, "one")
    api.complete_task(p, 1)
    assert api.add_task(p, "two")["id"] == 2


def test_invalid_title(tmp_path):
    p = tmp_path / "tasks.json"
    with pytest.raises(ValueError):
        api.add_task(p, " ")
    assert not p.exists()


def test_corrupt_storage(tmp_path):
    p = tmp_path / "tasks.json"
    p.write_text("bad")
    with pytest.raises(ValueError):
        api.add_task(p, "one")
    assert p.read_text() == "bad"


def test_complete(tmp_path):
    p = tmp_path / "tasks.json"
    api.add_task(p, "one")
    assert api.complete_task(p, 1)["done"] is True
    assert api.complete_task(p, 1)["done"] is True
    assert api.list_tasks(p, True)[0]["done"] is True
    with pytest.raises(ValueError):
        api.complete_task(p, 99)
