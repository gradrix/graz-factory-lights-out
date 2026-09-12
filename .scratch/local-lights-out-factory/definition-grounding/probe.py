"""CPU visibility experiment, not a runtime policy or a model-repair qualification."""

import argparse
import json
import re
import tempfile
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import SourceBundle
from gflo.records import WorkAtom
from gflo.repository import Repository, RepositoryError, SnapshotSource, snapshot_bundle
from gflo.symbols import build_symbols, query_symbols, read_symbol
from gflo.windows import WindowRead, window_view
from gflo.worker import Diagnostic, InputSnapshot, WorkerError

HERE = Path(__file__).resolve().parent


def bridge(repository, store, diagnostic):
    """Resolve only a unique, completely indexed qualified TypeError name.

    Deliberately no receiver inference, adjacent-call prediction or runtime wiring.
    Diagnostic text is only a hint; repository scope and identity remain authority.
    """
    names = re.findall(r"TypeError: ([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)\(\)", diagnostic)
    index = build_symbols(repository, store).index_digest
    reads = []
    for name in dict.fromkeys(names):
        if len(name) > 200:
            continue
        result = query_symbols(repository, store, index, name, max_hits=2)
        if result.complete and len(result.hits) == 1:
            hit = result.hits[0]
            read_symbol(repository, hit, max_lines=25)  # Verify authoritative binding.
            reads.append(
                WindowRead(
                    path=hit.path,
                    start_line=hit.definition.line,
                    max_lines=min(25, hit.definition.end_line - hit.definition.line + 1),
                )
            )
        if len(reads) == 2:
            break
    return tuple(reads)


def run(use_bridge):
    fixture = json.loads((HERE / "fixture.json").read_text())
    with tempfile.TemporaryDirectory() as temporary:
        store = ArtifactStore(Path(temporary) / "artifacts")
        provider = "game_server/state/recorderdb.py"
        caller = "tests/test_atomic_moves.py"
        source = SourceBundle(files={provider: fixture["provider"]})
        base_digest = store.publish(source.canonical().encode())
        current = SourceBundle(files={**source.files, caller: fixture["caller"]})
        fields = json.loads(Path("examples/work-atom.json").read_text())
        fields.update(
            writable_paths=[caller],
            prohibited_paths=[],
            inputs_digest=InputSnapshot(
                source_digest=base_digest, source_revision=fields["source_revision"]
            ).digest(),
        )
        atom = WorkAtom.model_validate_json(json.dumps(fields))
        diagnostic = Diagnostic(source_digest=base_digest, text=fixture["diagnostic"])
        diagnostic_digest = store.publish(diagnostic.canonical().encode())
        repository = Repository(SnapshotSource(store, snapshot_bundle(store, current)))
        hints = bridge(repository, store, diagnostic.text) if use_bridge else ()
        view, targets = window_view(
            store,
            atom,
            base_digest,
            current,
            selected_paths=(provider,),
            diagnostic_digests=(diagnostic_digest,),
            reads=(WindowRead(path=provider, start_line=116, max_lines=60), *hints),
        )
        contents = "\n".join(view.source_files.values())
        assert len(targets.targets) <= 8
        assert sum(len(text.encode()) for text in view.source_files.values()) <= 12000
        assert all(not t.writable for t in targets.targets.values() if t.path == provider)
        assert targets.source_digest == current.digest()
        result = dict(
            bridge=use_bridge,
            windows=len(targets.targets),
            source_bytes=sum(len(text.encode()) for text in view.source_files.values()),
            failed_definition_visible="def createPlayer(" in contents,
            next_definition_visible="def createGame(" in contents,
            indexed_names=[
                d["qualified_name"]
                for d in view.instruction["definitions"]
                if d["name"] in ("createPlayer", "createGame")
            ],
        )
        print(json.dumps(result, sort_keys=True))
        assert result["failed_definition_visible"], (
            "Failed callee definition absent from repair view"
        )

        for restricted in (
            atom.model_copy(update={"allowed_tools": ("edit",)}),
            atom.model_copy(update={"prohibited_paths": (provider,)}),
        ):
            try:
                window_view(store, restricted, base_digest, current, selected_paths=(), reads=hints)
            except WorkerError:
                pass
            else:
                raise AssertionError("Hint bypassed read authority")

        # Generic names, duplicate symbols, incomplete indexing and stale revisions.
        generic = SourceBundle(
            files={
                "api.py": "class Service:\n    def send(self, payload):\n        return payload\n"
            }
        )
        repo = Repository(SnapshotSource(store, snapshot_bundle(store, generic)))
        hint = "TypeError: Service.send() takes 2 positional arguments but 3 were given"
        assert bridge(repo, store, hint)[0].path == "api.py"
        duplicate = SourceBundle(files={**generic.files, "other.py": generic.files["api.py"]})
        assert not bridge(
            Repository(SnapshotSource(store, snapshot_bundle(store, duplicate))), store, hint
        )
        partial = SourceBundle(files={**generic.files, "bad.py": "def invalid("})
        assert not bridge(
            Repository(SnapshotSource(store, snapshot_bundle(store, partial))), store, hint
        )
        scoped = Repository(
            SnapshotSource(store, snapshot_bundle(store, generic)), scopes=("allowed",)
        )
        assert not bridge(scoped, store, hint)
        index = build_symbols(repo, store).index_digest
        hit = query_symbols(repo, store, index, "Service.send").hits[0]
        changed = SourceBundle(
            files={"api.py": generic.files["api.py"].replace("payload", "value")}
        )
        fresh = Repository(SnapshotSource(store, snapshot_bundle(store, changed)))
        try:
            read_symbol(fresh, hit)
        except RepositoryError:
            pass
        else:
            raise AssertionError("Stale definition accepted")
        assert not bridge(repo, store, "TypeError: Unknown.send() failed")
        print("Generic, ambiguity, partial-index, scope and stale-source checks passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", action="store_true")
    run(parser.parse_args().bridge)
