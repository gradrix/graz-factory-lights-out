import json
import os
import pathlib
import tempfile


def _resolve_path(path):
    if isinstance(path, str):
        return pathlib.Path(path)
    if isinstance(path, pathlib.Path):
        return path
    raise TypeError("path must be str or pathlib.Path")


def _validate_title(title):
    if not isinstance(title, str):
        raise ValueError("title must be a string")
    if '\r' in title or '\n' in title:
        raise ValueError("title must not contain CR or LF")
    stripped = title.strip()
    if len(stripped) < 1 or len(stripped) > 120:
        raise ValueError("title must be 1-120 characters after stripping")
    return stripped


def _validate_task(task):
    if not isinstance(task, dict):
        raise ValueError("task must be a dict")
    if set(task.keys()) != {"id", "title", "done"}:
        raise ValueError("task has invalid keys")
    tid = task["id"]
    if isinstance(tid, bool) or not isinstance(tid, int) or tid < 1:
        raise ValueError("task id must be a positive integer")
    title = task["title"]
    if not isinstance(title, str):
        raise ValueError("task title must be a string")
    if title != title.strip():
        raise ValueError("task title must be trimmed")
    if len(title) < 1 or len(title) > 120:
        raise ValueError("task title must be 1-120 characters")
    if '\r' in title or '\n' in title:
        raise ValueError("task title must not contain CR or LF")
    done = task["done"]
    if not isinstance(done, bool):
        raise ValueError("task done must be a boolean")


def _validate_storage(data):
    if not isinstance(data, dict):
        raise ValueError("storage root must be a dict")
    if set(data.keys()) != {"version", "tasks"}:
        raise ValueError("storage root has invalid keys")
    version = data["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        raise ValueError("version must be integer 1")
    tasks = data["tasks"]
    if not isinstance(tasks, list):
        raise ValueError("tasks must be a list")
    seen_ids = set()
    for task in tasks:
        _validate_task(task)
        tid = task["id"]
        if tid in seen_ids:
            raise ValueError("duplicate task id")
        seen_ids.add(tid)
    return data


def _validate_storage_strict(data):
    """Validate storage with strict version check (rejects version 1.0)."""
    if not isinstance(data, dict):
        raise ValueError("storage root must be a dict")
    if set(data.keys()) != {"version", "tasks"}:
        raise ValueError("storage root has invalid keys")
    version = data["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        raise ValueError("version must be integer 1")
    tasks = data["tasks"]
    if not isinstance(tasks, list):
        raise ValueError("tasks must be a list")
    seen_ids = set()
    for task in tasks:
        _validate_task(task)
        tid = task["id"]
        if tid in seen_ids:
            raise ValueError("duplicate task id")
        seen_ids.add(tid)
    return data


def _read_storage(path):
    p = _resolve_path(path)
    if not p.exists():
        return {"version": 1, "tasks": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        raise ValueError("malformed JSON")
    return _validate_storage(data)


def _write_storage(path, data):
    p = _resolve_path(path)
    parent = p.parent
    if not parent.exists():
        raise OSError(f"parent directory does not exist: {parent}")
    tmp_fd = None
    tmp_path = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(parent), suffix=".tmp")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            tmp_fd = None
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp_path, str(p))
        tmp_path = None
    except BaseException:
        if tmp_fd is not None:
            os.close(tmp_fd)
        if tmp_path is not None and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def add_task(path, title):
    p = _resolve_path(path)
    title = _validate_title(title)
    data = _read_storage(p)
    tasks = data["tasks"]
    max_id = max((t["id"] for t in tasks), default=0)
    new_task = {"id": max_id + 1, "title": title, "done": False}
    tasks.append(new_task)
    _write_storage(p, data)
    return new_task


def list_tasks(path, include_done=False):
    data = _read_storage(path)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if not include_done:
        tasks = [t for t in tasks if not t["done"]]
    return tasks


def complete_task(path, task_id):
    if isinstance(task_id, bool) or not isinstance(task_id, int) or task_id < 1:
        raise ValueError("task_id must be a positive integer")
    p = _resolve_path(path)
    data = _read_storage(p)
    found = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            found = t
            break
    if found is None:
        raise ValueError(f"unknown task id: {task_id}")
    found["done"] = True
    _write_storage(p, data)
    return found


def export_markdown(path):
    data = _read_storage(path)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    lines = ["# Tasks\n"]
    for t in tasks:
        check = "x" if t["done"] else " "
        lines.append(f"- [{check}] {t['id']}: {t['title']}\n")
    return "".join(lines)
