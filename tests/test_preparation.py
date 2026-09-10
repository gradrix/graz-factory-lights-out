"""Reviewed source preparation through real snapshots and the existing run contract."""

import hashlib
import json

import pytest

from gflo.artifacts import ArtifactStore
from gflo.broker import SourceBundle
from gflo.controller import prepare_run
from gflo.ledger import WorkLedger
from gflo.planning import PlanProposal
from gflo.preparation import PlanReview, RepositoryFeatureRequest, lift_candidate, prepare_task
from gflo.repository import Repository, SnapshotSource, SourceRef, snapshot_bundle


@pytest.fixture
def inputs(tmp_path):
    store = ArtifactStore(tmp_path / "artifacts")
    source = snapshot_bundle(
        store,
        SourceBundle(
            files={
                "main.py": "print(0)",
                "helper.py": "ANSWER=42",
                "docs/design.md": "Keep this design",
            }
        ),
    )
    request = RepositoryFeatureRequest.model_validate_json(
        json.dumps(
            dict(
                feature_id="answer",
                objective="Print the answer",
                requirements={"answer": "Print 42"},
                source=source.model_dump(),
                allowed_paths=["main.py"],
                environments={
                    "python": {"image": "sha256:" + "a" * 64, "description": "Pinned Python"}
                },
            )
        )
    )
    proposal = PlanProposal.model_validate_json(
        json.dumps(
            dict(
                request_digest=request.digest(),
                questions=[],
                rationale="One independent task",
                tasks=[
                    dict(
                        task_id="main",
                        objective="Print the answer",
                        requirement_ids=["answer"],
                        depends_on=[],
                        writable_paths=["main.py"],
                        read_paths=["helper.py"],
                        environment_id="python",
                        interface_contracts=["Print ANSWER from helper"],
                        acceptance_checks=["Untrusted suggestion, not a gate"],
                    )
                ],
            )
        )
    )
    review = PlanReview.model_validate_json(
        json.dumps(
            dict(
                request_digest=request.digest(),
                proposal_digest=proposal.digest(),
                tasks={
                    "main": dict(
                        execution_paths=["main.py", "helper.py"],
                        context_paths=["main.py"],
                        gates={
                            "answer": {
                                "cases": [
                                    {"command": ["python", "main.py"], "expected_stdout": "42\n"}
                                ]
                            }
                        },
                    )
                },
                model_profile={
                    "base_url": "http://127.0.0.1:30000/v1",
                    "model": "gflo-local",
                    "deployment_digest": hashlib.sha256(b"fixture").hexdigest(),
                },
                deployment="fixture",
                context_budget={"total_tokens": 8192, "output_tokens": 2048},
            )
        )
    )
    return store, request, proposal, review


def prepare(inputs):
    store, request, proposal, review = inputs
    return prepare_task(store, request, proposal, review, "main", current_source=request.source)


def test_prepare_real_run_and_preserve_omitted_files(inputs, tmp_path):
    store, request, _, review = inputs
    package = prepare(inputs)
    assert not package.execution.whole_repository
    assert package.context.bundle.files == {"main.py": "print(0)"}
    assert package.run.source.files == {"main.py": "print(0)", "helper.py": "ANSWER=42"}
    assert package.run.gates == review.tasks["main"].gates
    assert json.loads(package.run.atom.objective)["requirements"] == {"answer": "Print 42"}
    assert request.source.artifact_digest in package.run.atom.source_revision
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        prepare_run(ledger, package.run)
        assert ledger.status(package.run.atom.atom_id)["status"] == "ready"
    result = lift_candidate(
        store,
        package.digest(),
        SourceBundle(
            files={
                "main.py": "from helper import ANSWER\nprint(ANSWER)",
                "helper.py": "ANSWER=42",
            }
        ),
        current_source=request.source,
    )
    repository = Repository(SnapshotSource(store, result))
    assert repository.read("docs/design.md").content == "Keep this design"
    assert repository.read("main.py").content.endswith("print(ANSWER)")


@pytest.mark.parametrize(
    "change,match",
    [
        ("stale", "advanced"),
        ("review", "Review does not bind"),
        ("questions", "questions"),
        ("missing", "omit declared"),
        ("context", "Context must"),
        ("budget", "Execution selection"),
        ("context_budget", "context exceeds"),
        ("dependent", "accepted-base"),
    ],
)
def test_fail_closed_preparation(inputs, change, match):
    store, request, proposal, review = inputs
    current = request.source
    data = review.model_dump(mode="json")
    if change == "stale":
        current = SourceRef(kind="repository-snapshot-v1", artifact_digest="b" * 64)
    elif change == "review":
        data["proposal_digest"] = "b" * 64
    elif change in ("questions", "dependent"):
        plan = proposal.model_dump(mode="json")
        if change == "questions":
            plan["questions"] = ["Unresolved interface"]
        else:
            other = dict(plan["tasks"][0], task_id="provider", writable_paths=["main.py"])
            plan["tasks"][0]["depends_on"] = ["provider"]
            plan["tasks"].append(other)
            data["tasks"]["provider"] = data["tasks"]["main"]
        proposal = PlanProposal.model_validate_json(json.dumps(plan))
        data["proposal_digest"] = proposal.digest()
    elif change == "missing":
        data["tasks"]["main"]["execution_paths"] = ["main.py"]
    elif change == "context":
        data["tasks"]["main"]["context_paths"] = ["docs/design.md"]
    elif change == "budget":
        data["tasks"]["main"]["execution_bytes"] = 1
    else:
        data["tasks"]["main"]["context_bytes"] = 1
    review = PlanReview.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match=match):
        prepare_task(store, request, proposal, review, "main", current_source=current)


