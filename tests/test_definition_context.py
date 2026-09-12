"""Failed-call hints supply bounded source without granting authority."""

import json
from pathlib import Path

import pytest
from test_worker import prepared as prepared

from gflo.broker import SourceBundle
from gflo.windows import WindowRead, parse_window_result, window_view
from gflo.worker import Diagnostic, InputSnapshot, WorkerError


def project(prepared, files, text, *, enabled=True, reads=(), **changes):
    store, atom, _, _ = prepared
    source = SourceBundle(files=files)
    digest = store.publish(source.canonical().encode())
    atom = atom.model_copy(
        update={
            "inputs_digest": InputSnapshot(
                source_digest=digest, source_revision=atom.source_revision
            ).digest(),
            **changes,
        }
    )
    diagnostic = Diagnostic(source_digest=digest, text=text)
    view, targets = window_view(
        store,
        atom,
        digest,
        source,
        selected_paths=(),
        reads=reads,
        diagnostic_digests=(store.publish(diagnostic.canonical().encode()),),
        definition_context=enabled,
    )
    return view, targets, atom, source


def test_retained_failed_callee_is_visible_only_with_opt_in(prepared):
    fixture = json.loads(
        (
            Path(__file__).parents[1] / ".scratch/local-lights-out-factory/"
            "definition-grounding/fixture.json"
        ).read_text()
    )
    files = {
        "game_server/state/recorderdb.py": fixture["provider"],
        "tests/test_atomic_moves.py": fixture["caller"],
    }
    old, _, _, _ = project(prepared, files, fixture["diagnostic"], enabled=False)
    assert "def createPlayer(" not in "\n".join(old.source_files.values())
    assert "definition_context" not in old.instruction
    view, targets, atom, source = project(prepared, files, fixture["diagnostic"])
    assert "def createPlayer(" in "\n".join(view.source_files.values())
    assert "def createGame(" not in "\n".join(view.source_files.values())
    assert view.instruction["definition_context"]["hints"][0]["status"] == "shown"
    handle = next(h for h, t in targets.targets.items() if t.path.endswith("recorderdb.py"))
    with pytest.raises(WorkerError, match="read-only"):
        parse_window_result(
            json.dumps(
                {
                    "kind": "repair_window",
                    "edits": [{"target": handle, "old": "playerName", "new": "name"}],
                }
            ),
            atom,
            source,
            targets,
        )


API = "class Service:\n    def send(self, payload):\n        return payload\n"
ERROR = "TypeError: Service.send() takes 2 positional arguments but 3 were given"


@pytest.mark.parametrize(
    "extra,changes,status",
    [
        ({}, {}, "shown"),
        ({"duplicate.py": API}, {}, "ambiguous"),
        ({"broken.py": "def invalid("}, {}, "partial-index"),
        ({}, {"prohibited_paths": ("api.py",)}, "missing"),
        ({}, {"allowed_tools": ("edit",)}, "read-not-authorized"),
    ],
)
def test_generic_hints_do_not_expand_authority(prepared, extra, changes, status):
    view, _, _, _ = project(
        prepared, {"api.py": API, "allowed.txt": "context", **extra}, ERROR, **changes
    )
    assert view.instruction["definition_context"]["hints"][0]["status"] == status
    assert bool(view.source_files) == (status == "shown")


def test_multiple_hints_are_bounded_and_rebound_to_current_source(prepared):
    files = {
        "api.py": API + "\n".join(f"class C{i}:\n    def call(self): pass\n" for i in range(6))
    }
    text = ERROR + "\n" + "\n".join(f"TypeError: C{i}.call() failed" for i in range(6))
    view, targets, _, _ = project(prepared, files, text)
    assert len(view.instruction["definition_context"]["hints"]) == 4
    assert view.instruction["definition_context"]["truncated"]
    assert len(targets.targets) == 2
    fresh, fresh_targets, _, _ = project(
        prepared, {"api.py": API.replace("payload", "message")}, ERROR
    )
    assert "message" in "\n".join(fresh.source_files.values())
    assert targets.source_digest != fresh_targets.source_digest
    missing, _, _, _ = project(prepared, {"api.py": API}, "TypeError: Other.call() failed")
    assert missing.instruction["definition_context"]["hints"][0]["status"] == "missing"


def test_explicit_reads_win_when_definition_window_exhausts_bytes(prepared):
    files = {"api.py": API}
    files.update({f"read{i}.txt": "x" * 3998 + "\n" for i in range(3)})
    view, targets, _, _ = project(
        prepared,
        files,
        ERROR,
        reads=tuple(WindowRead(path=f"read{i}.txt", start_line=1) for i in range(3)),
    )
    assert {t.path for t in targets.targets.values()} == {f"read{i}.txt" for i in range(3)}
    assert view.instruction["definition_context"]["hints"][0]["status"] == "omitted"
    assert view.instruction["window_omissions"]
    assert len(targets.targets) <= 8
    assert sum(len(s.encode()) for s in view.source_files.values()) <= 12000


def test_definition_hints_share_count_limit_with_callers_headers_and_explicit_reads(prepared):
    from gflo.worker import Diagnostic

    store, atom, _, _ = prepared
    source = SourceBundle(
        files={
            "main.py": "# header\n" * 80 + API,
            "helper.py": "# header\n" * 80 + API.replace("Service", "Other"),
            "a.txt": "context\n" * 100,
            "b.txt": "context\n" * 100,
        }
    )
    digest = store.publish(source.canonical().encode())
    atom = atom.model_copy(
        update={
            "inputs_digest": InputSnapshot(
                source_digest=digest, source_revision=atom.source_revision
            ).digest()
        }
    )
    diagnostic = Diagnostic(
        source_digest=digest,
        text="main.py:50: " + ERROR + "\nhelper.py:50: TypeError: Other.send() failed",
    )
    explicit = tuple(WindowRead(path=p, start_line=70, max_lines=1) for p in source.files)
    view, targets = window_view(
        store,
        atom,
        digest,
        source,
        selected_paths=tuple(source.files),
        reads=explicit,
        diagnostic_digests=(store.publish(diagnostic.canonical().encode()),),
        definition_context=True,
    )
    assert len(targets.targets) == 8
    assert {(t.path, t.start_line) for t in targets.targets.values() if t.start_line == 70} == {
        (p, 70) for p in source.files
    }
    assert all(h["status"] == "shown" for h in view.instruction["definition_context"]["hints"])
    assert len(view.instruction["window_omissions"]) == 4
    assert all(
        o["reason"] == "Source window count budget exhausted"
        for o in view.instruction["window_omissions"]
    )
