"""Frozen budget-matched reasoning comparison with full features and retained failures."""

import importlib.util
import json
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.contracts import WINDOW_PROFILE, WINDOW_REASONING_PROFILE
from gflo.ledger import WorkLedger
from gflo.progression import FeaturePlan, run_feature
from gflo.records import ContextBudget
from gflo.repository import capture_worktree, snapshot_bundle

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/window-reasoning-v1")
BUDGET = ContextBudget(total_tokens=16384, output_tokens=6144)
spec = importlib.util.spec_from_file_location("fixture", HERE.parent / "atomic-moves/campaign.py")
assert spec and spec.loader
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def prepare(ledger, number, reasoning, repair):
    old = FeaturePlan.model_validate_json(
        json.dumps(json.loads((HERE / "frozen-features.json").read_text())[str(number)])
    )
    assert capture_worktree(ledger.artifacts, fixture.TARGET) == old.request.source
    plan = old
    if repair:
        retained = json.loads((HERE / "retained-drafts.json").read_text())[str(number)]
        draft = SourceBundle.model_validate_json(json.dumps(retained["source"]))
        assert draft.digest() == retained["candidate_digest"]
        source = snapshot_bundle(ledger.artifacts, draft)
        request = old.request.model_copy(
            update={
                "feature_id": f"atomic-retained-repair-{number}",
                "source": source,
                "allowed_paths": (fixture.TEST,),
            }
        )
        test_task = next(t for t in old.proposal.tasks if fixture.TEST in t.writable_paths)
        test_task = test_task.model_copy(
            update={
                "depends_on": (),
                "requirement_ids": tuple(sorted(request.requirements)),
                "objective": (
                    "Repair the retained tests to satisfy the original requirements "
                    "and pinned checks."
                ),
            }
        )
        proposal = old.proposal.model_copy(
            update={
                "request_digest": request.digest(),
                "tasks": (test_task,),
                "rationale": (
                    "New bounded repair work from an unchanged retained failed test draft."
                ),
            }
        )
        task_review = old.review.tasks[test_task.task_id].model_copy(
            update={
                "execution_paths": tuple(sorted(draft.files)),
                "context_paths": (
                    fixture.TEST,
                    fixture.IMPLEMENTATION,
                    "common/models/move.py",
                    fixture.SCHEMA,
                ),
            }
        )
        review = old.review.model_copy(
            update={
                "request_digest": request.digest(),
                "proposal_digest": proposal.digest(),
                "tasks": {test_task.task_id: task_review},
            }
        )
        plan = old.model_copy(update={"request": request, "proposal": proposal, "review": review})
    profile = WINDOW_REASONING_PROFILE if reasoning else WINDOW_PROFILE
    return FeaturePlan.model_validate(
        plan.model_copy(
            update={
                "review": plan.review.model_copy(
                    update={
                        "context_budget": BUDGET,
                        "model_profile": plan.review.model_profile.model_copy(
                            update={"profile_id": profile}
                        ),
                    }
                ),
            }
        )
    )


def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    schedule = [
        (1, False, False),
        (1, True, False),
        (2, True, False),
        (2, False, False),
        (3, False, False),
        (3, True, False),
        (1, False, True),
        (1, True, True),
        (2, True, True),
        (2, False, True),
    ]
    rows = []
    for number, reasoning, repair in schedule:
        name = (
            ("repair" if repair else "feature")
            + f"-{number}-"
            + ("reasoning" if reasoning else "control")
        )
        path = ROOT / name
        path.mkdir()
        with WorkLedger(path / "ledger.db") as ledger:
            plan = prepare(ledger, number, reasoning, repair)
            assert plan.review.max_attempts == 2 and plan.review.max_model_turns == 3
            assert plan.review.model_profile.context_limit == 16384
            (path / "plan.json").write_text(plan.canonical() + "\n")
            rows.append(
                dict(
                    name=name,
                    plan_digest=plan.digest(),
                    responses_reserved=len(plan.proposal.tasks) * 6,
                    tokens_reserved=len(plan.proposal.tasks) * 6 * 16384,
                )
            )
    # Budget-matched pairs differ only in the explicitly selected model profile.
    for number, repair in [(1, False), (2, False), (3, False), (1, True), (2, True)]:
        prefix = ("repair" if repair else "feature") + f"-{number}-"
        control = json.loads((ROOT / (prefix + "control") / "plan.json").read_text())
        reasoning = json.loads((ROOT / (prefix + "reasoning") / "plan.json").read_text())
        reasoning["review"]["model_profile"]["profile_id"] = WINDOW_PROFILE
        assert control == reasoning
    (ROOT / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    # Independent known-good reference and retained failures: no inference before gates qualify.
    checks = []
    for name in ["feature-1-control", "repair-1-control", "repair-2-control"]:
        path = ROOT / name
        with WorkLedger(path / "ledger.db") as ledger:
            plan = FeaturePlan.model_validate_json((path / "plan.json").read_bytes())
            from gflo.repository import Repository, SnapshotSource

            repository = Repository(SnapshotSource(ledger.artifacts, plan.request.source))
            selection = repository.select(
                tuple(p for p in plan.integration.execution_paths if p in repository.source.files),
                purpose="execution",
            )
            source = selection.bundle
            broker = DockerBroker(ledger.artifacts, plan.request.environments["python"].image)
            broker.qualify()
            good = SourceBundle(
                files=source.files
                | {
                    fixture.IMPLEMENTATION: fixture.replace_method(
                        source.files[fixture.IMPLEMENTATION],
                        (fixture.HERE / "reference-method.py").read_text(),
                    ),
                    fixture.TEST: (fixture.HERE / "reference-tests.py").read_text(),
                }
            )
            for gate_id, gate in plan.integration.gates.items():
                case = gate.cases[0]
                execution = broker.execute(
                    ledger.artifacts.publish(good.canonical().encode()),
                    case.command,
                    seconds=case.seconds,
                    purpose="validation",
                )
                checks.append(
                    dict(name=name, gate=gate_id, execution=execution.model_dump(mode="json"))
                )
                assert execution.exit_code == 0, (name, gate_id, execution.exit_code)
            if name.startswith("repair"):
                case = plan.integration.gates["tests"].cases[0]
                execution = broker.execute(
                    ledger.artifacts.publish(source.canonical().encode()),
                    case.command,
                    seconds=case.seconds,
                    purpose="validation",
                )
                checks.append(
                    dict(
                        name=name,
                        gate="retained-failure",
                        execution=execution.model_dump(mode="json"),
                    )
                )
                assert execution.exit_code != 0
    (ROOT / "preflight.json").write_text(json.dumps(checks, indent=2) + "\n")
    print("preflight passed; all ten plans and budgets frozen", flush=True)
    for row in rows:
        path = ROOT / row["name"]
        with WorkLedger(path / "ledger.db") as ledger:
            plan = FeaturePlan.model_validate_json((path / "plan.json").read_bytes())
            result = run_feature(ledger, plan, lambda: plan.request.source)
            (path / "result.json").write_text(result.canonical() + "\n")
            print(row["name"], result.status, flush=True)


if __name__ == "__main__":
    main()