@pytest.mark.parametrize(
    "files,match",
    [
        ({"main.py": "new"}, "deletes"),
        ({"main.py": "new", "helper.py": "changed"}, "scope"),
        ({"main.py": "new", "helper.py": "ANSWER=42", "docs/design.md": "lost"}, "omitted"),
    ],
)
def test_candidate_cannot_escape_or_discard_inputs(inputs, files, match):
    store, request, _, _ = inputs
    package = prepare(inputs)
    with pytest.raises(ValueError, match=match):
        lift_candidate(
            store, package.digest(), SourceBundle(files=files), current_source=request.source
        )


def test_large_repository_not_embedded_in_request_or_run(inputs):
    store, request, proposal, review = inputs
    from gflo.repository import FileEdit

    repository = Repository(SnapshotSource(store, request.source))
    expanded = repository.apply(
        store,
        {"large.txt": FileEdit(expected_digest=None, content="x" * 300000)},
        current_source=request.source,
        writable_paths=("large.txt",),
    )
    req = request.model_dump(mode="json")
    req["source"] = expanded.model_dump(mode="json")
    request = RepositoryFeatureRequest.model_validate_json(json.dumps(req))
    plan = proposal.model_dump(mode="json")
    plan["request_digest"] = request.digest()
    proposal = PlanProposal.model_validate_json(json.dumps(plan))
    rev = review.model_dump(mode="json")
    rev.update(request_digest=request.digest(), proposal_digest=proposal.digest())
    review = PlanReview.model_validate_json(json.dumps(rev))
    package = prepare((store, request, proposal, review))
    assert len(request.canonical()) < 2000
    assert len(package.run.canonical()) < 8000
    assert package.execution.repository_file_count == 4
    assert "large.txt" not in package.run.source.files


def test_review_changes_produce_new_work_identity(inputs):
    first = prepare(inputs)
    store, request, proposal, review = inputs
    data = review.model_dump(mode="json")
    data["tasks"]["main"]["gates"]["answer"]["cases"][0]["expected_stdout"] = "43\n"
    second = prepare((store, request, proposal, PlanReview.model_validate_json(json.dumps(data))))
    assert first.run.atom.atom_id != second.run.atom.atom_id
    assert first.run.atom.inputs_digest == second.run.atom.inputs_digest
    assert first.run.atom.required_gates != second.run.atom.required_gates


def test_lift_rejects_stale_source_and_missing_omitted_evidence(inputs):
    store, request, _, _ = inputs
    package = prepare(inputs)
    candidate = SourceBundle(files={"main.py": "print(42)", "helper.py": "ANSWER=42"})
    with pytest.raises(ValueError, match="advanced"):
        lift_candidate(
            store,
            package.digest(),
            candidate,
            current_source=SourceRef(kind="repository-snapshot-v1", artifact_digest="b" * 64),
        )
    repository = Repository(SnapshotSource(store, request.source))
    digest = repository.source.files["docs/design.md"].content_digest
    (store.root / digest).unlink()
    from gflo.artifacts import ArtifactError

    with pytest.raises(ArtifactError):
        lift_candidate(store, package.digest(), candidate, current_source=request.source)


def test_cli_emits_package_without_submitting(inputs, tmp_path, monkeypatch, capsys):
    from gflo.cli import main

    store, request, proposal, review = inputs
    paths = []
    for name, record in [("request", request), ("proposal", proposal), ("review", review)]:
        path = tmp_path / f"{name}.json"
        path.write_text(record.canonical())
        paths.append(str(path))
    db = tmp_path / "unused.db"
    monkeypatch.setattr(
        "sys.argv",
        [
            "gflo",
            "--db",
            str(db),
            "prepare-task",
            *paths,
            "main",
            "--store",
            str(store.root),
            "--current",
            request.source.artifact_digest,
        ],
    )
    assert main() == 0
    data = json.loads(capsys.readouterr().out)
    assert data["source"] == request.source.model_dump(mode="json")
    assert data["run"]["selected_paths"] == ["main.py"]
    assert not db.exists()


def test_unchanged_candidate_preserves_snapshot_identity(inputs):
    store, request, _, _ = inputs
    package = prepare(inputs)
    assert (
        lift_candidate(store, package.digest(), package.run.source, current_source=request.source)
        == request.source
    )
