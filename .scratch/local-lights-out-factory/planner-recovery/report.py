"""Export planner observations and worker outcomes without resuming halted work."""

import argparse
import json
import sqlite3
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.autonomy import FeaturePolicy, build_feature
from gflo.ledger import WorkLedger
from gflo.planning import RepositoryFeatureRequest

BASE = Path(__file__).parent.parent / "window-feature-qualification"


def model_evidence(store, digest):
    evidence = json.loads(store.read(digest))
    row = {"evidence_digest": digest, "evidence": evidence}
    if "view_digest" in evidence:
        view = json.loads(store.read(evidence["view_digest"]))
        row["source_labels"] = list(view["source_files"])
        row["visible_source_bytes"] = sum(
            len(text.encode()) for text in view["source_files"].values()
        )
    for exchange in evidence.get("exchanges", []):
        if exchange["path"] == "/v1/chat/completions":
            row["response"] = json.loads(store.read(exchange["response_digest"]))
    return row


def export(root):
    rows = []
    for name, kind in json.loads((root / "schedule.json").read_text()):
        path = root / name
        planning = path if kind == "navigation" else path / "build/planning"
        if not (planning / "result.json").exists():
            continue
        state = json.loads((planning / "result.json").read_text())
        store = ArtifactStore(planning / "artifacts")
        row = {
            "name": name,
            "kind": kind,
            "planning": state,
            "planner_responses": [],
            "worker_responses": [],
        }
        for observation in state["observations"]:
            response = model_evidence(store, observation["model_evidence_digest"])
            if "feedback_digest" in observation:
                response["feedback"] = json.loads(store.read(observation["feedback_digest"]))
            row["planner_responses"].append(response)
        if (planning / "proposal.json").exists():
            row["proposal"] = json.loads((planning / "proposal.json").read_text())
            if kind == "navigation":
                row["correct_return_quoted"] = "return 41" in row["proposal"]["rationale"]
        if kind == "feature" and (path / "build/result.json").exists():
            result = json.loads((path / "build/result.json").read_text())
            # Full source is reproducible from the fixture; retain identities, not huge copies.
            selection = result.get("feature_result", {}).get("integration_selection")
            if selection:
                selection.pop("bundle", None)
            row["result"] = result
            with WorkLedger(path / "ledger.db") as ledger:
                with sqlite3.connect(path / "ledger.db") as connection:
                    ids = [r[0] for r in connection.execute("select atom_id from atoms")]
                states = [ledger.status(atom) for atom in ids]
                row["atoms"] = states
                for atom in states:
                    for attempt in atom["attempts"]:
                        for event in attempt["events"]:
                            if (
                                event["kind"] == "observation"
                                and event["details"]["kind"] == "model"
                            ):
                                row["worker_responses"].append(
                                    model_evidence(ledger.artifacts, event["details"]["digest"])
                                )
                if result["status"] == "accepted":
                    fixture = json.loads((BASE / "window-feature-v4-fixture.json").read_text())
                    request = RepositoryFeatureRequest.model_validate_json(
                        json.dumps(fixture["request"])
                    )
                    policy = FeaturePolicy.model_validate_json(json.dumps(fixture["policy"]))
                    replay = build_feature(
                        ledger, request, policy, path / "build", lambda: request.source
                    )
                    assert replay["status"] == "accepted"
                    assert states == [ledger.status(atom) for atom in ids]
                    row["replay_unchanged"] = True
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = export(args.campaign)
    args.output.write_text(
        json.dumps({"campaign": args.campaign.name, "trials": rows}, indent=2) + "\n"
    )
    for row in rows:
        print(
            row["name"],
            row["planning"]["status"],
            len(row["planner_responses"]),
            row.get("result", {}).get("status", "draft-only"),
            row.get("correct_return_quoted", ""),
        )


if __name__ == "__main__":
    main()
