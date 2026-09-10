"""Project the retained failed turn with current window selection; no inference or edits."""

import json
from pathlib import Path

from gflo.broker import SourceBundle
from gflo.ledger import WorkLedger
from gflo.records import WorkAtom
from gflo.windows import WindowTargets, window_view

here = Path(__file__).resolve().parent
root = Path(".gflo/evidence/atomic-moves-v2/trial-1")
result = json.loads((root / "build/result.json").read_text())
with WorkLedger(root / "ledger.db") as ledger:
    state = ledger.status(result["feature_result"]["halted_atom"])
    atom = WorkAtom.model_validate_json(json.dumps(state["contract"]))
    events = state["attempts"][-1]["events"]
    event = next(
        e
        for e in reversed(events)
        if e["kind"] == "observation" and e["details"]["kind"] == "model"
    )
    evidence = json.loads(ledger.artifacts.read(event["details"]["digest"]))
    original = json.loads(ledger.artifacts.read(evidence["view_digest"]))
    targets = WindowTargets.model_validate_json(
        ledger.artifacts.read(evidence["window_targets_digest"])
    )
    draft = SourceBundle.model_validate_json(ledger.artifacts.read(targets.source_digest))
    diagnostics = tuple(
        ledger.artifacts.publish(json.dumps(d, sort_keys=True, separators=(",", ":")).encode())
        for d in original["diagnostics"]
    )
    paths = tuple(sorted({w["path"] for w in original["instruction"]["source_windows"].values()}))
    view, new_targets = window_view(
        ledger.artifacts,
        atom,
        original["source_digest"],
        draft,
        selected_paths=paths,
        diagnostic_digests=diagnostics,
    )
    before = [
        w
        for w in original["instruction"]["source_windows"].values()
        if w["path"].startswith("tests/")
    ]
    after = [
        w for w in view.instruction["source_windows"].values() if w["path"].startswith("tests/")
    ]
    assert not before and after
    assert any("assert rows[1]" in text for text in view.source_files.values())
    assert state == ledger.status(atom.atom_id)
    (here / "retained-view.json").write_text(
        json.dumps(
            dict(
                original_model_evidence=event["details"]["digest"],
                before=before,
                after=after,
                source_bytes=sum(len(t.encode()) for t in view.source_files.values()),
                ledger_unchanged=True,
                model_calls=0,
            ),
            indent=2,
        )
        + "\n"
    )
    print("Retained failing assertion is now visible; no ledger events, edits or inference.")
