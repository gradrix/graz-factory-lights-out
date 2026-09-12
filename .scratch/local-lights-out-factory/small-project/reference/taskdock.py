"""Trusted preflight reference; never part of worker input or published output."""

import json
import os
import tempfile
from pathlib import Path


def _title(value):
    if (
        not isinstance(value, str)
        or not 1 <= len(value.strip()) <= 120
        or "\n" in value
        or "\r" in value
    ):
        raise ValueError("invalid title")
    return value.strip()


def _read(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("invalid storage") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"version", "tasks"}
        or type(value["version"]) is not int
        or value["version"] != 1
        or not isinstance(value["tasks"], list)
    ):
        raise ValueError("invalid storage")
    seen = set()
    for task in value["tasks"]:
        if (
            not isinstance(task, dict)
            or set(task) != {"id", "title", "done"}
            or type(task["id"]) is not int
            or task["id"] < 1
            or task["id"] in seen
            or type(task["done"]) is not bool
        ):
            raise ValueError("invalid task")
        if _title(task["title"]) != task["title"]:
            raise ValueError("untrimmed stored title")
        seen.add(task["id"])
    return sorted(value["tasks"], key=lambda task: task["id"])


def _write(path, tasks):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            temporary = stream.name
            json.dump({"version": 1, "tasks": tasks}, stream, ensure_ascii=False)
        os.replace(temporary, path)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def add_task(path, title):
    title = _title(title)
    tasks = _read(path)
    task = {"id": max((t["id"] for t in tasks), default=0) + 1, "title": title, "done": False}
    _write(path, tasks + [task])
    return task


def list_tasks(path, include_done=False):
    return [t for t in _read(path) if include_done or not t["done"]]


def complete_task(path, task_id):
    if type(task_id) is not int or task_id < 1:
        raise ValueError("invalid ID")
    tasks = _read(path)
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            _write(path, tasks)
            return task
    raise ValueError("unknown ID")


def export_markdown(path):
    return "# Tasks\n" + "".join(
        f"- [{'x' if t['done'] else ' '}] {t['id']}: {t['title']}\n" for t in _read(path)
    )
