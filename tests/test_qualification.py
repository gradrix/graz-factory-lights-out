"""Operator-prepared plans remain subject to normal policy and replay authority."""

import json

import pytest
from test_autonomy import policy_for
from test_progression import Services, feature

from gflo.autonomy import build_feature
from gflo.ledger import WorkLedger
from gflo.qualification import prepared_planner


def test_prepared_build_uses_policy_and_replays_without_generation(tmp_path):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        services = Services()
        result = build_feature(
            ledger,
            plan.request,
            policy_for(plan),
            tmp_path / "build",
            lambda: plan.request.source,
            planner=prepared_planner(plan.proposal),
            model_factory=services.model,
            broker_factory=services.broker,
        )
        assert result["status"] == "accepted"
        state = json.loads((tmp_path / "build/planning/result.json").read_text())
        assert state["planner_origin"] == "operator-prepared-v1"
        assert state["observations"] == []
        before = (services.model_calls[:], services.broker_calls)
        replay = build_feature(
            ledger,
            plan.request,
            policy_for(plan),
            tmp_path / "build",
            lambda: plan.request.source,
            planner=lambda *args, **kwargs: pytest.fail("replanned"),
            model_factory=services.model,
            broker_factory=services.broker,
        )
        assert replay == result
        assert before == (services.model_calls, services.broker_calls)


def test_prepared_proposal_cannot_bypass_write_policy(tmp_path):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        proposal = plan.proposal.model_copy(
            update={
                "tasks": (
                    plan.proposal.tasks[0].model_copy(update={"writable_paths": ("outside.py",)}),
                    *plan.proposal.tasks[1:],
                )
            }
        )
        result = build_feature(
            ledger,
            plan.request,
            policy_for(plan),
            tmp_path / "build",
            lambda: plan.request.source,
            planner=prepared_planner(proposal),
            model_factory=lambda *args, **kwargs: pytest.fail("inference before policy"),
        )
        assert result["status"] == "policy-halt"


def test_prepared_proposal_rejects_wrong_binding_before_writing(tmp_path):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        proposal = plan.proposal.model_copy(update={"request_digest": "f" * 64})
        with pytest.raises(ValueError, match="different request"):
            prepared_planner(proposal)(
                plan.request, plan.review.model_profile, tmp_path / "planning"
            )
        assert not (tmp_path / "planning").exists()
