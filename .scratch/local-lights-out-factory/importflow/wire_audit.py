"""Audit actual tokenizer/generation messages and reserved budgets, without inference."""

import argparse
import json
from pathlib import Path

from gflo.artifacts import ArtifactStore

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/importflow-v1")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--prepared", action="store_true")
parser.add_argument("--resume", action="store_true")
args = parser.parse_args()
if args.prepared:
    ROOT = Path(".gflo/evidence/importflow-prepared-v1")
if args.resume:
    ROOT = Path(".gflo/evidence/importflow-resume-v1")
rows = []
for job in json.loads((ROOT / "schedule.json").read_text()):
    row = dict(name=job["name"], responses=0, max_prompt_tokens=0, profiles=set())
    for directory in (
        ROOT / job["name"] / "ledger.db.artifacts",
        ROOT / job["name"] / "build/planning/artifacts",
    ):
        if not directory.exists():
            continue
        store = ArtifactStore(directory)
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            try:
                evidence = json.loads(path.read_text())
            except (ValueError, UnicodeError):
                continue
            if (
                not isinstance(evidence, dict)
                or "exchanges" not in evidence
                or "manifest_digest" not in evidence
            ):
                continue
            exchanges = {e["path"]: e for e in evidence["exchanges"]}
            if "/v1/chat/completions" not in exchanges:
                continue
            request = json.loads(store.read(exchanges["/v1/chat/completions"]["request_digest"]))
            token = json.loads(store.read(exchanges["/tokenize"]["request_digest"]))
            manifest = json.loads(store.read(evidence["manifest_digest"]))
            assert request["messages"] == token["messages"]
            assert (
                request["chat_template_kwargs"]
                == token["chat_template_kwargs"]
                == {"enable_thinking": False}
            )
            assert request["max_tokens"] == manifest["output_reserved"]
            assert (
                manifest["prompt_tokens"] + manifest["output_reserved"] <= manifest["total_limit"]
            )
            assert manifest["total_limit"] <= 16384
            row["responses"] += 1
            row["max_prompt_tokens"] = max(row["max_prompt_tokens"], manifest["prompt_tokens"])
    assert row["responses"] <= job["max_responses"]
    row.pop("profiles")
    rows.append(row)
(
    HERE
    / (
        "resume-wire-audit.json"
        if args.resume
        else "prepared-wire-audit.json"
        if args.prepared
        else "wire-audit.json"
    )
).write_text(json.dumps(rows, indent=2) + "\n")
print(rows)
