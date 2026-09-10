"""Board opinions cannot silently clear blockers or replace trusted gates."""

import json

import pytest
from test_progression import feature

from gflo.board import draft_board
from gflo.board_records import ROLES, BoardFinding, SpecialistReport
from gflo.ledger import WorkLedger
from gflo.planning import BoardSynthesis, PlanQuestions, validate_board_report, validate_synthesis
from gflo.repository import Repository, SnapshotSource


def reports(request, blocking=False):
    return tuple(
        SpecialistReport(
            request_digest=request.digest(),
            role=role,
            findings=(
                BoardFinding(
                    finding_id="check",
                    requirement_ids=("value",),
                    severity="concern",
                    observation="Check compatibility",
                    recommendation="Retain provider signature",
                    source_paths=("main.py",),
                ),
            ),
            questions=("Which policy?",) if blocking and role == "product" else (),
            summary="Bounded advice",
        )
        for role in ROLES
    )


def synthesis(plan, rows):
    return BoardSynthesis(
        request_digest=plan.request.digest(),
        report_digests=tuple(r.digest() for r in rows),
        dispositions={
            f"{r.role}:check": "Covered by the independent contract checks" for r in rows
        },
        disagreements=(),
        outcome=plan.proposal,
    )


def test_synthesis_requires_all_findings_exact_evidence_and_unresolved_blockers(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        rows = reports(plan.request)
        decision = synthesis(plan, rows)
        validate_synthesis(decision, plan.request.digest(), rows)
        for field, value, match in [
            ("dispositions", {}, "every specialist"),
            ("report_digests", ["a" * 64] * 4, "exact specialist"),
            ("request_digest", "a" * 64, "bind the request"),
        ]:
            d = decision.model_dump(mode="json")
            d[field] = value
            with pytest.raises(ValueError, match=match):
                validate_synthesis(
                    BoardSynthesis.model_validate_json(json.dumps(d)), plan.request.digest(), rows
                )
        blocked = reports(plan.request, True)
        with pytest.raises(ValueError, match="blockers"):
            validate_synthesis(synthesis(plan, blocked), plan.request.digest(), blocked)
        d = synthesis(plan, blocked).model_dump(mode="json")
        d["outcome"] = PlanQuestions(
            request_digest=plan.request.digest(),
            questions=("Which policy?",),
            rationale="Missing policy",
        ).model_dump(mode="json")
        validate_synthesis(
            BoardSynthesis.model_validate_json(json.dumps(d)), plan.request.digest(), blocked
        )


def test_report_cannot_forge_role_request_or_source(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        row = reports(plan.request)[0]
        validate_board_report(row, plan.request, "product", ("main.py",))
        with pytest.raises(ValueError, match="request and role"):
            validate_board_report(row, plan.request, "operations", ("main.py",))
        with pytest.raises(ValueError, match="outside"):
            validate_board_report(row, plan.request, "product", ())


def test_board_runs_independent_roles_then_preserves_synthesis(tmp_path, monkeypatch):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        rows = reports(plan.request)
        calls = []

        def stage(request, profile, output, **kwargs):
            calls.append(kwargs)
            output.mkdir()
            role = kwargs.get("specialist")
            if role:
                assert not kwargs.get("reports")
                row = next(r for r in rows if r.role == role)
                (output / "report.json").write_text(row.canonical())
                return dict(status="advisory", report_digest=row.digest())
            assert kwargs["reports"] == rows
            (output / "proposal.json").write_text(plan.proposal.canonical())
            (output / "synthesis.json").write_text(synthesis(plan, rows).canonical())
            return dict(status="needs-review", questions=[])

        monkeypatch.setattr("gflo.board.draft_feature", stage)
        output = tmp_path / "board"
        result = draft_board(
            plan.request,
            plan.review.model_profile,
            output,
            deployment=plan.review.deployment,
            repository=Repository(SnapshotSource(ledger.artifacts, plan.request.source)),
            context_paths=("main.py",),
        )
        assert len(calls) == 5
        assert result["execution_authorized"] is False
        assert result["report_digests"] == [r.digest() for r in rows]
        assert (output / "synthesis.json").is_file()
        with pytest.raises(FileExistsError):
            draft_board(
                plan.request,
                plan.review.model_profile,
                output,
                deployment=plan.review.deployment,
                repository=Repository(SnapshotSource(ledger.artifacts, plan.request.source)),
                context_paths=("main.py",),
            )


def test_failed_specialist_stops_board_without_coordinator(tmp_path, monkeypatch):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        calls = []

        def stage(*args, **kwargs):
            calls.append(kwargs["specialist"])
            return {"status": "exhausted"}

        monkeypatch.setattr("gflo.board.draft_feature", stage)
        result = draft_board(
            plan.request,
            plan.review.model_profile,
            tmp_path / "board",
            deployment=plan.review.deployment,
            repository=Repository(SnapshotSource(ledger.artifacts, plan.request.source)),
            context_paths=("main.py",),
        )
        assert result["status"] == "specialist-halt" and calls == ["product"]


def test_real_board_pipeline_validates_reports_and_synthesis(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from gflo.worker import CandidateResult

    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        rows = reports(plan.request)
        answers = [*rows, synthesis(plan, rows)]

        class Model:
            def __init__(self, store, profile):
                self.artifacts = store
                self.last_evidence_digest = None

            def turn(self, *args, **kwargs):
                self.last_evidence_digest = self.artifacts.publish(b"board model double")
                record = answers.pop(0)
                return SimpleNamespace(
                    result=CandidateResult(
                        kind="candidate", changes={"factory-plan.json": record.canonical()}
                    )
                )

        monkeypatch.setattr("gflo.planning.LocalModel", Model)
        result = draft_board(
            plan.request,
            plan.review.model_profile,
            tmp_path / "board",
            deployment=plan.review.deployment,
            repository=Repository(SnapshotSource(ledger.artifacts, plan.request.source)),
            context_paths=("main.py",),
        )
        assert result["status"] == "needs-review"
        assert not answers and len(result["stages"]) == 5
        assert (tmp_path / "board/proposal.json").read_text().strip() == plan.proposal.canonical()


def test_board_stops_at_advice_budget_without_dropping_reports(tmp_path, monkeypatch):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        calls = []

        def stage(request, profile, output, **kwargs):
            role = kwargs["specialist"]
            calls.append(role)
            output.mkdir()
            row = SpecialistReport(
                request_digest=request.digest(),
                role=role,
                questions=(),
                summary="s",
                findings=tuple(
                    BoardFinding(
                        finding_id=f"f{i}",
                        requirement_ids=("value",),
                        severity="concern",
                        observation="x" * 1200,
                        recommendation="y" * 1200,
                        source_paths=("main.py",),
                    )
                    for i in range(2)
                ),
            )
            (output / "report.json").write_text(row.canonical())
            return {"status": "advisory"}

        monkeypatch.setattr("gflo.board.draft_feature", stage)
        result = draft_board(
            plan.request,
            plan.review.model_profile,
            tmp_path / "board",
            deployment=plan.review.deployment,
            repository=Repository(SnapshotSource(ledger.artifacts, plan.request.source)),
            context_paths=("main.py",),
        )
        assert result["status"] == "advice-budget-halt" and calls == list(ROLES)
        assert all((tmp_path / "board" / role / "report.json").exists() for role in ROLES)
        assert not (tmp_path / "board/proposal.json").exists()


def test_unresolved_specialist_questions_short_circuit_without_synthesis(tmp_path, monkeypatch):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        calls = []
        row = reports(plan.request, True)[0]

        def stage(request, profile, output, **kwargs):
            calls.append(kwargs["specialist"])
            output.mkdir()
            (output / "report.json").write_text(row.canonical())
            return {"status": "advisory"}

        monkeypatch.setattr("gflo.board.draft_feature", stage)
        result = draft_board(
            plan.request,
            plan.review.model_profile,
            tmp_path / "board",
            deployment=plan.review.deployment,
            repository=Repository(SnapshotSource(ledger.artifacts, plan.request.source)),
            context_paths=("main.py",),
        )
        assert calls == ["product"]
        assert result["status"] == "needs-info" and result["questions"] == ["Which policy?"]
        assert result["execution_authorized"] is False
        assert not (tmp_path / "board/coordinator").exists()
        assert not (tmp_path / "board/proposal.json").exists()
