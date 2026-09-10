"""Fresh solo-worker trials using the frozen decomposition fixture and gates."""

import importlib.util
from pathlib import Path

from gflo.ledger import WorkLedger
from gflo.progression import run_feature

fixture = Path(__file__).resolve().parent.parent / "test-decomposition/campaign.py"
spec = importlib.util.spec_from_file_location("decomposition", fixture)
assert spec and spec.loader
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)
root = Path(".gflo/evidence/draft-repair-v1")
root.mkdir(parents=True, exist_ok=False)
for name in ("solo-1", "solo-2", "solo-3"):
    trial = root / name
    trial.mkdir()
    with WorkLedger(trial / "ledger.db") as ledger:
        feature = campaign.plan(ledger.artifacts, name, False)
        (trial / "plan.json").write_text(feature.canonical() + "\n")
        result = run_feature(ledger, feature, lambda: feature.request.source)
        (trial / "result.json").write_text(result.canonical() + "\n")
        print(name, result.status, flush=True)
