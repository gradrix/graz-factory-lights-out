"""The structured boundary and durable review stops preserve execution authority."""

import json

import pytest
from test_controller import plan as plan
from test_controller import setup
from test_preparation import inputs as inputs

from gflo.contracts import CONTRACT_PROFILE, InterfaceBundle, InterfaceDeclaration, task_interfaces
from gflo.escalation import pending_review, review_handoff
from gflo.ledger import WorkLedger
from gflo.preparation import prepare_task
from gflo.worker import CandidateResult, ContractConflict, parse_result


@pytest.mark.parametrize("symbol", ["_validate_title", "_validate_storage", "_Outer._helper"])
def test_private_python_interface_names_are_valid_without_widening_general_identifiers(symbol):
    from pydantic import TypeAdapter, ValidationError

    from gflo.contracts import InterfaceDeclaration
    from gflo.records import Identifier

    declaration = InterfaceDeclaration(
        path="taskdock.py",
        symbol=symbol,
        declaration=f"def {symbol.rsplit('.', 1)[-1]}(value): ...",
        requirement_ids=("storage",),
    )
    assert declaration.symbol == symbol
    with pytest.raises(ValidationError):
        TypeAdapter(Identifier).validate_python("_work_atom")


@pytest.mark.parametrize(
    "text",
    [
        "def select(x): return min(x)",
        "def broken(",
        "@dec\ndef select(x): ...",
        "def select(x=call()): ...",
        "def other(x): ...",
        "def select(x): ...\nraise Exception()",
    ],
)
def test_declarations_reject_implementation(text):
    with pytest.raises(ValueError):
        InterfaceDeclaration(
            path="main.py", symbol="select", declaration=text, requirement_ids=("answer",)
        )


def test_structured_authority_omits_planner_algorithm(inputs):
    store, request, proposal, review = inputs
    declaration = InterfaceDeclaration(
        path="main.py",
        symbol="select",
        declaration="def select(x): ...",
        requirement_ids=("answer",),
    )
    bundle = InterfaceBundle(declarations=(declaration,)).canonical()
    task = proposal.tasks[0].model_copy(
        update={
            "objective": "BAD ALGORITHM: print 0",
            "interface_contracts": (bundle,),
            "acceptance_checks": ("BAD ALGORITHM: print 0",),
        }
    )
    proposal = proposal.model_copy(update={"tasks": (task,)})
    review = review.model_copy(
        update={
            "proposal_digest": proposal.digest(),
            "model_profile": review.model_profile.model_copy(
                update={"profile_id": CONTRACT_PROFILE}
            ),
        }
    )
    package = prepare_task(store, request, proposal, review, "main", current_source=request.source)
    objective = json.loads(package.run.atom.objective)
    assert "BAD ALGORITHM" not in package.run.atom.objective
    assert objective["requirements"] == {"answer": "Print 42"}
    assert objective["interfaces"][0]["declaration"] == "def select(x): ..."
    for paths, requirements in [((), ("answer",)), (("main.py",), ("unknown",))]:
        with pytest.raises(ValueError):
            task_interfaces((bundle,), paths, requirements)


def contract_plan(plan):
    return plan.model_copy(
        update={
            "model_profile": plan.model_profile.model_copy(update={"profile_id": CONTRACT_PROFILE})
        }
    )


@pytest.mark.parametrize("conflict", [False, True])
def test_review_stop_survives_reopen_without_spending_retry(tmp_path, plan, conflict):
    plan = contract_plan(plan)
    action = (
        ContractConflict(
            kind="contract_conflict",
            reason="Signature cannot express requirement",
            requirement_ids=plan.atom.requirement_ids[:1],
        )
        if conflict
        else CandidateResult(kind="candidate", changes={"main.py": "print(1)"})
    )
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan, [action])
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "retry-ready"
        assert len(result["attempts"]) == 1
        assert len(model.calls) == (1 if conflict else 2)
        assert broker.calls == (0 if conflict else 1)
        assert pending_review(ledger, plan.atom.atom_id)
        packet = review_handoff(ledger, plan.atom.atom_id)
        assert packet["status"] == "needs-review"
        assert packet["latest_unaccepted_draft"]
        assert ledger.audit_artifacts().missing == ()
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan, [action])
        assert controller.run(plan.atom.atom_id) == result
        assert model.calls == [] and broker.calls == 0


def test_conflict_protocol_is_opt_in_and_requirement_bound(plan):
    conflict = ContractConflict(
        kind="contract_conflict",
        reason="Contradiction",
        requirement_ids=plan.atom.requirement_ids[:1],
    )
    with pytest.raises(ValueError, match="not enabled"):
        parse_result(conflict.canonical(), plan.atom, plan.source)
    assert (
        parse_result(conflict.canonical(), plan.atom, plan.source, allow_conflicts=True) == conflict
    )
    with pytest.raises(ValueError, match="unknown requirements"):
        parse_result(
            conflict.model_copy(update={"requirement_ids": ("unknown",)}).canonical(),
            plan.atom,
            plan.source,
            allow_conflicts=True,
        )


def test_final_gate_failure_cannot_repeat_unchanged_across_attempts(tmp_path, plan):
    plan = contract_plan(plan).model_copy(update={"max_model_turns": 1})
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(
            ledger, plan, [CandidateResult(kind="candidate", changes={"main.py": "print(1)"})]
        )
        result = controller.run(plan.atom.atom_id)
        assert len(result["attempts"]) == 2
        assert len(model.calls) == 2
        assert broker.calls == 2  # smoke and final gate for the first draft only
        assert pending_review(ledger, plan.atom.atom_id)
        assert result["attempts"][0]["gate_receipts"][0]["outcome"] == "fail"
        assert not result["attempts"][1]["gate_receipts"]


@pytest.mark.parametrize(
    "profile, inherited",
    [
        ("vllm-python-worker-contracts-v1", False),
        ("vllm-python-worker-contracts-v2", True),
    ],
)
def test_dependency_brief_contains_original_provider_rules_without_advice(
    tmp_path, profile, inherited
):
    from test_progression import Services, feature

    from gflo.progression import run_feature

    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        tasks = tuple(
            task.model_copy(
                update={
                    "interface_contracts": (InterfaceBundle(declarations=()).canonical(),),
                    "objective": "BAD ALGORITHM ADVICE",
                }
            )
            for task in plan.proposal.tasks
        )
        proposal = plan.proposal.model_copy(update={"tasks": tasks})
        review = plan.review.model_copy(
            update={
                "proposal_digest": proposal.digest(),
                "model_profile": plan.review.model_profile.model_copy(
                    update={"profile_id": profile}
                ),
            }
        )
        plan = plan.model_copy(update={"proposal": proposal, "review": review})
        services = Services()
        result = run_feature(
            ledger,
            plan,
            lambda: plan.request.source,
            model_factory=services.model,
            broker_factory=services.broker,
        )
        assert result.status == "accepted"
        consumer = services.model_calls[1][0]
        brief = json.loads(consumer.objective)
        assert ("value" in brief["requirements"]) is inherited
        assert ("value" in consumer.requirement_ids) is inherited
        assert "BAD ALGORITHM ADVICE" not in consumer.objective
        assert consumer.writable_paths == ("main.py",)
        calls = len(services.model_calls)
        assert (
            run_feature(
                ledger,
                plan,
                lambda: plan.request.source,
                model_factory=services.model,
                broker_factory=services.broker,
            )
            == result
        )
        assert len(services.model_calls) == calls
