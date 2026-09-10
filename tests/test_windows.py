"""Window edits preserve unseen source and retain ordinary acceptance checks."""

import json

import pytest
from test_controller import plan as plan
from test_controller import setup
from test_preparation import inputs as inputs
from test_worker import prepared as prepared
from test_worker import server as server

from gflo.broker import SourceBundle
from gflo.ledger import WorkLedger
from gflo.windows import WINDOW_PROFILE, WindowRead, parse_window_result, window_view
from gflo.worker import CandidateResult, WorkerError


def edit(handle, old="broken", new="fixed"):
    return json.dumps(dict(kind="repair_window", edits=[dict(target=handle, old=old, new=new)]))


def test_range_binding_preserves_duplicate_text_elsewhere_and_crlf(prepared):
    store, atom, _, _ = prepared
    source = SourceBundle(
        files={"main.py": "# λ\r\nx='broken'\r\ny='broken'\r\n", "helper.py": "hidden"}
    )
    from gflo.worker import InputSnapshot

    atom = atom.model_copy(
        update={
            "inputs_digest": InputSnapshot(
                source_digest=source.digest(), source_revision=atom.source_revision
            ).digest()
        }
    )
    digest = store.publish(source.canonical().encode())
    view, targets = window_view(
        store,
        atom,
        digest,
        source,
        selected_paths=(),
        reads=(WindowRead(path="main.py", start_line=2, max_lines=1),),
    )
    handle = next(iter(targets.targets))
    assert view.source_files[handle] == "x='broken'\r\n"
    result = parse_window_result(edit(handle), atom, source, targets)
    assert result.changes == {"main.py": "# λ\r\nx='fixed'\r\ny='broken'\r\n"}
    with pytest.raises(WorkerError, match="inside its visible window"):
        parse_window_result(edit(handle, old="y='broken'"), atom, source, targets)
    changed = source.model_copy(update={"files": {**source.files, "helper.py": "advanced"}})
    with pytest.raises(WorkerError, match="different contract or draft"):
        parse_window_result(edit(handle), atom, changed, targets)
    with pytest.raises(WorkerError, match="different contract or draft"):
        parse_window_result(
            edit(handle), atom.model_copy(update={"atom_id": "new"}), source, targets
        )
    _, fresh = window_view(store, atom, digest, source, selected_paths=("main.py",))
    with pytest.raises(WorkerError, match="Unknown"):
        parse_window_result(edit(handle), atom, source, fresh)


def test_scope_overlap_and_whole_file_replacements_are_rejected(prepared):
    store, atom, source, digest = prepared
    view, targets = window_view(
        store, atom, digest, source, selected_paths=("main.py", "helper.py")
    )
    writable = next(k for k, t in targets.targets.items() if t.path == "main.py")
    readonly = next(k for k, t in targets.targets.items() if t.path == "helper.py")
    with pytest.raises(WorkerError, match="read-only"):
        parse_window_result(edit(readonly, "value", "other"), atom, source, targets)
    data = json.loads(edit(writable))
    data["edits"] *= 2
    with pytest.raises(WorkerError, match="overlap"):
        parse_window_result(json.dumps(data), atom, source, targets)
    with pytest.raises(WorkerError, match="exact edits"):
        parse_window_result(
            CandidateResult(kind="candidate", changes={"main.py": "pass"}).canonical(),
            atom,
            source,
            targets,
        )
    with pytest.raises(ValueError):
        parse_window_result(
            WindowRead(path="private/test.py", start_line=1).canonical(), atom, source, targets
        )
    assert "secret validator" not in view.canonical()


def test_large_file_projection_is_bounded_and_navigable(prepared):
    from gflo.worker import InputSnapshot

    store, atom, _, _ = prepared
    text = "".join(f"constant_{i} = {i}\n" for i in range(5000))
    text += "def chosen_value():\n    return 41\n"
    text += "".join(f"constant_{i} = {i}\n" for i in range(5000, 10000))
    source = SourceBundle(files={"main.py": text})
    digest = store.publish(source.canonical().encode())
    atom = atom.model_copy(
        update={
            "inputs_digest": InputSnapshot(
                source_digest=digest, source_revision=atom.source_revision
            ).digest()
        }
    )
    view, _ = window_view(store, atom, digest, source)
    assert len(view.canonical().encode()) < 12000
    assert view.instruction["definitions"][0]["line"] == 5001
    assert "constant_9999" not in view.canonical()
    view, targets = window_view(
        store,
        atom,
        digest,
        source,
        reads=(WindowRead(path="main.py", start_line=5001, max_lines=2),),
    )
    handle = next(k for k, t in targets.targets.items() if t.start_line == 5001)
    result = parse_window_result(edit(handle, "return 41", "return 42"), atom, source, targets)
    assert result.changes["main.py"] == text.replace("return 41", "return 42")


