"""Bounded storage faults: no host disk exhaustion."""

import errno
import hashlib
import os
import shutil
import sqlite3
from pathlib import Path

import pytest

from gflo.artifacts import ArtifactStore
from gflo.ledger import WorkLedger
from gflo.records import WorkAtom
from gflo.storage import StoragePressure, require_space


def test_reserve_boundary_and_pending_bytes(tmp_path, monkeypatch):
    usage = shutil.disk_usage(tmp_path)
    monkeypatch.setattr(shutil, "disk_usage", lambda path: usage._replace(free=100))
    require_space(tmp_path, 80, pending_bytes=20)
    with pytest.raises(StoragePressure):
        require_space(tmp_path, 80, pending_bytes=21)
    with pytest.raises(ValueError):
        require_space(tmp_path, -1)


@pytest.mark.parametrize("window", ["staging", "link"])
def test_publication_enospc_retains_old_bytes_and_retries(tmp_path, monkeypatch, window):
    store = ArtifactStore(tmp_path / "objects")
    prior = store.publish(b"accepted evidence")
    original = store.audit([prior])

    def full(*args, **kwargs):
        raise OSError(errno.ENOSPC, "isolated injected storage failure")

    with monkeypatch.context() as patch:
        if window == "staging":
            patch.setattr("gflo.artifacts.tempfile.mkstemp", full)
        else:
            patch.setattr(os, "link", full)
        with pytest.raises(OSError) as error:
            store.publish(b"new candidate")
        assert error.value.errno == errno.ENOSPC
    assert store.audit([prior]) == original
    assert store.read(prior) == b"accepted evidence"
    assert store.publish(b"new candidate") == hashlib.sha256(b"new candidate").hexdigest()


def test_low_reserve_rejects_publish_before_staging_and_recovers(tmp_path, monkeypatch):
    store = ArtifactStore(tmp_path / "objects", reserve_bytes=100)
    usage = shutil.disk_usage(tmp_path)
    with monkeypatch.context() as patch:
        patch.setattr(shutil, "disk_usage", lambda path: usage._replace(free=99))
        with pytest.raises(StoragePressure):
            store.publish(b"candidate")
        assert list(store.root.iterdir()) == []
    assert store.read(store.publish(b"candidate")) == b"candidate"


def test_sqlite_full_transaction_rolls_back_and_reopens(tmp_path):
    path = tmp_path / "ledger.db"
    atom = WorkAtom.model_validate_json(Path("examples/work-atom.json").read_bytes())
    with WorkLedger(path) as ledger:
        ledger.submit(atom)
        before = ledger.status(atom.atom_id)
        # SQLite's own per-database page cap bounds this fixture to a few pages.
        ledger._db.execute("CREATE TABLE fault_payload (data BLOB)")
        pages = ledger._db.execute("PRAGMA page_count").fetchone()[0]
        ledger._db.execute(f"PRAGMA max_page_count={pages}")
        with pytest.raises(sqlite3.OperationalError, match="full"):
            with ledger._transaction():
                ledger._db.execute("INSERT INTO fault_payload VALUES (zeroblob(1048576))")
        assert ledger.status(atom.atom_id) == before
        assert ledger._db.execute("SELECT count(*) FROM fault_payload").fetchone()[0] == 0
        ledger._db.execute("PRAGMA max_page_count=10000")
        lease = ledger.claim(atom.atom_id, "recovered")
        ledger.start(lease)
    with WorkLedger(path) as reopened:
        assert reopened.status(atom.atom_id)["status"] == "running"


@pytest.mark.parametrize("window", ["file_sync", "directory_sync", "cleanup_sync"])
def test_fsync_failure_never_reports_publication_success(tmp_path, monkeypatch, window):
    import stat

    store = ArtifactStore(tmp_path / "objects")
    prior = store.publish(b"prior evidence")
    real_sync = os.fsync
    directory_calls = 0
    fired = False

    def fail_selected(fd):
        nonlocal directory_calls, fired
        directory = stat.S_ISDIR(os.fstat(fd).st_mode)
        if directory:
            directory_calls += 1
        target = (
            (window == "file_sync" and not directory)
            or (window == "directory_sync" and directory_calls == 1 and directory)
            or (window == "cleanup_sync" and directory_calls == 2 and directory)
        )
        if target and not fired:
            fired = True
            raise OSError(errno.EIO, "injected fsync failure")
        real_sync(fd)

    with monkeypatch.context() as patch:
        patch.setattr(os, "fsync", fail_selected)
        with pytest.raises(OSError, match="injected fsync failure"):
            store.publish(b"candidate")
    assert fired
    assert store.read(prior) == b"prior evidence"
    # A completed link may survive a sync error; it is not an acceptance receipt.
    assert not store.audit([prior]).corrupt
    reopened = ArtifactStore(store.root)
    assert reopened.read(reopened.publish(b"candidate")) == b"candidate"


def test_cleanup_failure_does_not_mask_original_write_failure(tmp_path, monkeypatch):
    store = ArtifactStore(tmp_path / "objects")

    def fail_sync(fd):
        raise OSError(errno.ENOSPC, "cleanup has no space")

    def fail_link(*args, **kwargs):
        raise OSError(errno.EIO, "original link failure")

    real_sync = os.fsync
    import stat

    with monkeypatch.context() as patch:
        patch.setattr(os, "link", fail_link)
        patch.setattr(
            os,
            "fsync",
            lambda fd: fail_sync(fd) if stat.S_ISDIR(os.fstat(fd).st_mode) else real_sync(fd),
        )
        with pytest.raises(OSError, match="original link failure"):
            store.publish(b"candidate")
    assert store.read(store.publish(b"candidate")) == b"candidate"
