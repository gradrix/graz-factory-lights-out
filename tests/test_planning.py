"""Plans are bounded proposals; structural validity is not execution permission."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from gflo.model import ModelError, ModelProfile
from gflo.planning import FeatureRequest, PlanProposal, draft_feature, validate_proposal
from gflo.worker import CandidateResult, ReadFileRequest


@pytest.fixture
def feature():
    return FeatureRequest.model_validate_json(
        json.dumps(
            {
                "feature_id": "summary",
                "objective": "Summarize retained history",
                "requirements": {"read": "Preserve task warnings", "format": "Show compact output"},
                "source_revision": "fixed-base",
                "source": {"files": {"history.py": "pass", "cli.py": "pass"}},
                "allowed_paths": ["history.py", "cli.py", "tests"],
                "selected_paths": ["history.py"],
                "environments": {
                    "python": {"image": "sha256:" + "a" * 64, "description": "Pinned Python"}
                },
            }
        )
    )


def proposal(feature):
    return {
        "request_digest": feature.digest(),
        "questions": [],
        "rationale": "Provider before consumer",
        "tasks": [
            {
                "task_id": "provider",
                "objective": "Summarize",
                "requirement_ids": ["read"],
                "depends_on": [],
                "writable_paths": ["history.py"],
                "read_paths": ["history.py"],
                "environment_id": "python",
                "interface_contracts": ["summary(data) returns text"],
                "acceptance_checks": ["Warnings retained"],
            },
            {
                "task_id": "cli",
                "objective": "Wire CLI",
                "requirement_ids": ["format"],
                "depends_on": ["provider"],
                "writable_paths": ["cli.py"],
                "read_paths": ["cli.py"],
                "environment_id": "python",
                "interface_contracts": ["Call summary(data)"],
                "acceptance_checks": ["Compact output omits full diffs"],
            },
        ],
    }


def test_dependency_order_and_questions_do_not_authorize_execution(feature):
    data = proposal(feature)
    data["tasks"].reverse()
    data["questions"] = ["Which summary layout is preferred?"]
    plan = PlanProposal.model_validate_json(json.dumps(data))
    assert validate_proposal(feature, plan) == ("provider", "cli")


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda d: d.update(request_digest="b" * 64), "another request"),
        (lambda d: d["tasks"][1].update(task_id="provider"), "Duplicate task"),
        (lambda d: d["tasks"][0].update(depends_on=["cli"]), "Cyclic"),
        (lambda d: d["tasks"][1].update(depends_on=["missing"]), "missing dependency"),
        (lambda d: d["tasks"][1].update(depends_on=["cli"]), "self or missing"),
        (lambda d: d["tasks"][1].update(requirement_ids=["read"]), "no planned task"),
        (lambda d: d["tasks"][1].update(requirement_ids=["unknown"]), "unknown requirement"),
        (lambda d: d["tasks"][1].update(environment_id="network"), "unknown environment"),
        (lambda d: d["tasks"][1].update(read_paths=["missing.py"]), "missing source"),
        (lambda d: d["tasks"][1].update(writable_paths=["../secret"]), "normalized"),
        (lambda d: d["tasks"][1].update(writable_paths=["ledger.py"]), "outside allowed"),
        (
            lambda d: d["tasks"][1].update(writable_paths=["history.py"], depends_on=[]),
            "Overlapping",
        ),
    ],
)
def test_invalid_graphs_rejected(feature, mutation, match):
    data = proposal(feature)
    mutation(data)
    with pytest.raises(ValueError, match=match):
        validate_proposal(feature, PlanProposal.model_validate_json(json.dumps(data)))


def fake_model(monkeypatch, answers):
    instances = []

    class Model:
        def __init__(self, artifacts, profile):
            self.artifacts = artifacts
            self.last_evidence_digest = None
            self.calls = []
            self.atoms = []
            instances.append(self)

        def turn(self, *args, **kwargs):
            self.calls.append(kwargs)
            self.atoms.append(args[0])
            self.last_evidence_digest = self.artifacts.publish(b"observed model call")
            answer = answers.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return SimpleNamespace(result=answer)

    monkeypatch.setattr("gflo.planning.LocalModel", Model)
    return instances


def profile():
    return ModelProfile(
        base_url="http://127.0.0.1:30000/v1",
        model="local",
        deployment_digest=hashlib.sha256(b"fixture").hexdigest(),
    )


def test_reads_then_proposal_retains_evidence_and_refuses_rerun(feature, tmp_path, monkeypatch):
    answer = CandidateResult(
        kind="candidate", changes={"factory-plan.json": json.dumps(proposal(feature))}
    )
    instances = fake_model(monkeypatch, [ReadFileRequest(kind="read_file", path="cli.py"), answer])
    output = tmp_path / "draft"
    result = draft_feature(feature, profile(), output, deployment="fixture")
    assert result["status"] == "needs-review" and result["execution_authorized"] is False
    assert len(result["observations"]) == 2
    assert instances[0].calls[1]["selected_paths"] == ("cli.py", "history.py")
    assert json.loads((output / "result.json").read_text()) == result
    with pytest.raises(FileExistsError):
        draft_feature(feature, profile(), output, deployment="fixture")
    assert len(instances) == 1


def test_invalid_proposals_exhaust_without_acceptance(feature, tmp_path, monkeypatch):
    bad = CandidateResult(kind="candidate", changes={"cli.py": "unapproved source change"})
    instances = fake_model(monkeypatch, [bad, bad])
    result = draft_feature(feature, profile(), tmp_path / "draft", deployment="fixture")
    assert result["status"] == "exhausted" and result["proposal_digest"] is None
    assert len(instances[0].calls) == 2
    assert instances[0].calls[1]["diagnostic_digests"]
    assert not (tmp_path / "draft/proposal.json").exists()


def test_transport_failure_stops_without_retry(feature, tmp_path, monkeypatch):
    instances = fake_model(monkeypatch, [ModelError("offline")])
    with pytest.raises(ModelError):
        draft_feature(feature, profile(), tmp_path / "draft", deployment="fixture")
    assert len(instances[0].calls) == 1
    result = json.loads((tmp_path / "draft/result.json").read_text())
    assert result["status"] == "infrastructure-halt" and len(result["observations"]) == 1


def test_read_window_is_bounded_and_records_eviction(feature, tmp_path, monkeypatch):
    data = json.loads(feature.canonical())
    data["source"]["files"]["notes.md"] = "Local documentation"
    feature = FeatureRequest.model_validate_json(json.dumps(data))
    answer = CandidateResult(
        kind="candidate", changes={"factory-plan.json": json.dumps(proposal(feature))}
    )
    instances = fake_model(
        monkeypatch,
        [
            ReadFileRequest(kind="read_file", path="cli.py"),
            ReadFileRequest(kind="read_file", path="notes.md"),
            answer,
        ],
    )
    result = draft_feature(feature, profile(), tmp_path / "draft", deployment="fixture")
    assert result["status"] == "needs-review"
    assert instances[0].calls[2]["selected_paths"] == ("cli.py", "notes.md")
    assert result["observations"][1]["evicted_path"] == "history.py"


def test_wrong_deployment_rejected_before_creating_run(feature, tmp_path):
    with pytest.raises(ValueError, match="Deployment"):
        draft_feature(feature, profile(), tmp_path / "draft", deployment="different")
    assert not (tmp_path / "draft").exists()


def test_check_plan_cli_requires_no_work_ledger(feature, tmp_path, monkeypatch, capsys):
    import sys

    from gflo.cli import main

    request_file = tmp_path / "request.json"
    proposal_file = tmp_path / "proposal.json"
    request_file.write_text(feature.canonical())
    proposal_file.write_text(json.dumps(proposal(feature)))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "gflo",
            "--db",
            str(tmp_path / "missing.db"),
            "check-plan",
            str(request_file),
            str(proposal_file),
        ],
    )
    assert main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["task_order"] == ["provider", "cli"]
    assert result["execution_authorized"] is False
    assert not (tmp_path / "missing.db").exists()


def test_snapshot_planning_binds_full_source_without_loading_omitted_bytes(
    feature, tmp_path, monkeypatch
):
    from gflo.artifacts import ArtifactStore
    from gflo.planning import RepositoryFeatureRequest
    from gflo.repository import FileEdit, Repository, SnapshotSource, snapshot_bundle

    store = ArtifactStore(tmp_path / "source")
    ref = snapshot_bundle(store, feature.source)
    repo = Repository(SnapshotSource(store, ref))
    ref = repo.apply(
        store,
        {"large.txt": FileEdit(expected_digest=None, content="x" * 300000)},
        current_source=ref,
        writable_paths=("large.txt",),
    )
    fields = feature.model_dump(mode="json")
    fields.pop("selected_paths")
    fields.pop("source_revision")
    fields["source"] = ref.model_dump(mode="json")
    fields["allowed_paths"].append("large.txt")
    request = RepositoryFeatureRequest.model_validate_json(json.dumps(fields))
    data = proposal(feature)
    data["request_digest"] = request.digest()
    instances = fake_model(
        monkeypatch,
        [CandidateResult(kind="candidate", changes={"factory-plan.json": json.dumps(data)})],
    )
    output = tmp_path / "draft"
    result = draft_feature(
        request,
        profile(),
        output,
        deployment="fixture",
        repository=Repository(SnapshotSource(store, ref)),
        context_paths=("history.py", "cli.py"),
    )
    assert result["status"] == "needs-review"
    assert '"large.txt":"existing-file"' in instances[0].atoms[0].objective
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["request_digest"] == request.digest()
    assert manifest["source_coverage"]["whole_repository"] is False
    assert manifest["source_coverage"]["repository_files"] == 3
    assert "large.txt" not in manifest["source_coverage"]["readable_paths"]
    with pytest.raises(ValueError, match="bind the request"):
        draft_feature(
            request,
            profile(),
            tmp_path / "stale",
            deployment="fixture",
            repository=Repository(SnapshotSource(store, snapshot_bundle(store, feature.source))),
            context_paths=("history.py",),
        )


def test_planner_can_request_product_decisions_without_inventing_tasks(
    feature, tmp_path, monkeypatch
):
    from gflo.planning import PlanQuestions

    questions = PlanQuestions(
        request_digest=feature.digest(),
        questions=("Which reporting policy?",),
        rationale="Required policy is not supplied",
    )
    fake_model(
        monkeypatch,
        [CandidateResult(kind="candidate", changes={"factory-plan.json": questions.canonical()})],
    )
    result = draft_feature(feature, profile(), tmp_path / "draft", deployment="fixture")
    assert result["status"] == "needs-info"
    assert result["execution_authorized"] is False
    assert result["proposal_digest"] is None
    assert result["questions"] == ["Which reporting policy?"]
    assert (tmp_path / "draft/questions.json").is_file()
    assert not (tmp_path / "draft/proposal.json").exists()


def test_questions_must_bind_the_current_request(feature, tmp_path, monkeypatch):
    from gflo.planning import PlanQuestions

    questions = PlanQuestions(
        request_digest="b" * 64, questions=("Unbound question?",), rationale="Wrong base"
    )
    answer = CandidateResult(kind="candidate", changes={"factory-plan.json": questions.canonical()})
    fake_model(monkeypatch, [answer, answer])
    result = draft_feature(feature, profile(), tmp_path / "draft", deployment="fixture")
    assert result["status"] == "exhausted"
    assert all("another request" in row["error"] for row in result["observations"])


def test_missing_self_output_identifies_task_path_and_resolution(feature):
    data = proposal(feature)
    data['tasks'][1]['writable_paths'] = ['tests/test_new.py']
    data['tasks'][1]['read_paths'] = ['tests/test_new.py']
    with pytest.raises(ValueError, match="cli.*tests/test_new.py.*only in writable_paths"):
        validate_proposal(feature, PlanProposal.model_validate_json(json.dumps(data)))
    data['tasks'][1]['read_paths'] = ['history.py']
    assert validate_proposal(feature, PlanProposal.model_validate_json(json.dumps(data)))


def test_planner_receives_path_presence_and_input_output_rules(feature, tmp_path, monkeypatch):
    answer = CandidateResult(kind='candidate', changes={
        'factory-plan.json': json.dumps(proposal(feature)),
    })
    instances = fake_model(monkeypatch, [answer])
    draft_feature(feature, profile(), tmp_path / 'draft', deployment='fixture')
    instruction = instances[0].atoms[0].objective
    assert 'only in writable_paths, not its own read_paths' in instruction
    brief = instruction
    assert '"allowed_path_state":{"history.py":"existing-file","cli.py":"existing-file","tests":"absent"}' in brief
