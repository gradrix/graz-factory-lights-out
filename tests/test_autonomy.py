"""Policy authority and full build replay through the real execution controller."""

import json

import pytest
from test_progression import Services, feature

from gflo.autonomy import FeaturePolicy, build_feature, compile_feature
from gflo.ledger import WorkLedger
from gflo.repository import SourceRef


def policy_for(plan):
    return FeaturePolicy(
        request_digest=plan.request.digest(),
        file_gates={
            "provider.py": plan.review.tasks["provider"].gates["behavior"],
            "main.py": plan.review.tasks["consumer"].gates["behavior"],
        },
        execution_paths=("main.py", "provider.py"),
        planning_paths=("main.py",),
        integration_gates=plan.integration.gates,
        environment_id="python",
        model_profile=plan.review.model_profile,
        deployment=plan.review.deployment,
        context_budget=plan.review.context_budget,
    )


def replace(record, **changes):
    return type(record).model_validate_json(json.dumps(record.model_dump(mode="json") | changes))


def planner_for(plan, calls):
    def draft(request, profile, output, **kwargs):
        calls.append(request.digest())
        output.mkdir()
        (output / "proposal.json").write_text(plan.proposal.canonical())
        state = {
            "status": "needs-review",
            "questions": [],
            "proposal_digest": plan.proposal.digest(),
        }
        (output / "result.json").write_text(json.dumps(state))
        return state

    return draft


def test_compiles_trusted_checks_and_preserves_graph(tmp_path):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        policy = policy_for(plan)
        compiled = compile_feature(ledger.artifacts, plan.request, plan.proposal, policy)
        assert compiled.proposal == plan.proposal
        assert compiled.review.tasks["provider"].execution_paths == ("main.py",)
        assert compiled.review.tasks["consumer"].execution_paths == ("main.py", "provider.py")
        assert compiled.review.tasks["provider"].gates == {
            "file-0": policy.file_gates["provider.py"]
        }
        assert compiled.integration.gates == policy.integration_gates
        assert ledger.artifacts.read(policy.digest()) == policy.canonical().encode()


@pytest.mark.parametrize(
    "change,match",
    [
        ({"request_digest": "f" * 64}, "exact request"),
        ({"max_reserved_tokens": 1}, "token budget"),
        ({"max_tasks": 1}, "task budget"),
        ({"execution_paths": ["main.py"]}, "every authorized output"),
        ({"execution_paths": ["main.py", "provider.py", "absent.py"]}, "neither existing"),
        ({"environment_id": "other"}, "Unknown policy environment"),
    ],
)
def test_policy_rejects_unhandled_authority(tmp_path, change, match):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        with pytest.raises(ValueError, match=match):
            compile_feature(
                ledger.artifacts, plan.request, plan.proposal, replace(policy_for(plan), **change)
            )


def test_missing_gate_and_questions_never_compile(tmp_path):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        policy = policy_for(plan)
        with pytest.raises(ValueError, match="every exact allowed file"):
            compile_feature(
                ledger.artifacts,
                plan.request,
                plan.proposal,
                replace(
                    policy,
                    file_gates={"main.py": policy.file_gates["main.py"].model_dump(mode="json")},
                ),
            )
        with pytest.raises(ValueError, match="questions"):
            compile_feature(
                ledger.artifacts,
                plan.request,
                replace(plan.proposal, questions=["Which answer?"]),
                policy,
            )


def test_build_replays_without_planner_or_worker_calls(tmp_path):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        policy = policy_for(plan)
        services, calls = Services(), []

        def run(current=plan.request.source, selected_policy=policy):
            return build_feature(
                ledger,
                plan.request,
                selected_policy,
                tmp_path / "build",
                lambda: current,
                planner=planner_for(plan, calls),
                model_factory=services.model,
                broker_factory=services.broker,
            )

        result = run()
        assert result["status"] == "accepted"
        assert len(services.model_calls) == 2
        assert len(calls) == 1
        broker_calls = services.broker_calls
        assert run() == result
        assert len(services.model_calls) == 2
        assert services.broker_calls == broker_calls
        assert len(calls) == 1
        with pytest.raises(ValueError, match="different request, policy or store"):
            run(selected_policy=replace(policy, max_tasks=5))
        with pytest.raises(ValueError, match="External source"):
            run(current=SourceRef(kind="repository-snapshot-v1", artifact_digest="f" * 64))


