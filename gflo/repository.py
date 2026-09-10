"""Revision-bound repository access independent of bounded worker bundles.

Capture requires a quiescent Git worktree. The manifest identifies captured bytes,
not HEAD; inventory and a second content pass detect concurrent changes. No checkout
is modified. Indexes and larger execution environments are outside this first slice.
"""

from __future__ import annotations

import hashlib
import os
import re
import selectors
import stat
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Literal, Protocol

from pydantic import Field, model_validator

from gflo.artifacts import ArtifactStore
from gflo.broker import SourceBundle
from gflo.records import Digest, Record

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_CAPTURE_BYTES = 512 * 1024 * 1024
MAX_FILES = 100_000


class RepositoryError(ValueError):
    """Unsupported, stale, unavailable, or over-budget repository access."""


def _path(path: str) -> None:
    if (
        len(path) > 200
        or not re.fullmatch(r"[A-Za-z0-9_./-]+", path)
        or path.startswith("/")
        or any(p in ("", ".", "..") for p in path.split("/"))
    ):
        raise RepositoryError("Expected a normalized supported relative path")


def _within(path: str, scopes: tuple[str, ...]) -> bool:
    return not scopes or any(path == s or path.startswith(s + "/") for s in scopes)


def _text(data: bytes) -> str:
    if b"\0" in data:
        raise RepositoryError("Binary content is unsupported")
    try:
        return data.decode("utf-8")
    except UnicodeError as error:
        raise RepositoryError("Only UTF-8 text is supported") from error


def _lines(text: str) -> list[str]:
    pieces = text.split("\n")
    return [part + "\n" for part in pieces[:-1]] + ([pieces[-1]] if pieces[-1] else [])


class SourceRef(Record):
    kind: Literal["source-bundle-v1", "repository-snapshot-v1"]
    artifact_digest: Digest


class FileIdentity(Record):
    content_digest: Digest
    size_bytes: Annotated[int, Field(ge=0, le=MAX_FILE_BYTES)]
    executable: bool = False


class Snapshot(Record):
    kind: Literal["repository-snapshot-v1"] = "repository-snapshot-v1"
    files: Annotated[dict[str, FileIdentity], Field(min_length=1, max_length=MAX_FILES)]
    parent: SourceRef | None = None
    inventory_policy: Literal["git-visible-v1", "bundle-v1", "derived-v1"] = "derived-v1"

    @model_validator(mode="after")
    def names(self) -> Snapshot:
        for name in self.files:
            _path(name)
            parts = name.split("/")
            if any("/".join(parts[:i]) in self.files for i in range(1, len(parts))):
                raise RepositoryError("File/directory collision")
        if sum(f.size_bytes for f in self.files.values()) > MAX_CAPTURE_BYTES:
            raise RepositoryError("Snapshot exceeds supported total byte budget")
        return self


class SourceBackend(Protocol):
    @property
    def ref(self) -> SourceRef: ...
    @property
    def files(self) -> Mapping[str, FileIdentity]: ...
    def read_bytes(self, path: str) -> bytes: ...
    def retain(self, artifacts: ArtifactStore) -> None: ...


class BundleSource:
    """Adapter that preserves the exact legacy SourceBundle identity."""

    def __init__(self, bundle: SourceBundle):
        bundle = SourceBundle.model_validate(bundle)
        self._ref = SourceRef(kind="source-bundle-v1", artifact_digest=bundle.digest())
        self._bundle_bytes = bundle.canonical().encode()
        self._data = {p: text.encode("utf-8") for p, text in bundle.files.items()}
        self._files = MappingProxyType(
            {
                p: FileIdentity(content_digest=hashlib.sha256(b).hexdigest(), size_bytes=len(b))
                for p, b in self._data.items()
            }
        )

    @property
    def ref(self) -> SourceRef:
        return self._ref

    @property
    def files(self) -> Mapping[str, FileIdentity]:
        return self._files

    def read_bytes(self, path: str) -> bytes:
        return self._data[path]

    def retain(self, artifacts: ArtifactStore) -> None:
        artifacts.publish(self._bundle_bytes)
        for data in self._data.values():
            artifacts.publish(data)


