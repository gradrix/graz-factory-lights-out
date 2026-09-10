"""Frozen full-retry comparison; checked reliability is primary, cost secondary."""

import importlib.util
import json
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.gates import ProcessCase, ProcessGate
from gflo.ledger import WorkLedger
from gflo.progression import FeaturePlan, run_feature

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/full-worker-budgets-v1")


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, HERE.parent / "test-decomposition" / (name + ".py")
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture, audit, report = load("campaign"), load("audit"), load("report")


def with_default(gate, paths):
    # Keep the four original faults and independently require default coverage.
    command = audit.command(paths, ["default"])
    code = command[-1].replace(
        "print(json.dumps(results))",
        "assert all(r['detected'] for r in results), results\nprint('qualified')",
    )
    return ProcessGate(
        cases=gate.cases
        + (ProcessCase(command=(*command[:-1], code), expected_stdout="qualified\n", seconds=30),)
    )


def make_plan(store, name, split):
    plan = fixture.plan(store, name, split)
    tasks = dict(plan.review.tasks)
    key = "values" if split else "all"
    policy = tasks[key]
    tasks[key] = policy.model_copy(
        update={"gates": {"faults": with_default(policy.gates["faults"], [f"tests/test_{key}.py"])}}
    )
    paths = [f"tests/test_{key}.py" for key in tasks]
    return plan.model_copy(
        update={
            "review": plan.review.model_copy(update={"tasks": tasks, "max_attempts": 2}),
            "integration": plan.integration.model_copy(
                update={
                    "gates": {"combined": with_default(plan.integration.gates["combined"], paths)}
                }
            ),
        }
    )


def preflight(plans):
    image = plans[0].request.environments["python"].image
    with WorkLedger(ROOT / "preflight.db") as ledger:
        broker = DockerBroker(ledger.artifacts, image)
        broker.qualify()
        reports = []
        for plan in plans[:2]:
            tests = (
                {"tests/test_all.py": fixture.VALUES + "\n" + fixture.TYPES}
                if len(plan.proposal.tasks) == 1
                else {"tests/test_values.py": fixture.VALUES, "tests/test_types.py": fixture.TYPES}
            )
            good = SourceBundle(files=fixture.source().files | tests)
            for scope, policy in [*plan.review.tasks.items(), ("integration", plan.integration)]:
                for gate in policy.gates.values():
                    for case in gate.cases:
                        digest = ledger.artifacts.publish(good.canonical().encode())
                        execution = broker.execute(
                            digest, case.command, seconds=case.seconds, purpose="validation"
                        )
                        reports.append(
                            dict(scope=scope, execution=execution.model_dump(mode="json"))
                        )
                        assert execution.exit_code == 0 and execution.stdout == b"qualified\n", (
                            execution
                        )
        (ROOT / "preflight.json").write_text(json.dumps(reports, indent=2) + "\n")
    print("preflight passed", flush=True)


def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    schedule = [
        ("solo-1", False),
        ("split-1", True),
        ("split-2", True),
        ("solo-2", False),
        ("solo-3", False),
        ("split-3", True),
    ]
    (ROOT / "schedule.json").write_text(json.dumps(schedule) + "\n")
    plans = []
    # Freeze every plan, gate and finite reservation before any inference.
    for name, split in schedule:
        trial = ROOT / name
        trial.mkdir()
        with WorkLedger(trial / "ledger.db") as ledger:
            plan = make_plan(ledger.artifacts, name, split)
            plan = FeaturePlan.model_validate(plan)
            assert plan.kind == "reviewed-feature-v2"
            assert plan.review.max_attempts == 2 and plan.review.max_model_turns == 3
            (trial / "plan.json").write_text(plan.canonical() + "\n")
            plans.append(plan)
    preflight(plans)
    for (name, _), plan in zip(schedule, plans, strict=True):
        trial = ROOT / name
        with WorkLedger(trial / "ledger.db") as ledger:
            result = run_feature(ledger, plan, lambda: plan.request.source)
            (trial / "result.json").write_text(result.canonical() + "\n")
            print(name, result.status, flush=True)
    rows = []
    for name, split in schedule:
        row = report.trial_report(ROOT / name)
        row["reserved_model_responses"] = 12 if split else 6
        row["reserved_tokens"] = row["reserved_model_responses"] * 12288
        rows.append(row)
    (HERE / "results.json").write_text(
        json.dumps(dict(campaign=ROOT.name, schedule=schedule, trials=rows), indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
