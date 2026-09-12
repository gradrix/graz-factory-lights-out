"""Freeze paired definition-context trials before inference, preserving every halt."""

import importlib.util
import json
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.contracts import WINDOW_DEFINITION_PROFILE, WINDOW_REASONING_PROFILE
from gflo.ledger import WorkLedger
from gflo.progression import FeaturePlan, run_feature
from gflo.repository import Repository, SnapshotSource, snapshot_bundle

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/definition-context-v1")
spec = importlib.util.spec_from_file_location(
    "previous", HERE.parent / "window-reasoning/campaign.py"
)
assert spec and spec.loader
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


def prepare(ledger, number, retained, enabled):
    plan = previous.prepare(ledger, number, True, retained)
    if retained:
        draft = SourceBundle.model_validate_json((HERE / "retained-source.json").read_bytes())
        source = snapshot_bundle(ledger.artifacts, draft)
        request = plan.request.model_copy(
            update={"source": source, "feature_id": "retained-helper-call-repair"}
        )
        proposal = plan.proposal.model_copy(update={"request_digest": request.digest()})
        review = plan.review.model_copy(
            update={"request_digest": request.digest(), "proposal_digest": proposal.digest()}
        )
        plan = plan.model_copy(update={"request": request, "proposal": proposal, "review": review})
    profile = WINDOW_DEFINITION_PROFILE if enabled else WINDOW_REASONING_PROFILE
    plan = plan.model_copy(
        update={
            "review": plan.review.model_copy(
                update={
                    "model_profile": plan.review.model_profile.model_copy(
                        update={"profile_id": profile}
                    )
                }
            )
        }
    )
    return FeaturePlan.model_validate_json(plan.canonical())


def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    rows = []
    for number, retained, enabled in (
        (2, False, False),
        (2, False, True),
        (3, False, True),
        (3, False, False),
        (2, True, False),
        (2, True, True),
    ):
        name = f"{'retained' if retained else 'feature'}-{number}-{'definitions' if enabled else 'control'}"
        path = ROOT / name
        path.mkdir()
        with WorkLedger(path / "ledger.db") as ledger:
            plan = prepare(ledger, number, retained, enabled)
            assert plan.review.max_attempts == 2 and plan.review.max_model_turns == 3
            (path / "plan.json").write_text(plan.canonical() + "\n")
            rows.append(
                dict(
                    name=name,
                    plan_digest=plan.digest(),
                    responses_reserved=len(plan.proposal.tasks) * 6,
                    tokens_reserved=len(plan.proposal.tasks) * 6 * 16384,
                )
            )
    for prefix in ("feature-2", "feature-3", "retained-2"):
        control = json.loads((ROOT / f"{prefix}-control/plan.json").read_text())
        enabled = json.loads((ROOT / f"{prefix}-definitions/plan.json").read_text())
        enabled["review"]["model_profile"]["profile_id"] = WINDOW_REASONING_PROFILE
        assert control == enabled
    (ROOT / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    (HERE / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    checks = []
    fixture = previous.fixture
    for name in ("feature-2-control", "retained-2-control"):
        path = ROOT / name
        with WorkLedger(path / "ledger.db") as ledger:
            plan = FeaturePlan.model_validate_json((path / "plan.json").read_bytes())
            repo = Repository(SnapshotSource(ledger.artifacts, plan.request.source))
            source = repo.select(
                tuple(p for p in plan.integration.execution_paths if p in repo.source.files),
                purpose="execution",
            ).bundle
            broker = DockerBroker(ledger.artifacts, plan.request.environments["python"].image)
            broker.qualify()
            good = SourceBundle(
                files={
                    **source.files,
                    fixture.IMPLEMENTATION: fixture.replace_method(
                        source.files[fixture.IMPLEMENTATION],
                        (fixture.HERE / "reference-method.py").read_text(),
                    ),
                    fixture.TEST: (fixture.HERE / "reference-tests.py").read_text(),
                }
            )
            for gate_id, gate in plan.integration.gates.items():
                for case in gate.cases:
                    result = broker.execute(
                        ledger.artifacts.publish(good.canonical().encode()),
                        case.command,
                        stdin=case.stdin,
                        seconds=case.seconds,
                        purpose="validation",
                    )
                    checks.append(
                        dict(name=name, gate=gate_id, execution=result.model_dump(mode="json"))
                    )
                    assert result.exit_code == 0, (name, gate_id)
            if name.startswith("retained"):
                case = plan.integration.gates["tests"].cases[0]
                result = broker.execute(
                    ledger.artifacts.publish(source.canonical().encode()),
                    case.command,
                    stdin=case.stdin,
                    seconds=case.seconds,
                    purpose="validation",
                )
                checks.append(
                    dict(
                        name=name, gate="retained-failure", execution=result.model_dump(mode="json")
                    )
                )
                assert result.exit_code != 0
    (ROOT / "preflight.json").write_text(json.dumps(checks, indent=2) + "\n")
    summaries = [
        dict(
            name=c["name"],
            gate=c["gate"],
            exit_code=c["execution"]["exit_code"],
            candidate_digest=c["execution"]["candidate_digest"],
            outcome=c["execution"]["outcome"],
        )
        for c in checks
    ]
    (HERE / "preflight.json").write_text(json.dumps(summaries, indent=2) + "\n")
    print(
        "Six plans frozen; reference and retained-failure preflights passed; 983040 tokens reserved",
        flush=True,
    )
    for row in rows:
        path = ROOT / row["name"]
        with WorkLedger(path / "ledger.db") as ledger:
            plan = FeaturePlan.model_validate_json((path / "plan.json").read_bytes())
            result = run_feature(ledger, plan, lambda: plan.request.source)
            (path / "result.json").write_text(result.canonical() + "\n")
            print(row["name"], result.status, flush=True)


if __name__ == "__main__":
    main()
