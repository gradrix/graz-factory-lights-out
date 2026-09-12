import json
import os
import pathlib
import pytest

import taskdock


@pytest.fixture
def storage_path(tmp_path):
    return tmp_path / "tasks.json"


def test_persistence(storage_path):
    task = taskdock.add_task(storage_path, "Write report")
    assert task == {"id": 1, "title": "Write report", "done": False}
    # Verify file exists and contains correct JSON
    data = json.loads(storage_path.read_text(encoding="utf-8"))
    assert data == {"version": 1, "tasks": [{"id": 1, "title": "Write report", "done": False}]}
    # Re-read via API
    tasks = taskdock.list_tasks(storage_path)
    assert tasks == [{"id": 1, "title": "Write report", "done": False}]


def test_completed_filtering(storage_path):
    taskdock.add_task(storage_path, "Task A")
    taskdock.add_task(storage_path, "Task B")
    taskdock.add_task(storage_path, "Task C")
    # Complete task 2
    taskdock.complete_task(storage_path, 2)
    # Default list excludes completed
    tasks = taskdock.list_tasks(storage_path)
    assert [t["id"] for t in tasks] == [1, 3]
    # include_done includes all
    all_tasks = taskdock.list_tasks(storage_path, include_done=True)
    assert [t["id"] for t in all_tasks] == [1, 2, 3]
    assert all_tasks[1]["done"] is True


def test_monotonic_ids_after_completion(storage_path):
    taskdock.add_task(storage_path, "First")
    taskdock.add_task(storage_path, "Second")
    taskdock.complete_task(storage_path, 1)
    # New task should get id 3, not reuse 1
    task = taskdock.add_task(storage_path, "Third")
    assert task["id"] == 3
    assert task["title"] == "Third"
    assert task["done"] is False


def test_invalid_titles(storage_path):
    # Empty title
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "")
    # Whitespace-only title
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "   ")
    # Too long (>120 chars after stripping)
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "a" * 121)
    # Contains CR
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "bad\rtitle")
    # Contains LF
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "bad\ntitle")
    # Non-string
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, 123)
    # Storage should not be created or modified
    assert not storage_path.exists()


def test_invalid_storage_preservation(tmp_path):
    # Write corrupt JSON
    corrupt_path = tmp_path / "corrupt.json"
    corrupt_path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError):
        taskdock.list_tasks(corrupt_path)
    # Original bytes preserved
    assert corrupt_path.read_text(encoding="utf-8") == "{not valid json"

    # Write invalid version
    bad_version_path = tmp_path / "bad_version.json"
    bad_version_path.write_text(json.dumps({"version": 2, "tasks": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        taskdock.list_tasks(bad_version_path)
    assert json.loads(bad_version_path.read_text(encoding="utf-8")) == {"version": 2, "tasks": []}

    # Write with extra keys
    extra_keys_path = tmp_path / "extra.json"
    extra_keys_path.write_text(json.dumps({"version": 1, "tasks": [], "extra": True}), encoding="utf-8")
    with pytest.raises(ValueError):
        taskdock.list_tasks(extra_keys_path)
    assert json.loads(extra_keys_path.read_text(encoding="utf-8"))["extra"] is True


def test_idempotent_completion_and_unknown_id(storage_path):
    taskdock.add_task(storage_path, "Do something")
    # Complete it
    result = taskdock.complete_task(storage_path, 1)
    assert result["done"] is True
    # Complete again - idempotent
    result2 = taskdock.complete_task(storage_path, 1)
    assert result2["done"] is True
    # Unknown ID raises ValueError
    with pytest.raises(ValueError):
        taskdock.complete_task(storage_path, 999)
    # Invalid ID (0) raises ValueError
    with pytest.raises(ValueError):
        taskdock.complete_task(storage_path, 0)
    # Negative ID raises ValueError
    with pytest.raises(ValueError):
        taskdock.complete_task(storage_path, -1)
    # Bool ID raises ValueError (True is not a valid int for this purpose)
    with pytest.raises(ValueError):
        taskdock.complete_task(storage_path, True)


def test_export_markdown(storage_path):
    # Empty export
    assert taskdock.export_markdown(storage_path) == "# Tasks\n"
    # Add tasks
    taskdock.add_task(storage_path, "Alpha")
    taskdock.add_task(storage_path, "Beta")
    taskdock.complete_task(storage_path, 1)
    md = taskdock.export_markdown(storage_path)
    assert md == "# Tasks\n- [x] 1: Alpha\n- [ ] 2: Beta\n"


def test_unicode_titles(storage_path):
    task = taskdock.add_task(storage_path, "\u00e9\u00e8\u00ea\u00fc\u00f6\u00df")
    assert task["title"] == "\u00e9\u00e8\u00ea\u00fc\u00f6\u00df"
    tasks = taskdock.list_tasks(storage_path)
    assert tasks[0]["title"] == "\u00e9\u00e8\u00ea\u00fc\u00f6\u00df"


def test_duplicate_titles(storage_path):
    t1 = taskdock.add_task(storage_path, "Same")
    t2 = taskdock.add_task(storage_path, "Same")
    assert t1["id"] == 1
    assert t2["id"] == 2
    tasks = taskdock.list_tasks(storage_path)
    assert len(tasks) == 2
    assert tasks[0]["title"] == "Same"
    assert tasks[1]["title"] == "Same"
