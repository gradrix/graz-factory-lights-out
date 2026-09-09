"""Trusted CLI for repository snapshots; never executes code from the checkout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from gflo.artifacts import ArtifactStore
from gflo.repository import FileEdit, Repository, SnapshotSource, SourceRef, capture_worktree


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--store", type=Path, required=True)
    actions = parser.add_subparsers(dest="repository_action", required=True)
    capture = actions.add_parser(
        "capture", help="Capture Git-visible UTF-8 files from a quiescent worktree"
    )
    capture.add_argument("root", type=Path)
    for name in ("list", "read", "search", "select", "apply"):
        command = actions.add_parser(name)
        command.add_argument("snapshot", help="Snapshot artifact digest returned by capture")
        command.add_argument("--scope", action="append", default=[])
        if name == "list":
            command.add_argument("--limit", type=int, default=100)
            command.add_argument("--after")
        elif name == "read":
            command.add_argument("path")
            command.add_argument("--start-line", type=int, default=1)
            command.add_argument("--max-lines", type=int, default=200)
            command.add_argument("--max-bytes", type=int, default=65536)
        elif name == "search":
            command.add_argument("query")
            command.add_argument("--max-hits", type=int, default=100)
            command.add_argument("--max-files", type=int, default=256)
            command.add_argument("--max-bytes", type=int, default=1048576)
        elif name == "select":
            command.add_argument("paths", nargs="+")
            command.add_argument("--purpose", choices=("context", "execution"), default="context")
            command.add_argument("--max-bytes", type=int, default=262144)
            command.add_argument("--max-files", type=int, default=100)
        else:
            command.add_argument("edits", type=Path, help="Mapping of paths to FileEdit records")
            command.add_argument("--current", required=True, help="Trusted current snapshot digest")
            command.add_argument("--writable", action="append", required=True)


def execute(args: argparse.Namespace) -> dict[str, Any]:
    if args.repository_action == "capture":
        args.store.parent.mkdir(parents=True, exist_ok=True)
        artifacts = ArtifactStore(args.store)
        return capture_worktree(artifacts, args.root).model_dump(mode="json")
    if not args.store.is_dir():
        raise ValueError("Repository artifact store does not exist")
    artifacts = ArtifactStore(args.store)
    ref = SourceRef(kind="repository-snapshot-v1", artifact_digest=args.snapshot)
    repository = Repository(SnapshotSource(artifacts, ref), scopes=tuple(args.scope))
    if args.repository_action == "list":
        result = repository.list_paths(limit=args.limit, after=args.after)
    elif args.repository_action == "read":
        return repository.read(
            args.path,
            start_line=args.start_line,
            max_lines=args.max_lines,
            max_bytes=args.max_bytes,
        ).model_dump(mode="json")
    elif args.repository_action == "search":
        return repository.search(
            args.query, max_hits=args.max_hits, max_files=args.max_files, max_bytes=args.max_bytes
        ).model_dump(mode="json")
    elif args.repository_action == "select":
        return repository.select(
            tuple(args.paths),
            purpose=args.purpose,
            max_bytes=args.max_bytes,
            max_files=args.max_files,
        ).model_dump(mode="json")
    else:
        data = json.loads(args.edits.read_bytes())
        if not isinstance(data, dict):
            raise ValueError("Edits must be a mapping")
        edits = {
            path: FileEdit.model_validate_json(json.dumps(value)) for path, value in data.items()
        }
        return repository.apply(
            artifacts,
            edits,
            current_source=SourceRef(kind="repository-snapshot-v1", artifact_digest=args.current),
            writable_paths=tuple(args.writable),
        ).model_dump(mode="json")
    return result.model_dump(mode="json")
