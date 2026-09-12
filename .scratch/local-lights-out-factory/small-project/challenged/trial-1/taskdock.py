import json
import os
import pathlib
import tempfile
from typing import Union


def _resolve_path(path: Union[str, pathlib.Path]) -> pathlib.Path:
    if isinstance(path, pathlib.Path):
        return path
    if isinstance(path, str):
        return pathlib.Path(path)
    raise TypeError("path must be str or pathlib.Path")


def _validate_title(title: str) -> str:
    if not isinstance(title, str):
        raise ValueError("title must be a string")
    stripped = title.strip()
    if len(stripped) < 1 or len(stripped) > 120:
        raise ValueError("title must be 1-120 characters after stripping")
    if '\r' in stripped or '\n' in stripped:
        raise ValueError("title must not contain CR or LF")
    return stripped


def _load_storage(path: pathlib.Path) -> dict:
    if not path.exists():
        return {"version": 1, "tasks": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"malformed JSON: {e}")
    _validate_storage(data)
    return data


def _validate_storage(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("storage must be a JSON object")
    if set(data.keys()) != {"version", "tasks"}:
        raise ValueError("storage must have exactly 'version' and 'tasks' keys")
    if isinstance(data["version"], bool) or data["version"] != 1:
        raise ValueError("version must be integer 1")
    tasks = data["tasks"]
    if not isinstance(tasks, list):
        raise ValueError("tasks must be a list")
    seen_ids = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("each task must be a dict")
        if set(task.keys()) != {"id", "title", "done"}:
            raise ValueError("task must have exactly 'id', 'title', 'done' keys")
        tid = task["id"]
        if isinstance(tid, bool) or not isinstance(tid, int) or tid < 1:
            raise ValueError("task id must be a positive integer")
        if tid in seen_ids:
            raise ValueError("duplicate task id")
        seen_ids.add(tid)
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


def _save_storage(path: pathlib.Path, data: dict) -> None:
    parent = path.parent
    if not parent.exists():
        raise OSError(f"parent directory {parent} does not exist")
    fd, tmp_path = tempfile.mkstemp(dir=str(parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def add_task(path: Union[str, pathlib.Path], title: str) -> dict:
    p = _resolve_path(path)
    title = _validate_title(title)
    data = _load_storage(p)
    tasks = data["tasks"]
    max_id = max((t["id"] for t in tasks), default=0)
    new_task = {"id": max_id + 1, "title": title, "done": False}
    tasks.append(new_task)
    _save_storage(p, data)
    return new_task


def list_tasks(path: Union[str, pathlib.Path], include_done: bool = False) -> list:
    p = _resolve_path(path)
    data = _load_storage(p)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if not include_done:
        tasks = [t for t in tasks if not t["done"]]
    return tasks


def complete_task(path: Union[str, pathlib.Path], task_id: int) -> dict:
    p = _resolve_path(path)
    if isinstance(task_id, bool) or not isinstance(task_id, int) or task_id < 1:
        raise ValueError("task_id must be a positive integer")
    data = _load_storage(p)
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            _save_storage(p, data)
            return task
    raise ValueError(f"unknown task id {task_id}")


def export_markdown(path: Union[str, pathlib.Path]) -> str:
    p = _resolve_path(path)
    data = _load_storage(p)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    lines = ["# Tasks\n"]
    for task in tasks:
        checkbox = "x" if task["done"] else " "
        lines.append(f"- [{checkbox}] {task['id']}: {task['title']}\n")
    return "".join(lines)
