"""Definition navigation binds source, scope, analyzer and explicit coverage."""

import json

import pytest

from gflo.artifacts import ArtifactStore
from gflo.broker import SourceBundle
from gflo.repository import FileEdit, Repository, RepositoryError, SnapshotSource, snapshot_bundle
from gflo.symbols import SymbolIndex, build_symbols, query_symbols, read_symbol


def repository(store, files):
    return Repository(SnapshotSource(store, snapshot_bundle(store, SourceBundle(files=files))))


def test_definitions_nested_async_duplicate_and_source_read(tmp_path):
    store = ArtifactStore(tmp_path)
    repo = repository(
        store,
        {
            "a.py": (
                "class A:\n def value(self):\n  async def nested(): pass\n"
                "  return 1\n\ndef value(): pass\n"
            ),
            "b.txt": "def fake(): pass\n",
        },
    )
    index = build_symbols(repo, store)
    values = query_symbols(repo, store, index.index_digest, "value")
    assert values.complete and len(values.hits) == 2
    assert [h.definition.qualified_name for h in values.hits] == ["A.value", "value"]
    nested = query_symbols(repo, store, index.index_digest, "A.value.nested")
    assert nested.hits[0].definition.kind == "async-function"
    assert read_symbol(repo, nested.hits[0]).content == "  async def nested(): pass\n"
    assert not query_symbols(repo, store, index.index_digest, "fake").hits
    limited = query_symbols(repo, store, index.index_digest, "value", max_hits=1)
    assert limited.truncated and not limited.complete
    assert query_symbols(repo, store, index.index_digest, "missing").complete


@pytest.mark.parametrize(
    "kwargs,reason", [({"max_files": 1}, "file-budget"), ({"max_bytes": 20}, "byte-budget")]
)
def test_partial_coverage_cannot_prove_absence(tmp_path, kwargs, reason):
    store = ArtifactStore(tmp_path)
    repo = repository(store, {"a.py": "def first(): pass\n", "b.py": "def second(): pass\n"})
    index = build_symbols(repo, store, **kwargs)
    result = query_symbols(repo, store, index.index_digest, "second")
    assert not result.complete and result.skipped == {"b.py": reason}
    assert result.eligible_files == 2 and result.indexed_files == 1


def test_syntax_error_and_unchanged_reuse(tmp_path):
    store = ArtifactStore(tmp_path)
    repo = repository(
        store, {"a.py": "def value(): pass\n", "bad.py": "def !", "data.txt": "unchanged"}
    )
    first = build_symbols(repo, store)
    assert first.parsed_files == 1 and first.skipped_files == 1
    second = build_symbols(repo, store, prior_digest=first.index_digest)
    assert second.index_digest == first.index_digest
    assert second.parsed_files == 0 and second.reused_files == 1
    assert query_symbols(repo, store, first.index_digest, "absent").skipped == {
        "bad.py": "parse-error"
    }
    new_source = repo.apply(
        store,
        {
            "bad.py": FileEdit(
                expected_digest=repo.source.files["bad.py"].content_digest,
                content="def fixed(): pass\n",
            )
        },
        current_source=repo.source.ref,
        writable_paths=("bad.py",),
    )
    new_repo = Repository(SnapshotSource(store, new_source))
    third = build_symbols(new_repo, store, prior_digest=first.index_digest)
    assert third.parsed_files == 1 and third.reused_files == 1 and third.skipped_files == 0
    assert query_symbols(new_repo, store, third.index_digest, "fixed").complete
    with pytest.raises(RepositoryError, match="another source"):
        query_symbols(new_repo, store, first.index_digest, "value")
    old_hit = query_symbols(repo, store, first.index_digest, "value").hits[0]
    with pytest.raises(RepositoryError, match="another source"):
        read_symbol(new_repo, old_hit)


