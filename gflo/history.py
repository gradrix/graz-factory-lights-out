"""Human-reviewable candidate diffs derived from immutable Attempt evidence."""

from __future__ import annotations

import difflib
import json
from typing import Any

from gflo.broker import SourceBundle
from gflo.controller import RunPlan
from gflo.integration import IntegrationPlan
from gflo.ledger import WorkLedger


def _diff(path: str, before: str | None, after: str | None) -> str:
    lines = difflib.unified_diff(
        [] if before is None else before.splitlines(keepends=True),
        [] if after is None else after.splitlines(keepends=True),
        fromfile="/dev/null" if before is None else "base/" + path,
        tofile="/dev/null" if after is None else "candidate/" + path,
    )
    return "".join(
        line if line.endswith("\n") else line + "\n\\ No newline at end of file\n" for line in lines
    )


def change_history(ledger: WorkLedger, atom_id: str) -> dict[str, Any]:
    state = ledger.status(atom_id)
    raw = ledger.run_plan(atom_id)
    plan: RunPlan | IntegrationPlan
    if json.loads(raw).get("kind") == "prepared-integration-v1":
        plan = IntegrationPlan.model_validate_json(raw)
    else:
        plan = RunPlan.model_validate_json(raw)
    if plan.atom.model_dump(mode="json") != state["contract"]:
        raise ValueError("Prepared plan differs from task history")
    source = plan.base if isinstance(plan, IntegrationPlan) else plan.source
    baseline = SourceBundle.model_validate_json(ledger.artifacts.read(source.digest()))
    for finding in state["acceptance_findings"]:
        ledger.artifacts.verify(finding["evidence_digest"])
    attempts = []
    for attempt in state["attempts"]:
        candidates = []
        outcome = "in-progress"
        failures = []
        model_evidence = []
        for event in attempt["events"]:
            if event["kind"] in ("failed", "expired", "accepted"):
                outcome = event["kind"]
            if event["kind"] in ("failed", "expired"):
                failures.append(event["details"]["reason"])
            if event["kind"] == "observation" and event["details"]["kind"] == "model":
                digest = event["details"]["digest"]
                ledger.artifacts.verify(digest)
                model_evidence.append(digest)
            if event["kind"] != "candidate":
                continue
            digest = event["details"]["digest"]
            candidate = SourceBundle.model_validate_json(ledger.artifacts.read(digest))
            changes = []
            for path in sorted(baseline.files.keys() | candidate.files.keys()):
                before, after = baseline.files.get(path), candidate.files.get(path)
                if before != after:
                    changes.append(
                        {
                            "path": path,
                            "kind": "added"
                            if before is None
                            else "deleted"
                            if after is None
                            else "modified",
                            "diff": _diff(path, before, after),
                        }
                    )
            candidates.append(
                {
                    "digest": digest,
                    "event_id": event["event_id"],
                    "recorded_at": event["recorded_at"],
                    "changes": changes,
                }
            )
        for receipt in attempt["gate_receipts"]:
            ledger.artifacts.verify(receipt["evidence_digest"])
        attempts.append(
            {
                "attempt_id": attempt["attempt_id"],
                "ordinal": attempt["ordinal"],
                "controller_owner": attempt["owner"],
                "outcome": outcome,
                "failures": failures,
                "retry_plan": attempt["retry_plan"],
                "model_evidence": model_evidence,
                "candidates": candidates,
                "gate_receipts": attempt["gate_receipts"],
            }
        )
    return {
        "schema_version": 1,
        "atom_id": atom_id,
        "status": state["status"],
        "objective": plan.atom.objective,
        "source_revision": plan.atom.source_revision,
        "baseline_digest": baseline.digest(),
        "model_profile": plan.model_profile.model_dump(mode="json")
        if isinstance(plan, RunPlan)
        else None,
        "accepted_candidate_digest": state["candidate_digest"]
        if state["status"] == "accepted"
        else None,
        "acceptance_findings": state["acceptance_findings"],
        "acceptance_challenged": state["acceptance_challenged"],
        "attempts": attempts,
        "scope": "Each published candidate compared with the immutable task baseline; "
        "failed and unaccepted candidates are not integrated product changes. "
        "Worker explanations are not inferred from diffs.",
    }


def render_history(history: dict[str, Any]) -> str:
    lines = [
        f"Task {history['atom_id']} — {history['status']}",
        history["objective"],
        f"Base: {history['source_revision']} ({history['baseline_digest']})",
    ]
    for finding in history.get("acceptance_findings", []):
        lines.append("Reuse blocked by later evidence: " + finding["reason"])
        lines.append("Finding evidence: " + finding["evidence_digest"])
    for attempt in history["attempts"]:
        lines.append(
            f"\nAttempt {attempt['ordinal']} ({attempt['attempt_id']}): {attempt['outcome']}"
        )
        lines.extend("Failure: " + reason for reason in attempt["failures"])
        if not attempt["candidates"]:
            lines.append("No published candidate.")
        for candidate in attempt["candidates"]:
            lines.append("Candidate: " + candidate["digest"])
            if not candidate["changes"]:
                lines.append("No source changes.")
            for change in candidate["changes"]:
                lines.append(f"{change['kind']}: {change['path']}")
                lines.append(change["diff"])
        lines.extend(
            f"Gate {r['gate_id']}: {r['outcome']} ({r['evidence_digest']})"
            for r in attempt["gate_receipts"]
        )
    lines.append("\n" + history["scope"])
    # Source/diagnostics are untrusted. Keep terminal controls visibly escaped.
    text = "\n".join(lines) + "\n"
    return "".join(c if c in "\n\t" or c.isprintable() else ascii(c)[1:-1] for c in text)