def test_controller_advances_window_read_then_runs_complete_gates(tmp_path, plan):
    plan = plan.model_copy(
        update={
            "model_profile": plan.model_profile.model_copy(update={"profile_id": WINDOW_PROFILE})
        }
    )
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(
            ledger,
            plan,
            [
                WindowRead(path="helper.py", start_line=1, max_lines=1),
                CandidateResult(kind="candidate", changes={"main.py": "print(42)"}),
            ],
        )
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "accepted"
        assert model.calls[1]["window_reads"][0].path == "helper.py"
        assert broker.calls == 3
        assert controller.run(plan.atom.atom_id) == result and len(model.calls) == 2


def test_model_tokenizes_only_windows_and_retains_target_binding(prepared, server):
    from test_worker import client_for

    from gflo.model import LocalModel
    from gflo.windows import WindowTargets

    store, atom, source, digest = prepared
    client = client_for(prepared, server)
    client = LocalModel(store, client.profile.model_copy(update={"profile_id": WINDOW_PROFILE}))

    def mutate(response):
        view = json.loads(server[0]["calls"][-1][1]["messages"][1]["content"])
        handle = next(
            k for k, t in view["instruction"]["source_windows"].items() if t["path"] == "main.py"
        )
        response["choices"][0]["message"]["content"] = edit(handle)
        return response

    server[0]["mutate"] = mutate
    result = client.turn(atom, digest, current_inputs=lambda: atom.inputs_digest)
    assert result.result.changes == {"main.py": "print('fixed')\n"}
    assert server[0]["calls"][1][1]["messages"] == server[0]["calls"][-1][1]["messages"]
    evidence = json.loads(store.read(client.last_evidence_digest))
    targets = WindowTargets.model_validate_json(store.read(evidence["window_targets_digest"]))
    assert targets.source_digest == source.digest() and targets.contract_digest == atom.digest()
    assert "repair_handle" not in server[0]["calls"][-1][1]["messages"][0]["content"]


def test_prepared_window_context_preserves_full_execution_source(inputs):
    from gflo.contracts import InterfaceBundle
    from gflo.preparation import prepare_task
    from gflo.repository import snapshot_bundle
    from gflo.windows import WindowContext

    store, request, proposal, review = inputs
    source = snapshot_bundle(
        store, SourceBundle(files={"main.py": "x=1\n" * 20000, "helper.py": "ANSWER=42"})
    )
    request = request.model_copy(update={"source": source})
    task = proposal.tasks[0].model_copy(
        update={"interface_contracts": (InterfaceBundle(declarations=()).canonical(),)}
    )
    proposal = proposal.model_copy(update={"request_digest": request.digest(), "tasks": (task,)})
    review = review.model_copy(
        update={
            "request_digest": request.digest(),
            "proposal_digest": proposal.digest(),
            "model_profile": review.model_profile.model_copy(update={"profile_id": WINDOW_PROFILE}),
        }
    )
    package = prepare_task(store, request, proposal, review, "main", current_source=source)
    assert isinstance(package.context, WindowContext)
    assert package.context.max_source_bytes == 12000
    assert len(package.run.source.files["main.py"]) == 80000


def test_oversized_line_is_explicitly_omitted_and_later_window_is_readable(prepared):
    from gflo.worker import InputSnapshot

    store, atom, _, _ = prepared
    source = SourceBundle(files={"main.py": "#" + "x" * 5000 + "\nvalue = 41\n"})
    digest = store.publish(source.canonical().encode())
    atom = atom.model_copy(
        update={
            "inputs_digest": InputSnapshot(
                source_digest=digest, source_revision=atom.source_revision
            ).digest()
        }
    )
    view, targets = window_view(store, atom, digest, source)
    assert not targets.targets
    assert view.instruction["window_omissions"][0]["path"] == "main.py"
    assert "x" * 100 not in view.canonical()
    view, targets = window_view(
        store, atom, digest, source, reads=(WindowRead(path="main.py", start_line=2, max_lines=1),)
    )
    handle = next(iter(targets.targets))
    result = parse_window_result(edit(handle, "41", "42"), atom, source, targets)
    assert result.changes["main.py"] == source.files["main.py"].replace("41", "42")


