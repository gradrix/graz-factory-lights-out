import json
import os
import pathlib
import pytest

import taskdock


@pytest.fixture
def storage_path(tmp_path):
    return tmp_path / "tasks.json"


def test_persistence(storage_path):
    """Added tasks persist across separate API calls."""
    t1 = taskdock.add_task(storage_path, "First")
    t2 = taskdock.add_task(storage_path, "Second")
    assert t1["id"] == 1
    assert t2["id"] == 2
    # Re-read from disk
    tasks = taskdock.list_tasks(storage_path)
    assert len(tasks) == 2
    assert tasks[0]["title"] == "First"
    assert tasks[1]["title"] == "Second"


def test_completed_filtering(storage_path):
    """list_tasks excludes completed by default; include_done shows all."""
    taskdock.add_task(storage_path, "A")
    taskdock.add_task(storage_path, "B")
    taskdock.complete_task(storage_path, 1)
    active = taskdock.list_tasks(storage_path)
    assert len(active) == 1
    assert active[0]["id"] == 2
    all_tasks = taskdock.list_tasks(storage_path, include_done=True)
    assert len(all_tasks) == 2


def test_monotonic_ids_after_completion(storage_path):
    """IDs are monotonic even after completing tasks."""
    taskdock.add_task(storage_path, "A")
    taskdock.add_task(storage_path, "B")
    taskdock.complete_task(storage_path, 1)
    t3 = taskdock.add_task(storage_path, "C")
    assert t3["id"] == 3


def test_invalid_titles(storage_path):
    """Invalid titles raise ValueError and leave storage unchanged."""
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "")
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, " " * 130)
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "\n")
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, 123)
    # Storage should not exist or be empty
    assert not storage_path.exists() or taskdock.list_tasks(storage_path) == []


def test_corrupt_storage_preserved(storage_path):
    """Malformed JSON raises ValueError and original bytes are preserved."""
    storage_path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError):
        taskdock.list_tasks(storage_path)
    # Original content preserved
    assert storage_path.read_text(encoding="utf-8") == "{not valid json"


def test_idempotent_completion_and_unknown_id(storage_path):
    """Completing an already-done task is idempotent; unknown IDs raise ValueError."""
    taskdock.add_task(storage_path, "A")
    result1 = taskdock.complete_task(storage_path, 1)
    assert result1["done"] is True
    # Idempotent
    result2 = taskdock.complete_task(storage_path, 1)
    assert result2["done"] is True
    # Unknown ID
    with pytest.raises(ValueError):
        taskdock.complete_task(storage_path, 999)
    # Non-positive / bool
    with pytest.raises(ValueError):
        taskdock.complete_task(storage_path, 0)
    with pytest.raises(ValueError):
        taskdock.complete_task(storage_path, True)


def test_export_markdown(storage_path):
    """export_markdown produces correct format."""
    taskdock.add_task(storage_path, "Alpha")
    taskdock.add_task(storage_path, "Beta")
    taskdock.complete_task(storage_path, 1)
    md = taskdock.export_markdown(storage_path)
    assert md == "# Tasks\n- [x] 1: Alpha\n- [ ] 2: Beta\n"


def test_export_empty(storage_path):
    """Empty export is just '# Tasks\n'."""
    md = taskdock.export_markdown(storage_path)
    assert md == "# Tasks\n"


def test_unicode_titles(storage_path):
    """Unicode titles are preserved literally."""
    t = taskdock.add_task(storage_path, "\u00e9\u00e8\u00ea\u00fc\u00f6")
    assert t["title"] == "\u00e9\u00e8\u00ea\u00fc\u00f6"
    md = taskdock.export_markdown(storage_path)
    assert "\u00e9\u00e8\u00ea\u00fc\u00f6" in md


def test_missing_file_no_creation(storage_path):
    """Reading/listing/exporting a missing file does not create it."""
    assert taskdock.list_tasks(storage_path) == []
    assert not storage_path.exists()
    assert taskdock.export_markdown(storage_path) == "# Tasks\n"
    assert not storage_path.exists()


def test_raw_cr_lf_titles(storage_path):
    """Raw leading/trailing CR or LF in titles must be rejected, not stripped."""
    # Leading CR
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "\rTitle")
    # Trailing CR
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "Title\r")
    # Leading LF
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "\nTitle")
    # Trailing LF
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "Title\n")
    # Leading CR+LF
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "\r\nTitle")
    # Trailing CR+LF
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "Title\r\n")
    # Storage must not have been created or modified
    assert not storage_path.exists() or taskdock.list_tasks(storage_path) == []


def test_float_version_rejected(storage_path):
    """Storage with version 1.0 (float) must be rejected, not accepted as int 1."""
    # Write storage with float version 1.0
    storage_path.write_text(
        json.dumps({"version": 1.0, "tasks": []}),
        encoding="utf-8",
    )
    # Reading should raise ValueError because version must be integer 1, not bool/float
    with pytest.raises(ValueError):
        taskdock.list_tasks(storage_path)
    # Original bytes must be preserved
    assert storage_path.read_text(encoding="utf-8") == json.dumps(
        {"version": 1.0, "tasks": []}
    )
    # Also test that add_task on float-version storage raises and preserves bytes
    with pytest.raises(ValueError):
        taskdock.add_task(storage_path, "Test")
    assert storage_path.read_text(encoding="utf-8") == json.dumps(
        {"version": 1.0, "tasks": []}
    )
