"""Fresh fixed-budget follow-ups for the two reasoning-only feature halts."""

import json
from pathlib import Path

from campaign import prepare

from gflo.ledger import WorkLedger
from gflo.progression import FeaturePlan, run_feature

ROOT = Path(".gflo/evidence/window-reasoning-truncation-v1")
ROOT.mkdir(parents=True, exist_ok=False)
rows = []
for number in (2, 3):
    name = f"feature-{number}-reasoning"
    path = ROOT / name
    path.mkdir()
    with WorkLedger(path / "ledger.db") as ledger:
        plan = prepare(ledger, number, True, False)
        frozen = json.loads((Path(__file__).with_name("schedule.json")).read_text())
        original_digest = next(row["plan_digest"] for row in frozen if row["name"] == name)
        assert plan.digest() == original_digest
        (path / "plan.json").write_text(plan.canonical() + "\n")
        rows.append(
            dict(
                name=name, plan_digest=plan.digest(), responses_reserved=12, tokens_reserved=196608
            )
        )
(ROOT / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
print("Both unchanged plans frozen in fresh ledgers; 393216 tokens reserved", flush=True)
for row in rows:
    path = ROOT / row["name"]
    with WorkLedger(path / "ledger.db") as ledger:
        plan = FeaturePlan.model_validate_json((path / "plan.json").read_bytes())
        result = run_feature(ledger, plan, lambda: plan.request.source)
        (path / "result.json").write_text(result.canonical() + "\n")
        print(row["name"], result.status, flush=True)