def test_planning_window_wire_supports_reads_and_direct_documents(prepared, server):
    from test_worker import client_for

    from gflo.model import LocalModel

    store, atom, _, digest = prepared
    atom = atom.model_copy(update={"writable_paths": ("factory-plan.json",)})
    original = client_for(prepared, server)
    client = LocalModel(store, original.profile.model_copy(update={"profile_id": WINDOW_PROFILE}))
    document = {"kind": "planning-questions-v1", "questions": ["Required policy?"]}
    for payload in [dict(kind="read_window", path="main.py", start_line=1), document]:

        def mutate(response):
            response["choices"][0]["message"]["content"] = json.dumps(payload)
            return response

        server[0]["mutate"] = mutate
        turn = client.turn(
            atom, digest, current_inputs=lambda: atom.inputs_digest, planning_document=True
        )
        if payload is document:
            assert json.loads(turn.result.changes["factory-plan.json"]) == document
        else:
            assert isinstance(turn.result, WindowRead)
        messages = server[0]["calls"][-1][1]["messages"]
        assert "repair_window" not in messages[0]["content"]
        view = json.loads(messages[1]["content"])
        assert all(
            not target["writable"] for target in view["instruction"]["source_windows"].values()
        )


def test_window_output_truncation_is_retryable_without_accepting_partial_text(prepared, server):
    from test_worker import client_for

    from gflo.model import LocalModel, ModelError

    store, atom, _, digest = prepared
    old = client_for(prepared, server)
    client = LocalModel(store, old.profile.model_copy(update={"profile_id": WINDOW_PROFILE}))

    def mutate(response):
        response["choices"][0]["finish_reason"] = "length"
        response["choices"][0]["message"]["content"] = '{"kind":"candidate"'
        return response

    server[0]["mutate"] = mutate
    with pytest.raises(WorkerError, match="No partial output was applied"):
        client.turn(atom, digest, current_inputs=lambda: atom.inputs_digest)
    assert client.last_evidence_digest
    with pytest.raises(ModelError, match="Incomplete or unsupported"):
        old.turn(atom, digest, current_inputs=lambda: atom.inputs_digest)


def test_repeated_invalid_window_output_exhausts_existing_attempts(tmp_path, plan):
    plan = plan.model_copy(
        update={
            "model_profile": plan.model_profile.model_copy(update={"profile_id": WINDOW_PROFILE})
        }
    )
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, _ = setup(
            ledger, plan, [WorkerError("output exceeded"), WorkerError("output exceeded")]
        )
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "quarantined"
        assert len(result["attempts"]) == 2 and len(model.calls) == 2
        assert controller.run(plan.atom.atom_id) == result


def test_planning_windows_label_text_without_losing_source_identity(prepared):
    from gflo.windows import planning_window_view

    store, atom, source, digest = prepared
    atom = atom.model_copy(update={"writable_paths": ("factory-plan.json",)})
    view, _ = window_view(store, atom, digest, source)
    labeled = planning_window_view(view)
    assert labeled.source_files["main.py:1-1"] == source.files["main.py"]
    assert labeled.sources == view.sources
    assert labeled.omission_reasons == view.omission_reasons
    assert labeled.contract_digest == view.contract_digest


def test_task_created_draft_replacement_preserves_original_authority(prepared):
    store, atom, base, digest = prepared
    atom = atom.model_copy(update={"writable_paths": ("main.py", "tests")})
    draft = SourceBundle(files=base.files | {"tests/test_new.py": "def test_new()\n    pass\n"})
    view, targets = window_view(store, atom, digest, draft)
    assert view.instruction["task_created_paths"] == ["tests/test_new.py"]
    candidate = CandidateResult(
        kind="candidate", changes={"tests/test_new.py": "def test_new():\n    pass\n"}
    )
    assert (
        parse_window_result(candidate.canonical(), atom, draft, targets, base_source=base)
        == candidate
    )
    # Legacy callers do not acquire new authority implicitly.
    with pytest.raises(WorkerError, match="exact edits"):
        parse_window_result(candidate.canonical(), atom, draft, targets)
    for changes in ({"main.py": "pass\n"}, candidate.changes | {"main.py": "pass\n"}):
        with pytest.raises(WorkerError, match="exact edits"):
            parse_window_result(
                CandidateResult(kind="candidate", changes=changes).canonical(),
                atom,
                draft,
                targets,
                base_source=base,
            )
    with pytest.raises(WorkerError, match="bind contract inputs"):
        parse_window_result(candidate.canonical(), atom, draft, targets, base_source=draft)
    with pytest.raises(WorkerError, match="different contract or draft"):
        parse_window_result(candidate.canonical(), atom, base, targets, base_source=base)
    with pytest.raises(WorkerError, match="outside granted"):
        parse_window_result(
            CandidateResult(kind="candidate", changes={"outside.py": "pass\n"}).canonical(),
            atom,
            draft,
            targets,
            base_source=base,
        )