@pytest.mark.parametrize(
    "state,status",
    [
        ({"status": "needs-info", "questions": ["Which policy?"]}, "needs-info"),
        ({"status": "exhausted"}, "planning-halt"),
        ({}, "planning-halt"),
    ],
)
def test_planning_halts_are_not_silently_retried(tmp_path, state, status):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        calls = []

        def draft(request, profile, output, **kwargs):
            calls.append(1)
            output.mkdir()
            if state:
                (output / "result.json").write_text(json.dumps(state))
            return state

        for _ in range(2):
            result = build_feature(
                ledger,
                plan.request,
                policy_for(plan),
                tmp_path / "build",
                lambda: plan.request.source,
                planner=draft,
            )
            assert result["status"] == status
        assert calls == [1]


def test_policy_halt_spends_no_worker_calls(tmp_path):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        services, calls = Services(), []
        result = build_feature(
            ledger,
            plan.request,
            replace(policy_for(plan), max_tasks=1),
            tmp_path / "build",
            lambda: plan.request.source,
            planner=planner_for(plan, calls),
            model_factory=services.model,
            broker_factory=services.broker,
        )
        assert result["status"] == "policy-halt"
        assert services.model_calls == []
        assert services.broker_calls == 0


def test_interrupted_execution_resumes_without_replanning(tmp_path):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        services, calls = Services(), []
        services.interrupt = True

        def run():
            return build_feature(
                ledger,
                plan.request,
                policy_for(plan),
                tmp_path / "build",
                lambda: plan.request.source,
                planner=planner_for(plan, calls),
                model_factory=services.model,
                broker_factory=services.broker,
            )

        with pytest.raises(KeyboardInterrupt):
            run()
        assert (
            json.loads((tmp_path / "build/result.json").read_text())["status"]
            == "execution-interrupted"
        )
        services.interrupt = False
        assert run()["status"] == "accepted"
        assert len(calls) == 1
        assert sum(atom.writable_paths == ("provider.py",) for atom, _ in services.model_calls) == 1


def test_altered_proposal_is_not_a_new_authorized_build(tmp_path):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        services, calls = Services(), []

        def run():
            return build_feature(
                ledger,
                plan.request,
                policy_for(plan),
                tmp_path / "build",
                lambda: plan.request.source,
                planner=planner_for(plan, calls),
                model_factory=services.model,
                broker_factory=services.broker,
            )

        assert run()["status"] == "accepted"
        (tmp_path / "build/planning/proposal.json").write_text(
            replace(plan.proposal, rationale="Changed after planning").canonical()
        )
        with pytest.raises(ValueError, match="differs from planning result"):
            run()
        assert len(services.model_calls) == 2


def test_policy_planning_stays_nonthinking_while_worker_profile_is_retained(tmp_path):
    with WorkLedger(tmp_path / "ledger") as ledger:
        plan = feature(ledger)
        policy = policy_for(plan)
        policy = replace(
            policy,
            model_profile={
                **policy.model_profile.model_dump(mode="json"),
                "profile_id": "vllm-python-worker-reasoning-v1",
            },
        )
        services = Services()

        def planner(request, profile, output, **kwargs):
            assert profile.profile_id == "vllm-python-worker-v1"
            assert profile.deployment_digest == policy.model_profile.deployment_digest
            return planner_for(plan, [])(request, profile, output, **kwargs)

        result = build_feature(
            ledger,
            plan.request,
            policy,
            tmp_path / "build",
            lambda: plan.request.source,
            planner=planner,
            model_factory=services.model,
            broker_factory=services.broker,
        )
        assert result["status"] == "accepted"
        prepared = json.loads((tmp_path / "build/feature-plan.json").read_text())
        assert (
            prepared["review"]["model_profile"]["profile_id"] == "vllm-python-worker-reasoning-v1"
        )
