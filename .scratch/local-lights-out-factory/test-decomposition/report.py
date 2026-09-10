"""Export trial records and aggregate costs without restarting any work."""

import argparse
import ast
import json
import sqlite3
from collections import Counter
from pathlib import Path

from gflo.ledger import Conflict, WorkLedger
from gflo.progression import FeaturePlan, run_feature


def trial_report(root):
    result = json.loads((root / "result.json").read_text())
    report = {
        "name": root.name,
        "status": result["status"],
        "atoms": [],
        "responses": [],
        "reserved_model_responses": 6,
        "reserved_tokens": 73728,
    }
    with WorkLedger(root / "ledger.db") as ledger:
        with sqlite3.connect(root / "ledger.db") as connection:
            atom_ids = [
                r[0] for r in connection.execute("select atom_id from atoms order by atom_id")
            ]
        states = [ledger.status(atom) for atom in atom_ids]
        report["atoms"] = states
        for state in states:
            for attempt in state["attempts"]:
                for event in attempt["events"]:
                    if event["kind"] != "observation" or event["details"]["kind"] != "model":
                        continue
                    evidence = json.loads(ledger.artifacts.read(event["details"]["digest"]))
                    row = {
                        "atom": state["atom_id"],
                        "attempt": attempt["ordinal"],
                        "evidence_digest": event["details"]["digest"],
                        "evidence": evidence,
                    }
                    for exchange in evidence["exchanges"]:
                        if exchange["path"] == "/v1/chat/completions":
                            row["response"] = json.loads(
                                ledger.artifacts.read(exchange["response_digest"])
                            )
                    report["responses"].append(row)
        plan = FeaturePlan.model_validate_json((root / "plan.json").read_bytes())
        report["plan"] = plan.model_dump(mode="json")
        if result["status"] == "accepted":
            selection = result["integration_selection"]
            files = selection["bundle"]["files"]
            report["tests"] = {p: t for p, t in files.items() if p.startswith("tests/")}
            report["integrated_file_identities"] = selection["file_identities"]
            bodies = Counter()
            for text in report["tests"].values():
                for node in ast.walk(ast.parse(text)):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
                        bodies[ast.dump(ast.Module(body=node.body, type_ignores=[]))] += 1
            report["test_functions"] = sum(bodies.values())
            report["exact_duplicate_test_bodies"] = sum(n - 1 for n in bodies.values())
            try:
                replay = run_feature(ledger, plan, lambda: plan.request.source)
                assert replay.status == "accepted"
                report["reuse_status"] = "accepted"
            except Conflict as error:
                assert any(state.get("acceptance_challenged") for state in states)
                report["reuse_status"] = "blocked"
                report["replay_reason"] = str(error)
            assert states == [ledger.status(a) for a in atom_ids]
            report["replay_unchanged"] = True
        usage = [r["response"]["usage"] for r in report["responses"] if "response" in r]
        report["cost"] = {
            "responses": len(usage),
            "prompt_tokens": sum(u["prompt_tokens"] for u in usage),
            "completion_tokens": sum(u["completion_tokens"] for u in usage),
            "total_tokens": sum(u["total_tokens"] for u in usage),
            "model_seconds": sum(
                r["evidence"].get("elapsed_seconds", 0) for r in report["responses"]
            ),
            "max_prompt_tokens": max((u["prompt_tokens"] for u in usage), default=0),
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    schedule = json.loads((args.campaign / "schedule.json").read_text())
    rows = [
        trial_report(args.campaign / name)
        for name, _ in schedule
        if (args.campaign / name / "result.json").exists()
    ]
    result = {
        "campaign": args.campaign.name,
        "schedule": schedule,
        "trials": rows,
        "preflight": json.loads((args.campaign / "preflight.json").read_text()),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    for row in rows:
        print(row["name"], row["status"], row["cost"])


if __name__ == "__main__":
    main()