class SnapshotSource:
    def __init__(self, artifacts: ArtifactStore, ref: SourceRef):
        ref = SourceRef.model_validate(ref)
        if ref.kind != "repository-snapshot-v1":
            raise RepositoryError("Snapshot adapter requires a snapshot reference")
        manifest = Snapshot.model_validate_json(artifacts.read(ref.artifact_digest))
        self._ref, self._artifacts = ref, artifacts
        self._parent = manifest.parent
        self._files = MappingProxyType(dict(manifest.files))

    @property
    def ref(self) -> SourceRef:
        return self._ref

    @property
    def files(self) -> Mapping[str, FileIdentity]:
        return self._files

    def read_bytes(self, path: str) -> bytes:
        entry = self.files[path]
        data = self._artifacts.read(entry.content_digest)
        if len(data) != entry.size_bytes:
            raise RepositoryError("File size differs from snapshot identity")
        return data

    def retain(self, artifacts: ArtifactStore) -> None:
        if artifacts.root.resolve() != self._artifacts.root.resolve():
            raise RepositoryError("Snapshot edits require the original artifact store")
        artifacts.verify(self.ref.artifact_digest)
        if self._parent is not None:
            artifacts.verify(self._parent.artifact_digest)
        for path in self.files:
            self.read_bytes(path)


def _publish(
    artifacts: ArtifactStore,
    files: Mapping[str, FileIdentity],
    parent: SourceRef | None = None,
    inventory_policy: Literal["git-visible-v1", "bundle-v1", "derived-v1"] = "derived-v1",
) -> SourceRef:
    snapshot = Snapshot(files=dict(files), parent=parent, inventory_policy=inventory_policy)
    return SourceRef(
        kind="repository-snapshot-v1",
        artifact_digest=artifacts.publish(snapshot.canonical().encode()),
    )


def snapshot_bundle(artifacts: ArtifactStore, bundle: SourceBundle) -> SourceRef:
    source = BundleSource(bundle)
    artifacts.publish(bundle.canonical().encode())
    for path in source.files:
        artifacts.publish(source.read_bytes(path))
    return _publish(artifacts, source.files, source.ref, "bundle-v1")


