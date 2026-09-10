"""Source identity, bounded coverage, and preservation across repository adapters."""

import subprocess

import pytest

from gflo.artifacts import ArtifactError, ArtifactStore
from gflo.broker import SourceBundle
from gflo.repository import (
    BundleSource,
    FileEdit,
    Repository,
    RepositoryError,
    Snapshot,
    SnapshotSource,
    capture_worktree,
    snapshot_bundle,
)


@pytest.fixture
def artifacts(tmp_path):
    return ArtifactStore(tmp_path / "artifacts")


def source(artifacts, files):
    bundle = SourceBundle(files=files)
    return Repository(SnapshotSource(artifacts, snapshot_bundle(artifacts, bundle)))


def test_legacy_bundle_identity_and_selection_parity(artifacts):
    bundle = SourceBundle(files={"a.py": "first\r\nsecond\n", "b.py": "雪 = 1\n"})
    before = bundle.canonical()
    legacy = Repository(BundleSource(bundle))
    captured = source(artifacts, dict(bundle.files))
    assert legacy.source.ref.artifact_digest == bundle.digest()
    assert legacy.source.ref.kind == "source-bundle-v1"
    assert captured.source.ref.kind == "repository-snapshot-v1"
    for repository in (legacy, captured):
        assert repository.select(("a.py", "b.py")).bundle.canonical() == before
        assert repository.read("a.py", start_line=2, max_lines=1).content == "second\n"
        assert repository.read("b.py").content == "雪 = 1\n"
    assert bundle.canonical() == before
    assert artifacts.read(bundle.digest()).decode() == before


def test_search_complete_empty_and_budget_coverage(artifacts):
    repo = source(artifacts, {"a.py": "needle\nneedle\n", "b.py": "last needle\n"})
    empty = repo.search("absent")
    assert empty.complete and empty.searched_files == 2 and not empty.hits
    limited = repo.search("absent", max_files=1)
    assert not limited.complete and limited.reason == "file-budget" and not limited.hits
    limited = repo.search("needle", max_hits=1)
    assert not limited.complete and limited.reason == "hit-budget" and len(limited.hits) == 1
    assert repo.search("needle", max_bytes=1).reason == "byte-budget"
    full = repo.search("needle", max_hits=3)
    assert full.complete and len(full.hits) == 3
    assert repo.read_hit(full.hits[-1]).content == "last needle\n"


def test_stale_hits_and_edits_rejected_and_omitted_files_preserved(artifacts):
    repo = source(artifacts, {"a.py": "needle\n", "unselected.py": "preserve me\n"})
    hit = repo.search("needle").hits[0]
    ref = repo.apply(
        artifacts,
        {"a.py": FileEdit(expected_digest=hit.file_digest, content="new\n")},
        current_source=repo.source.ref,
        writable_paths=("a.py",),
    )
    updated = Repository(SnapshotSource(artifacts, ref))
    assert updated.read("unselected.py").content == "preserve me\n"
    assert updated.source.files["unselected.py"] == repo.source.files["unselected.py"]
    assert repo.read("a.py").content == "needle\n"
    with pytest.raises(RepositoryError, match="another source"):
        updated.read_hit(hit)
    with pytest.raises(RepositoryError, match="advanced"):
        repo.apply(
            artifacts,
            {"a.py": FileEdit(expected_digest=hit.file_digest, content="bad")},
            current_source=ref,
            writable_paths=("a.py",),
        )
    with pytest.raises(RepositoryError, match="Original file"):
        updated.apply(
            artifacts,
            {"a.py": FileEdit(expected_digest=hit.file_digest, content="bad")},
            current_source=ref,
            writable_paths=("a.py",),
        )


@pytest.mark.parametrize("path", ["../secret", "a/../secret", "/secret", "a//b", "a\\b"])
def test_path_aliases_rejected(artifacts, path):
    repo = source(artifacts, {"a.py": "x"})
    with pytest.raises(RepositoryError, match="normalized"):
        repo.read(path)


def test_scope_applies_to_read_search_selection_and_edits(artifacts):
    full = source(artifacts, {"src/a.py": "needle", "private.py": "needle"})
    repo = Repository(full.source, scopes=("src",))
    assert repo.list_paths().paths == ("src/a.py",)
    assert repo.search("needle").eligible_files == 1
    for operation in (
        lambda: repo.read("private.py"),
        lambda: repo.select(("private.py",)),
        lambda: repo.apply(
            artifacts,
            {"private.py": FileEdit(expected_digest=None, content="x")},
            current_source=repo.source.ref,
            writable_paths=("private.py",),
        ),
    ):
        with pytest.raises(RepositoryError, match="scope"):
            operation()


