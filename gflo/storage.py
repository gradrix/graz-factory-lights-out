"""Prospective free-space admission; not a reservation against concurrent writers."""

from __future__ import annotations

import errno
import shutil
from pathlib import Path


class StoragePressure(OSError):
    """Insufficient available space for the configured control-plane reserve."""


def require_space(path: Path, reserve_bytes: int, *, pending_bytes: int = 0) -> None:
    if type(reserve_bytes) is not int or reserve_bytes < 0:
        raise ValueError("Storage reserve must be a nonnegative integer")
    if type(pending_bytes) is not int or pending_bytes < 0:
        raise ValueError("Pending storage must be a nonnegative integer")
    if reserve_bytes == 0:
        return
    available = shutil.disk_usage(path).free
    if available < reserve_bytes + pending_bytes:
        raise StoragePressure(
            errno.ENOSPC,
            f"Storage admission refused: {available} available bytes; "
            f"{reserve_bytes} reserve + {pending_bytes} pending bytes required",
            str(path),
        )