def _inventory(root: Path) -> tuple[str, ...]:
    def git(*args: str) -> bytes:
        process = subprocess.Popen(
            ["git", "-C", str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        assert process.stdout is not None
        data = bytearray()
        deadline = time.monotonic() + 30
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise RepositoryError("Git inventory timed out")
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        break
                    data.extend(chunk)
                    if len(data) > 32 * 1024 * 1024:
                        raise RepositoryError("Git inventory exceeds 32 MiB")
            if process.wait(timeout=max(0.01, deadline - time.monotonic())) != 0:
                raise RepositoryError("Git inventory command failed")
            return bytes(data)
        finally:
            process.stdout.close()
            if process.poll() is None:
                process.kill()
            process.wait()

    top = Path(os.fsdecode(git("rev-parse", "--show-toplevel")).strip()).resolve()
    if top != root:
        raise RepositoryError("Capture requires the Git worktree root")
    paths = set()
    for row in git("ls-files", "--stage", "-z").split(b"\0"):
        if not row:
            continue
        metadata, raw_path = row.split(b"\t", 1)
        mode, _, stage = metadata.split()
        if mode not in (b"100644", b"100755") or stage != b"0":
            raise RepositoryError("Symlinks, submodules, and unresolved merges are unsupported")
        paths.add(os.fsdecode(raw_path))
    paths.update(
        os.fsdecode(p)
        for p in git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
        if p
    )
    paths.difference_update(
        os.fsdecode(p) for p in git("ls-files", "--deleted", "-z").split(b"\0") if p
    )
    if not 1 <= len(paths) <= MAX_FILES:
        raise RepositoryError("Capture requires 1–100000 supported files")
    for path in paths:
        _path(path)
    return tuple(sorted(paths))


def _read_worktree(root: Path, path: str) -> tuple[bytes, bool]:
    _path(path)
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        parts = path.split("/")
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_FILE_BYTES:
                raise RepositoryError("Capture requires regular files of at most 8 MiB")
            data = stream.read(MAX_FILE_BYTES + 1)
            after = os.fstat(stream.fileno())
        if (
            len(data) > MAX_FILE_BYTES
            or before.st_size != len(data)
            or (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_mode)
            != (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_mode)
        ):
            raise RepositoryError("File changed during capture")
        return data, bool(before.st_mode & 0o111)
    finally:
        os.close(directory)


def capture_worktree(artifacts: ArtifactStore, root: Path) -> SourceRef:
    root = root.resolve(strict=True)
    paths = _inventory(root)
    files: dict[str, FileIdentity] = {}
    size = 0
    for path in paths:
        data, executable = _read_worktree(root, path)
        size += len(data)
        if size > MAX_CAPTURE_BYTES:
            raise RepositoryError("Capture exceeds 512 MiB")
        files[path] = FileIdentity(
            content_digest=artifacts.publish(data), size_bytes=len(data), executable=executable
        )
    if paths != _inventory(root):
        raise RepositoryError("Worktree inventory changed during capture")
    for path in paths:
        data, executable = _read_worktree(root, path)
        if (
            hashlib.sha256(data).hexdigest() != files[path].content_digest
            or executable != files[path].executable
        ):
            raise RepositoryError("Worktree changed during capture")
    if paths != _inventory(root):
        raise RepositoryError("Worktree inventory changed during verification")
    return _publish(artifacts, files, inventory_policy="git-visible-v1")


class Listing(Record):
    source: SourceRef
    paths: tuple[str, ...]
    complete: bool
    next_after: str | None


class SourceRead(Record):
    source: SourceRef
    path: str
    file_digest: Digest
    start_line: int
    end_line: int
    content: str
    complete: bool


class SearchHit(Record):
    source: SourceRef
    path: str
    file_digest: Digest
    line: Annotated[int, Field(ge=1)]
    column: Annotated[int, Field(ge=1)]
    excerpt: str


class SearchResult(Record):
    source: SourceRef
    hits: tuple[SearchHit, ...]
    complete: bool
    searched_files: int
    eligible_files: int
    reason: Literal["complete", "file-budget", "byte-budget", "hit-budget"]
    engine: Literal["literal-scan-v1"] = "literal-scan-v1"


class Selection(Record):
    source: SourceRef
    purpose: Literal["context", "execution"]
    bundle: SourceBundle | None
    file_identities: dict[str, FileIdentity]
    omitted: dict[str, str]
    repository_file_count: int
    whole_repository: bool


class FileEdit(Record):
    expected_digest: Digest | None
    content: str


class Repository:
    def __init__(self, source: SourceBackend, scopes: tuple[str, ...] = ()):
        for scope in scopes:
            _path(scope)
        self.source, self.scopes = source, scopes

    def _entry(self, path: str) -> FileIdentity:
        _path(path)
        if not _within(path, self.scopes):
            raise RepositoryError("Path is outside granted scope")
        if path not in self.source.files:
            raise RepositoryError("Path is absent from this snapshot")
        return self.source.files[path]

    def _bytes(self, path: str) -> bytes:
        entry = self._entry(path)
        data = self.source.read_bytes(path)
        if (
            len(data) != entry.size_bytes
            or hashlib.sha256(data).hexdigest() != entry.content_digest
        ):
            raise RepositoryError("Source differs from recorded file identity")
        return data

    def list_paths(self, *, limit: int = 100, after: str | None = None) -> Listing:
        if not 1 <= limit <= 1000:
            raise RepositoryError("Listing limit must be 1–1000")
        if after is not None:
            _path(after)
        paths = sorted(
            p for p in self.source.files if _within(p, self.scopes) and (after is None or p > after)
        )
        chosen = tuple(paths[:limit])
        return Listing(
            source=self.source.ref,
            paths=chosen,
            complete=len(paths) <= limit,
            next_after=chosen[-1] if len(paths) > limit else None,
        )

    def read(
        self, path: str, *, start_line: int = 1, max_lines: int = 200, max_bytes: int = 65536
    ) -> SourceRead:
        if not 1 <= max_lines <= 10000 or not 1 <= max_bytes <= 1048576 or start_line < 1:
            raise RepositoryError("Invalid read budget or line")
        entry = self._entry(path)
        lines = _lines(_text(self._bytes(path)))
        if start_line > max(1, len(lines)):
            raise RepositoryError("Line is outside the file")
        selected: list[str] = []
        size = 0
        for line in lines[start_line - 1 : start_line - 1 + max_lines]:
            count = len(line.encode())
            if size + count > max_bytes:
                if not selected:
                    raise RepositoryError("Requested line exceeds read byte budget")
                break
            selected.append(line)
            size += count
        end = start_line - 1 + len(selected)
        return SourceRead(
            source=self.source.ref,
            path=path,
            file_digest=entry.content_digest,
            start_line=start_line,
            end_line=end,
            content="".join(selected),
            complete=end >= len(lines),
        )

    def read_hit(self, hit: SearchHit) -> SourceRead:
        hit = SearchHit.model_validate(hit)
        if hit.source != self.source.ref or self._entry(hit.path).content_digest != hit.file_digest:
            raise RepositoryError("Search result belongs to another source identity")
        return self.read(hit.path, start_line=hit.line, max_lines=1)

    def search(
        self, query: str, *, max_hits: int = 100, max_files: int = 256, max_bytes: int = 1048576
    ) -> SearchResult:
        if not query or len(query) > 512 or "\n" in query:
            raise RepositoryError(
                "Expected a nonempty single-line literal query of at most 512 characters"
            )
        if (
            not 1 <= max_hits <= 1000
            or not 1 <= max_files <= 10000
            or not 1 <= max_bytes <= 16777216
        ):
            raise RepositoryError("Invalid search budget")
        paths = sorted(p for p in self.source.files if _within(p, self.scopes))
        hits: list[SearchHit] = []
        scanned = size = 0
        reason: Literal["complete", "file-budget", "byte-budget", "hit-budget"] = "complete"
        for path in paths:
            if scanned == max_files:
                reason = "file-budget"
                break
            entry = self._entry(path)
            if size + entry.size_bytes > max_bytes:
                reason = "byte-budget"
                break
            text = _text(self._bytes(path))
            scanned += 1
            size += entry.size_bytes
            for number, line in enumerate(_lines(text), 1):
                column = line.find(query)
                if column >= 0:
                    if len(hits) == max_hits:
                        reason = "hit-budget"
                        break
                    hits.append(
                        SearchHit(
                            source=self.source.ref,
                            path=path,
                            file_digest=entry.content_digest,
                            line=number,
                            column=column + 1,
                            excerpt=line[max(0, column - 120) : column + len(query) + 120],
                        )
                    )
            if reason != "complete":
                break
        return SearchResult(
            source=self.source.ref,
            hits=tuple(hits),
            complete=reason == "complete",
            searched_files=scanned,
            eligible_files=len(paths),
            reason=reason,
        )

    def select(
        self,
        paths: tuple[str, ...],
        *,
        purpose: Literal["context", "execution"] = "context",
        max_bytes: int = 262144,
        max_files: int = 100,
    ) -> Selection:
        if (
            not 1 <= max_bytes <= 262144
            or not 1 <= max_files <= 100
            or purpose not in ("context", "execution")
        ):
            raise RepositoryError("Invalid selection budget or purpose")
        if len(paths) != len(set(paths)) or len(paths) > 1000:
            raise RepositoryError("Selection requires at most 1000 distinct paths")
        files: dict[str, str] = {}
        omitted: dict[str, str] = {}
        identities: dict[str, FileIdentity] = {}
        for path in paths:
            entry = self._entry(path)
            if len(files) == max_files or entry.size_bytes > max_bytes:
                omitted[path] = "budget"
                continue
            text = _text(self._bytes(path))
            try:
                candidate = SourceBundle(files=files | {path: text})
            except ValueError:
                omitted[path] = "bundle-budget"
                continue
            if len(candidate.canonical().encode()) > max_bytes:
                omitted[path] = "byte-budget"
                continue
            files[path], identities[path] = text, entry
        if purpose == "execution" and (omitted or not files):
            raise RepositoryError(
                "Execution selection must include every explicitly requested file"
            )
        return Selection(
            source=self.source.ref,
            purpose=purpose,
            bundle=SourceBundle(files=files) if files else None,
            file_identities=identities,
            omitted=omitted,
            repository_file_count=len(self.source.files),
            whole_repository=len(files) == len(self.source.files),
        )

    def apply(
        self,
        artifacts: ArtifactStore,
        edits: Mapping[str, FileEdit],
        *,
        current_source: SourceRef,
        writable_paths: tuple[str, ...],
    ) -> SourceRef:
        if current_source != self.source.ref:
            raise RepositoryError("Source advanced since edit preparation")
        if not edits or len(edits) > 100 or not writable_paths:
            raise RepositoryError("Edits need bounded changes and explicit writable scopes")
        for scope in writable_paths:
            _path(scope)
        files = dict(self.source.files)
        for path, raw in edits.items():
            _path(path)
            if not _within(path, self.scopes) or not _within(path, writable_paths):
                raise RepositoryError("Edit escapes granted scope")
            edit = FileEdit.model_validate(raw)
            prior = files.get(path)
            if edit.expected_digest != (prior.content_digest if prior else None):
                raise RepositoryError("Original file digest does not match")
            data = edit.content.encode("utf-8")
            _text(data)
            if len(data) > MAX_FILE_BYTES:
                raise RepositoryError("Edited file exceeds snapshot limit")
            files[path] = FileIdentity(
                content_digest=artifacts.publish(data),
                size_bytes=len(data),
                executable=prior.executable if prior else False,
            )
        # Verify every original, including omitted evidence. A snapshot in this
        # store reuses existing blobs instead of staging the whole repository.
        self.source.retain(artifacts)
        return _publish(artifacts, files, self.source.ref)