def test_selection_reports_omission_and_execution_refuses_partial(artifacts):
    repo = source(artifacts, {"a.py": "x" * 100, "b.py": "small"})
    selected = repo.select(("a.py", "b.py"), max_bytes=80)
    assert selected.bundle.files == {"b.py": "small"}
    assert selected.omitted == {"a.py": "budget"} and not selected.whole_repository
    with pytest.raises(RepositoryError, match="every explicitly requested"):
        repo.select(("a.py", "b.py"), purpose="execution", max_bytes=80)
    with pytest.raises(RepositoryError, match="absent"):
        repo.select(("missing.py",))
    assert not repo.select(("b.py",), purpose="execution").whole_repository


def test_reads_never_silently_truncate_a_line(artifacts):
    repo = source(artifacts, {"a.py": "雪\nnext\n"})
    with pytest.raises(RepositoryError, match="line exceeds"):
        repo.read("a.py", max_bytes=3)
    read = repo.read("a.py", max_bytes=4)
    assert read.content == "雪\n" and not read.complete and read.end_line == 1


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def worktree(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    (root / "tracked.py").write_text("old\n")
    git(root, "add", "tracked.py")
    return root


def test_capture_dirty_untracked_deleted_and_ignored_files(tmp_path, artifacts):
    root = worktree(tmp_path)
    (root / "tracked.py").write_text("dirty\n")
    (root / "new.py").write_text("new\n")
    (root / ".gitignore").write_text("ignored\n")
    (root / "ignored").write_bytes(b"\0binary")
    ref = capture_worktree(artifacts, root)
    repo = Repository(SnapshotSource(artifacts, ref))
    assert repo.read("tracked.py").content == "dirty\n"
    assert repo.read("new.py").content == "new\n"
    assert "ignored" not in repo.source.files
    assert capture_worktree(artifacts, root) == ref
    (root / "tracked.py").unlink()
    changed = Repository(SnapshotSource(artifacts, capture_worktree(artifacts, root)))
    assert "tracked.py" not in changed.source.files
    assert repo.read("tracked.py").content == "dirty\n"


@pytest.mark.parametrize("kind", ["symlink", "submodule"])
def test_unsupported_capture_inputs_rejected(tmp_path, artifacts, kind):
    root = worktree(tmp_path)
    if kind == "symlink":
        (root / "link.py").symlink_to(tmp_path / "outside")
    else:
        git(root, "update-index", "--add", "--cacheinfo", "160000," + "a" * 40 + ",nested")
    with pytest.raises((RepositoryError, OSError)):
        capture_worktree(artifacts, root)


def test_capture_detects_changes_between_passes(tmp_path, artifacts, monkeypatch):
    import gflo.repository as module

    root = worktree(tmp_path)
    real = module._read_worktree
    calls = 0

    def changing(root, path):
        nonlocal calls
        calls += 1
        if calls == 2:
            (root / path).write_text("changed\n")
        return real(root, path)

    monkeypatch.setattr(module, "_read_worktree", changing)
    with pytest.raises(RepositoryError, match="changed during capture"):
        capture_worktree(artifacts, root)


def test_repository_larger_than_bundle_selects_small_task(tmp_path, artifacts):
    root = worktree(tmp_path)
    for number in range(120):
        (root / f"file-{number:03}.py").write_text("# untouched\n" * 300)
    ref = capture_worktree(artifacts, root)
    repo = Repository(SnapshotSource(artifacts, ref))
    assert len(repo.source.files) == 121
    assert sum(e.size_bytes for e in repo.source.files.values()) > 262144
    selected = repo.select(("tracked.py",), purpose="execution")
    assert selected.bundle.files == {"tracked.py": "old\n"}
    assert len(selected.canonical().encode()) < 2048
    first = repo.list_paths(limit=100)
    second = repo.list_paths(limit=100, after=first.next_after)
    assert not first.complete and second.complete and len(first.paths + second.paths) == 121
    ref2 = repo.apply(
        artifacts,
        {
            "tracked.py": FileEdit(
                expected_digest=repo.source.files["tracked.py"].content_digest, content="edited\n"
            )
        },
        current_source=ref,
        writable_paths=("tracked.py",),
    )
    snapshot = Snapshot.model_validate_json(artifacts.read(ref2.artifact_digest))
    assert len(snapshot.files) == 121
    assert snapshot.files["file-119.py"] == repo.source.files["file-119.py"]


def test_missing_unselected_evidence_prevents_assembly(artifacts):
    repo = source(artifacts, {"a.py": "x", "b.py": "y"})
    (artifacts.root / repo.source.files["b.py"].content_digest).unlink()
    with pytest.raises(ArtifactError):
        repo.apply(
            artifacts,
            {
                "a.py": FileEdit(
                    expected_digest=repo.source.files["a.py"].content_digest, content="z"
                )
            },
            current_source=repo.source.ref,
            writable_paths=("a.py",),
        )


def test_bundle_edit_retains_original_bundle_artifact_and_new_files(artifacts):
    bundle = SourceBundle(files={"old.py": "old"})
    repository = Repository(BundleSource(bundle))
    ref = repository.apply(
        artifacts,
        {"new.py": FileEdit(expected_digest=None, content="new")},
        current_source=repository.source.ref,
        writable_paths=("new.py",),
    )
    assert artifacts.read(bundle.digest()).decode() == bundle.canonical()
    updated = Repository(SnapshotSource(artifacts, ref))
    assert updated.read("old.py").content == "old"
    assert updated.read("new.py").content == "new"
    with pytest.raises(RepositoryError, match="Original file digest"):
        updated.apply(
            artifacts,
            {"new.py": FileEdit(expected_digest=None, content="overwrite")},
            current_source=ref,
            writable_paths=("new.py",),
        )


def test_snapshot_edit_does_not_republish_unchanged_blobs(artifacts, monkeypatch):
    repository = source(artifacts, {"a.py": "x", "b.py": "untouched"})
    published = []
    real = artifacts.publish

    def publish(data):
        published.append(data)
        return real(data)

    monkeypatch.setattr(artifacts, "publish", publish)
    repository.apply(
        artifacts,
        {
            "a.py": FileEdit(
                expected_digest=repository.source.files["a.py"].content_digest, content="z"
            )
        },
        current_source=repository.source.ref,
        writable_paths=("a.py",),
    )
    assert b"untouched" not in published


def test_cli_capture_and_scoped_search_require_no_ledger(tmp_path, monkeypatch, capsys):
    import json
    import sys

    from gflo.cli import main

    root = worktree(tmp_path)
    store = tmp_path / "store"
    monkeypatch.setattr(
        sys, "argv", ["gflo", "repository", "--store", str(store), "capture", str(root)]
    )
    assert main() == 0
    ref = json.loads(capsys.readouterr().out)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "gflo",
            "repository",
            "--store",
            str(store),
            "search",
            ref["artifact_digest"],
            "old",
            "--scope",
            "tracked.py",
        ],
    )
    assert main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["complete"] and result["hits"][0]["path"] == "tracked.py"


