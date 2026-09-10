"""Read-only review packets for exhausted work; no retry reset or model routing."""

from __future__ import annotations

import json
from typing import Any

from gflo.broker import SourceBundle
from gflo.ledger import WorkLedger
from gflo.reporting import cost_report


def review_handoff(ledger: WorkLedger, atom_id: str) -> dict[str, Any]:
    state = ledger.status(atom_id)
    if state["status"] != "quarantined":
        raise ValueError("Review escalation requires exhausted, quarantined work")
    plan = json.loads(ledger.run_plan(atom_id))
    drafts = []
    diagnostics = []
    for attempt in state["attempts"]:
        for event in attempt["events"]:
            if event["kind"] == "candidate":
                drafts.append(event["details"]["digest"])
            if event["kind"] != "observation":
                continue
            kind = event["details"]["kind"]
            if kind in ("development", "diagnostic"):
                record = json.loads(ledger.artifacts.read(event["details"]["digest"]))
                if kind == "development":
                    drafts.append(record["draft_digest"])
                else:
                    diagnostics.append(record)
    latest = drafts[-1] if drafts else None
    draft = SourceBundle.model_validate_json(ledger.artifacts.read(latest)) if latest else None
    return {
        "schema_version": 1,
        "kind": "review-handoff-v1",
        "atom_id": atom_id,
        "status": "needs-review",
        "reason": "Finite worker attempts exhausted; review required before further work.",
        "run_plan": plan,
        "latest_unaccepted_draft_digest": latest,
        "latest_unaccepted_draft": draft.model_dump(mode="json") if draft else None,
        "accepted_predecessors": state["contract"]["dependency_artifacts"],
        "diagnostics": diagnostics,
        "cost": cost_report(ledger, atom_id)["totals"],
        "next_action": (
            "Review the draft and diagnostics. A replacement task needs a new explicit contract, "
            "budget and unchanged or separately reviewed acceptance checks. Never reset quarantine "
            "or treat this draft as accepted. Original source and completed work remain retained."
        ),
    }
