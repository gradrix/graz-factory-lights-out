"""Replay the unedited failed draft and next response through parser and real gates."""

import importlib.util
import json
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.ledger import WorkLedger
from gflo.records import WorkAtom
from gflo.windows import parse_window_result, window_view
from gflo.worker import WorkerError

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "fixture", here.parent / "test-decomposition/campaign.py"
)
assert spec and spec.loader
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)
old = json.loads((here.parent / "test-decomposition/results.json").read_text())
trial = next(t for t in old["trials"] if t["name"] == "solo-2")
contents = [r["response"]["choices"][0]["message"]["content"] for r in trial["responses"]]
base = campaign.source()
atom = WorkAtom.model_validate_json(json.dumps(trial["atoms"][0]["contract"]))
root = Path(".gflo/evidence/draft-repair-retained-v2")
root.mkdir(parents=True, exist_ok=False)
with WorkLedger(root / "ledger.db") as ledger:
    digest = ledger.artifacts.publish(base.canonical().encode())
    draft = SourceBundle(files=base.files | json.loads(contents[0])["changes"])
    _, targets = window_view(ledger.artifacts, atom, digest, draft)
    try:
        parse_window_result(contents[1], atom, draft, targets)
    except WorkerError:
        pass
    else:
        raise AssertionError("Legacy parser must reject retained replacement")
    candidate = parse_window_result(contents[1], atom, draft, targets, base_source=base)
    repaired = SourceBundle(files=draft.files | candidate.changes)
    image = json.loads((here.parent / "test-decomposition/fixture.json").read_text())["image"]
    broker = DockerBroker(ledger.artifacts, image)
    broker.qualify()
    case = campaign.gate(
        ["tests/test_all.py"], ["unclamped", "constant", "caller", "permissive"]
    ).cases[0]
    results = {}
    for name, bundle in (("failed_draft", draft), ("retained_repair", repaired)):
        ref = ledger.artifacts.publish(bundle.canonical().encode())
        execution = broker.execute(ref, case.command, seconds=case.seconds, purpose="validation")
        results[name] = execution.model_dump(mode="json")
    (root / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    assert results["failed_draft"]["exit_code"] != 0
    assert results["retained_repair"]["exit_code"] == 0
    print("Original draft fails; unedited retained repair passes full fault gates.")
