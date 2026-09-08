"""Crash windows and integrity checks against real local filesystem objects."""

import hashlib
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from gflo.artifacts import ArtifactError, ArtifactStore


def test_duplicate_concurrent_publication_and_reopen(tmp_path):
    root = tmp_path / "objects"
    store = ArtifactStore(root)
    with ThreadPoolExecutor(max_workers=4) as pool:
        digests = list(pool.map(store.publish, [b"same bytes"] * 12))
    assert len(set(digests)) == 1
    assert ArtifactStore(root).read(digests[0]) == b"same bytes"
    assert [p.name for p in root.iterdir()] == [digests[0]]
    assert store.audit(digests).missing == ()


@pytest.mark.parametrize("window", ["before_link", "after_link"])
def test_process_crash_during_publication(tmp_path, window):
    root = tmp_path / "objects"
    code = """
import os, sys
from gflo.artifacts import ArtifactStore
store = ArtifactStore(sys.argv[1])
link = os.link
def crash(*args, **kwargs):
    if sys.argv[2] == "after_link":
        link(*args, **kwargs)
    os._exit(23)
os.link = crash
store.publish(b"survives")
"""
    result = subprocess.run([sys.executable, "-c", code, str(root), window])
    assert result.returncode == 23
    store = ArtifactStore(root)
    digest = hashlib.sha256(b"survives").hexdigest()
    audit = store.audit([])
    assert len(audit.staging) == 1
    if window == "before_link":
        assert audit.unreferenced == ()
        with pytest.raises(ArtifactError):
            store.read(digest)
    else:
        assert audit.unreferenced == (digest,)
        assert store.read(digest) == b"survives"
    # Retry safely publishes/verifies the same object; audit preserves the crash evidence.
    assert store.publish(b"survives") == digest
    assert store.audit([digest]).staging == audit.staging


def test_corruption_missing_and_orphans_are_reported_without_mutation(tmp_path):
    store = ArtifactStore(tmp_path / "objects")
    corrupt = store.publish(b"original")
    orphan = store.publish(b"uncommitted")
    path = store.root / corrupt
    path.chmod(0o600)
    path.write_bytes(b"broken")
    missing = "0" * 64
    audit = store.audit([corrupt, missing])
    assert audit.corrupt == (corrupt,)
    assert audit.missing == (missing,)
    assert audit.unreferenced == (orphan,)
    with pytest.raises(ArtifactError):
        store.publish(b"original")
    assert path.read_bytes() == b"broken"
    assert store.read(orphan) == b"uncommitted"


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo"])
def test_nonregular_objects_rejected_without_following_or_blocking(tmp_path, kind):
    store = ArtifactStore(tmp_path / "objects")
    digest = hashlib.sha256(b"external").hexdigest()
    path = store.root / digest
    if kind == "symlink":
        target = tmp_path / "external"
        target.write_bytes(b"external")
        path.symlink_to(target)
    elif kind == "directory":
        path.mkdir()
    else:
        os.mkfifo(path)
    with pytest.raises(ArtifactError):
        store.read(digest)
    assert store.audit([digest]).corrupt == (digest,)


@pytest.mark.parametrize("digest", ["../escape", "A" * 64, "a" * 63, "a" * 64 + "\n"])
def test_bad_digest_rejected(tmp_path, digest):
    with pytest.raises(ArtifactError):
        ArtifactStore(tmp_path / "objects").read(digest)