@pytest.mark.parametrize("opaque", [b"\0binary", b"\xff\xfe"])
def test_capture_preserves_opaque_files_without_granting_text_access(tmp_path, artifacts, opaque):
    root = worktree(tmp_path)
    (root / "data.db").write_bytes(opaque)
    captured = capture_worktree(artifacts, root)
    repo = Repository(SnapshotSource(artifacts, captured))
    assert repo.source.read_bytes("data.db") == opaque
    with pytest.raises(RepositoryError, match="Binary|UTF-8"):
        repo.read("data.db")
    with pytest.raises(RepositoryError, match="Binary|UTF-8"):
        repo.select(("data.db",), purpose="execution")
    with pytest.raises(RepositoryError, match="Binary|UTF-8"):
        repo.search("needle")
    # Opaque files survive a separate text edit, including their original identity.
    changed = repo.apply(
        artifacts,
        {"new.py": FileEdit(expected_digest=None, content="pass\n")},
        current_source=captured,
        writable_paths=("new.py",),
    )
    result = Repository(SnapshotSource(artifacts, changed))
    assert result.source.files["data.db"] == repo.source.files["data.db"]
    assert result.source.read_bytes("data.db") == opaque


def test_corrupt_omitted_opaque_blob_blocks_unrelated_edit(tmp_path, artifacts):
    root = worktree(tmp_path)
    (root / "asset.bin").write_bytes(b"\0opaque")
    captured = capture_worktree(artifacts, root)
    repo = Repository(SnapshotSource(artifacts, captured))
    (artifacts.root / repo.source.files["asset.bin"].content_digest).unlink()
    with pytest.raises(ArtifactError):
        repo.apply(
            artifacts,
            {"new.py": FileEdit(expected_digest=None, content="pass\n")},
            current_source=captured,
            writable_paths=("new.py",),
        )
