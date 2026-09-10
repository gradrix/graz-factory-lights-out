import json

import pytest
from test_planning import fake_model, profile, proposal
from test_planning import feature as feature

from gflo.planning import PlanQuestions, draft_feature
from gflo.question_grounding import QuestionGrounding
from gflo.worker import CandidateResult


def document(data):
    return CandidateResult(kind="candidate", changes={"factory-plan.json": json.dumps(data)})


def records(feature, quotes=True):
    questions = PlanQuestions(
        request_digest=feature.digest(),
        questions=("Should warnings remain?",),
        rationale="Policy check",
    )
    grounding = dict(
        kind="question-grounding-v1",
        request_digest=feature.digest(),
        questions_digest=questions.digest(),
        dispositions=[
            dict(
                question_index=0,
                quotes=[dict(requirement_id="read", quote=feature.requirements["read"])]
                if quotes
                else [],
            )
        ],
    )
    plan = proposal(feature)
    plan["kind"] = "contract-plan-v1"
    for task in plan["tasks"]:
        task.pop("interface_contracts")
        task.update(interfaces=[], implementation_suggestions=[])
    return questions, grounding, plan


def test_grounded_questions_replan_within_existing_turn_budget(feature, tmp_path, monkeypatch):
    questions, grounding, plan = records(feature)
    models = fake_model(
        monkeypatch,
        [document(json.loads(questions.canonical())), document(grounding), document(plan)],
    )
    result = draft_feature(
        feature, profile(), tmp_path / "plan", deployment="fixture", structured_interfaces=True
    )
    assert result["status"] == "needs-review"
    assert result["questions"] == []
    assert [(o["attempt"], o["turn"]) for o in result["observations"]] == [(1, 1), (1, 2), (1, 3)]
    assert result["questions_digest"] == questions.digest() and result["grounding_digest"]
    assert models[0].calls[1]["selected_paths"] == ()
    assert models[0].calls[1]["diagnostic_digests"] == ()
    assert models[0].calls[2]["diagnostic_digests"]
    assert "history.py" not in models[0].atoms[1].objective


@pytest.mark.parametrize("bad", ["unresolved", "invented", "missing", "duplicate", "wrong-request"])
def test_unresolved_or_unbound_grounding_keeps_questions(feature, tmp_path, monkeypatch, bad):
    questions, grounding, _ = records(feature, quotes=bad != "unresolved")
    if bad == "invented":
        grounding["dispositions"][0]["quotes"][0]["quote"] = "Policy that was never specified"
    if bad == "missing":
        grounding["dispositions"] = []
    if bad == "duplicate":
        grounding["dispositions"] *= 2
    if bad == "wrong-request":
        grounding["request_digest"] = "f" * 64
    models = fake_model(
        monkeypatch, [document(json.loads(questions.canonical())), document(grounding)]
    )
    result = draft_feature(
        feature, profile(), tmp_path / "plan", deployment="fixture", structured_interfaces=True
    )
    assert result["status"] == "needs-info"
    assert result["questions"] == list(questions.questions)
    assert result["proposal_digest"] is None and len(models[0].calls) == 2


def test_repeated_questions_do_not_start_another_review(feature, tmp_path, monkeypatch):
    questions, grounding, _ = records(feature)
    models = fake_model(
        monkeypatch,
        [
            document(json.loads(questions.canonical())),
            document(grounding),
            document(json.loads(questions.canonical())),
        ],
    )
    result = draft_feature(
        feature, profile(), tmp_path / "plan", deployment="fixture", structured_interfaces=True
    )
    assert result["status"] == "needs-info" and len(models[0].calls) == 3


def test_exact_citation_is_provenance_not_semantic_proof(feature):
    questions, grounding, _ = records(feature)
    # The trusted check proves quote provenance; semantic coverage remains model judgment.
    record = QuestionGrounding.model_validate_json(json.dumps(grounding))
    assert record.covered(
        feature.digest(), questions.digest(), questions.questions, feature.requirements
    )


def test_grounding_can_cross_attempt_boundary_without_budget_reset(feature, tmp_path, monkeypatch):
    from gflo.worker import ReadFileRequest

    questions, grounding, plan = records(feature)
    fake_model(
        monkeypatch,
        [
            ReadFileRequest(kind="read_file", path="cli.py"),
            document(json.loads(questions.canonical())),
            document(grounding),
            document(plan),
        ],
    )
    result = draft_feature(
        feature, profile(), tmp_path / "plan", deployment="fixture", structured_interfaces=True
    )
    assert result["status"] == "needs-review"
    assert [(o["attempt"], o["turn"]) for o in result["observations"]] == [
        (1, 1),
        (1, 2),
        (1, 3),
        (2, 1),
    ]


def test_grounding_cannot_expand_into_source_reads(feature, tmp_path, monkeypatch):
    from gflo.worker import ReadFileRequest, compose_view, messages

    questions, _, _ = records(feature)
    models = fake_model(
        monkeypatch,
        [
            document(json.loads(questions.canonical())),
            ReadFileRequest(kind="read_file", path="cli.py"),
        ],
    )
    result = draft_feature(
        feature, profile(), tmp_path / "plan", deployment="fixture", structured_interfaces=True
    )
    assert result["status"] == "needs-info" and len(models[0].calls) == 2
    atom = models[0].atoms[1]
    assert atom.allowed_tools == ("edit",)
    store = models[0].artifacts
    view = compose_view(store, atom, feature.source.digest(), selected_paths=())
    system = messages(view, document=True)[0]["content"]
    assert "read_file" not in system and "Source reads are unavailable" in system


def test_replanning_keeps_schema_failure_feedback_after_grounding(feature, tmp_path, monkeypatch):
    from gflo.worker import Diagnostic

    questions, grounding, plan = records(feature)
    malformed = {k: v for k, v in plan.items() if k != "questions"}
    models = fake_model(
        monkeypatch,
        [
            document(json.loads(questions.canonical())),
            document(grounding),
            document(malformed),
            document(plan),
        ],
    )
    result = draft_feature(
        feature, profile(), tmp_path / "plan", deployment="fixture", structured_interfaces=True
    )
    assert result["status"] == "needs-review" and len(models[0].calls) == 4
    diagnostics = [
        Diagnostic.model_validate_json(models[0].artifacts.read(d))
        for d in models[0].calls[-1]["diagnostic_digests"]
    ]
    assert any("exact original requirement quotes" in d.text for d in diagnostics)
    assert any("Field required" in d.text and "questions" in d.text for d in diagnostics)