def test_scope_and_coverage_forgery_rejected(tmp_path):
    store = ArtifactStore(tmp_path)
    repo = repository(
        store, {"a.py": "def value(): pass\n", "private/b.py": "def secret(): pass\n"}
    )
    narrow = Repository(repo.source, scopes=("a.py",))
    index = build_symbols(narrow, store)
    assert query_symbols(narrow, store, index.index_digest, "secret").complete
    with pytest.raises(RepositoryError, match="another scope"):
        query_symbols(repo, store, index.index_digest, "secret")
    data = json.loads(store.read(index.index_digest))
    data["files"] = {}
    forged = store.publish(json.dumps(data).encode())
    with pytest.raises(RepositoryError, match="coverage"):
        query_symbols(narrow, store, forged, "value")


def test_changed_file_does_not_reuse_old_symbols(tmp_path):
    store = ArtifactStore(tmp_path)
    repo = repository(store, {"a.py": "def old(): pass\n"})
    index = build_symbols(repo, store)
    new_source = repo.apply(
        store,
        {
            "a.py": FileEdit(
                expected_digest=repo.source.files["a.py"].content_digest,
                content="def new(): pass\n",
            )
        },
        current_source=repo.source.ref,
        writable_paths=("a.py",),
    )
    changed = Repository(SnapshotSource(store, new_source))
    updated = build_symbols(changed, store, prior_digest=index.index_digest)
    assert updated.reused_files == 0 and updated.parsed_files == 1
    assert not query_symbols(changed, store, updated.index_digest, "old").hits
    assert len(query_symbols(changed, store, updated.index_digest, "new").hits) == 1
    prior = SymbolIndex.model_validate_json(store.read(index.index_digest))
    data = json.loads(store.read(updated.index_digest))
    data["files"] = prior.files
    forged = store.publish(json.dumps(data).encode())
    with pytest.raises(RepositoryError, match="shard differs"):
        query_symbols(changed, store, forged, "old")


def test_reuse_respects_admission_budget_without_reading_source(tmp_path, monkeypatch):
    store = ArtifactStore(tmp_path)
    repo = repository(store, {"a.py": "def a(): pass\n", "b.py": "def b(): pass\n"})
    index = build_symbols(repo, store)

    def forbidden(path):
        raise AssertionError("Unchanged source should reuse analysis")

    monkeypatch.setattr(repo.source, "read_bytes", forbidden)
    reused = build_symbols(repo, store, prior_digest=index.index_digest, max_files=1)
    assert reused.reused_files == 1 and reused.skipped_files == 1
    assert not query_symbols(repo, store, reused.index_digest, "b").complete


def test_large_and_many_definition_files_are_explicitly_skipped(tmp_path):
    store = ArtifactStore(tmp_path)
    repo = repository(store, {"a.py": "pass\n"})
    ref = repo.apply(
        store,
        {
            "large.py": FileEdit(expected_digest=None, content="#" + "x" * 524288),
            "many.py": FileEdit(expected_digest=None, content="def same(): pass\n" * 1001),
        },
        current_source=repo.source.ref,
        writable_paths=("large.py", "many.py"),
    )
    changed = Repository(SnapshotSource(store, ref))
    index = build_symbols(changed, store)
    result = query_symbols(changed, store, index.index_digest, "same")
    assert result.skipped == {"large.py": "parse-byte-budget", "many.py": "analysis-budget"}
    assert not result.hits and not result.complete


def test_cli_build_and_query(tmp_path, monkeypatch, capsys):
    from gflo.cli import main

    store = ArtifactStore(tmp_path / "artifacts")
    repo = repository(store, {"a.py": "def hello(): pass\n"})
    prefix = ["gflo", "repository", "--store", str(store.root)]
    monkeypatch.setattr("sys.argv", prefix + ["index-symbols", repo.source.ref.artifact_digest])
    assert main() == 0
    index = json.loads(capsys.readouterr().out)["index_digest"]
    monkeypatch.setattr(
        "sys.argv", prefix + ["symbols", repo.source.ref.artifact_digest, index, "hello"]
    )
    assert main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["complete"] and result["hits"][0]["path"] == "a.py"
