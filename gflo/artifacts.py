"""Controller-owned, append-only byte storage on a local POSIX filesystem.

Publish before referring to content in SQLite. A crash can leave a staging file
or an unreferenced object, never a partially published object. Reconciliation is
read-only: even unreferenced content may belong to an in-flight publication.
Workers must not have write access to this directory or its parents.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import sys
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from gflo.storage import require_space


class ArtifactError(ValueError):
    """Referenced bytes are absent, corrupt, or not a regular stored object."""


@dataclass(frozen=True)
class ArtifactAudit:
    missing: tuple[str, ...]
    corrupt: tuple[str, ...]
    unreferenced: tuple[str, ...]
    staging: tuple[str, ...]


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class ArtifactStore:
    def __init__(self, root: str | Path, *, reserve_bytes: int = 0):
        self.root = Path(root)
        self.reserve_bytes = reserve_bytes
        # The ledger's existing parent is the trusted storage boundary.
        self.root.mkdir(mode=0o700, exist_ok=True)
        if self.root.is_symlink() or not self.root.is_dir():
            raise ArtifactError("Artifact root must be a real directory")
        require_space(self.root, reserve_bytes)
        _sync_directory(self.root.parent)

    def _path(self, digest: str) -> Path:
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ArtifactError("Expected a lowercase SHA-256 digest")
        return self.root / digest

    def read(self, digest: str) -> bytes:
        path = self._path(digest)
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ArtifactError(f"Not a regular artifact: {digest}")
                data = stream.read()
        except OSError as error:
            raise ArtifactError(f"Cannot read artifact: {digest}") from error
        if hashlib.sha256(data).hexdigest() != digest:
            raise ArtifactError(f"Corrupt artifact: {digest}")
        return data

    def verify(self, digest: str) -> None:
        self.read(digest)

    def publish(self, data: bytes) -> str:
        """Durably publish exact bytes without overwriting an existing object."""
        if not isinstance(data, bytes):
            raise TypeError("Publish requires immutable bytes")
        digest = hashlib.sha256(data).hexdigest()
        destination = self._path(digest)
        require_space(self.root, self.reserve_bytes, pending_bytes=len(data))
        fd, name = tempfile.mkstemp(prefix=".staging-", dir=self.root)
        temporary = Path(name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fchmod(stream.fileno(), 0o400)
                os.fsync(stream.fileno())
            try:
                os.link(temporary, destination, follow_symlinks=False)
            except FileExistsError:
                self.verify(digest)
            _sync_directory(self.root)
        finally:
            original = sys.exception()
            try:
                temporary.unlink(missing_ok=True)
                _sync_directory(self.root)
            except OSError as cleanup_error:
                if original is None:
                    raise
                original.add_note(f"Artifact cleanup also failed: {cleanup_error}")
        return digest

    def audit(self, references: Iterable[str]) -> ArtifactAudit:
        """Report a snapshot; never delete or repair bytes or ledger history."""
        referenced = set(references)
        for digest in referenced:
            self._path(digest)
        entries = {p.name for p in self.root.iterdir()}
        objects = {name for name in entries if re.fullmatch(r"[0-9a-f]{64}", name)}
        corrupt = []
        for digest in sorted(objects):
            try:
                self.verify(digest)
            except ArtifactError:
                corrupt.append(digest)
        return ArtifactAudit(
            missing=tuple(sorted(referenced - objects)),
            corrupt=tuple(corrupt),
            unreferenced=tuple(sorted(objects - referenced)),
            staging=tuple(sorted(name for name in entries if name.startswith(".staging-"))),
        )