@pytest.mark.parametrize(
    "location",
    [
        "tests/test_new.py:135: AssertionError: wrong index",
        '  File "tests/test_new.py", line 135, in test_recovery',
        "AssertionError: ('candidate', 'trace\\ntests/test_new.py:135: AssertionError\\n')",
    ],
)
def test_failure_location_exposes_current_new_draft_for_exact_repair(prepared, location):
    from gflo.worker import Diagnostic

    store, atom, base, digest = prepared
    atom = atom.model_copy(update={"writable_paths": ("main.py", "tests")})
    lines = [f"# line {i}\n" for i in range(1, 201)]
    lines[134] = "assert row_index == 1\n"
    draft = SourceBundle(files=base.files | {"tests/test_new.py": "".join(lines)})
    diagnostic = Diagnostic(source_digest=store.publish(b"failure evidence"), text=location)
    diagnostic_digest = store.publish(diagnostic.canonical().encode())
    view, targets = window_view(
        store,
        atom,
        digest,
        draft,
        selected_paths=("main.py",),
        diagnostic_digests=(diagnostic_digest,),
    )
    handle = next(h for h, t in targets.targets.items() if t.path == "tests/test_new.py")
    assert "assert row_index == 1" in view.source_files[handle]
    assert len(view.source_files[handle].splitlines()) <= 25
    repaired = parse_window_result(
        edit(handle, "assert row_index == 1", "assert row_index == 0"),
        atom,
        draft,
        targets,
        base_source=base,
    )
    assert repaired.changes["tests/test_new.py"] == draft.files["tests/test_new.py"].replace(
        "assert row_index == 1", "assert row_index == 0"
    )


def test_failure_locations_do_not_expand_scope_or_window_budget(prepared):
    from gflo.worker import Diagnostic

    store, atom, base, digest = prepared
    diagnostic = Diagnostic(
        source_digest=store.publish(b"untrusted failure text"),
        text="private/test.py:1: secret\n/etc/passwd:1: secret\n"
        "../main.py:1: secret\nmissing.py:1: missing\nmain.py:999999: invalid\n"
        "main.py:0: invalid\nmain.py:1: AssertionError\nhelper.py:1: AssertionError",
    )
    ref = store.publish(diagnostic.canonical().encode())
    view, targets = window_view(
        store,
        atom,
        digest,
        base,
        selected_paths=(),
        diagnostic_digests=(ref,),
    )
    assert {t.path for t in targets.targets.values()} == {"main.py", "helper.py"}
    assert len(targets.targets) <= 8
    assert sum(len(s.encode()) for s in view.source_files.values()) <= 12000
    assert not any(t.writable for t in targets.targets.values() if t.path == "helper.py")
    no_reads = atom.model_copy(update={"allowed_tools": ("edit",)})
    _, targets = window_view(
        store,
        no_reads,
        digest,
        base,
        selected_paths=(),
        diagnostic_digests=(ref,),
    )
    assert not targets.targets


def test_failure_windows_keep_explicit_reads_and_total_limits(prepared):
    from gflo.worker import Diagnostic, InputSnapshot

    store, atom, _, _ = prepared
    paths = ("main.py", "helper.py", "other.py", "last.py")
    source = SourceBundle(files={p: ("#" + "x" * 169 + "\n") * 100 for p in paths})
    digest = store.publish(source.canonical().encode())
    atom = atom.model_copy(
        update={
            "inputs_digest": InputSnapshot(
                source_digest=digest, source_revision=atom.source_revision
            ).digest()
        }
    )
    diagnostic = Diagnostic(
        source_digest=store.publish(b"trace"), text="main.py:50: failed\nhelper.py:50: failed"
    )
    ref = store.publish(diagnostic.canonical().encode())
    view, targets = window_view(
        store,
        atom,
        digest,
        source,
        selected_paths=paths,
        reads=tuple(WindowRead(path=p, start_line=75, max_lines=1) for p in paths),
        diagnostic_digests=(ref,),
    )
    assert {(t.path, t.start_line) for t in targets.targets.values() if t.start_line == 75} == {
        (p, 75) for p in paths
    }
    assert len(targets.targets) <= 8
    assert sum(len(s.encode()) for s in view.source_files.values()) <= 12000
    assert any(
        o["reason"] == "Source window count budget exhausted"
        for o in view.instruction["window_omissions"]
    )
