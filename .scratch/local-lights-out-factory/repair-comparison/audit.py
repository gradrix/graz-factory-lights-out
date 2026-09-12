"""Audit retained wire budgets without new inference."""

import json
from pathlib import Path

from probe import HERE

from gflo.artifacts import ArtifactStore

ROOT = Path(".gflo/evidence/repair-comparison-v2")
store = ArtifactStore(ROOT / "factory/ledger.db.artifacts")
rows = []
for path in store.root.rglob("*"):
    if not path.is_file():
        continue
    try:
        obj = json.loads(path.read_text())
    except (ValueError, UnicodeError):
        continue
    if not isinstance(obj, dict) or "exchanges" not in obj or "manifest_digest" not in obj:
        continue
    exchanges = {e["path"]: e for e in obj["exchanges"]}
    if "/v1/chat/completions" not in exchanges:
        continue
    wire = json.loads(store.read(exchanges["/v1/chat/completions"]["request_digest"]))
    token = json.loads(store.read(exchanges["/tokenize"]["request_digest"]))
    manifest = json.loads(store.read(obj["manifest_digest"]))
    response = json.loads(store.read(exchanges["/v1/chat/completions"]["response_digest"]))
    assert wire["messages"] == token["messages"]
    assert (
        wire["chat_template_kwargs"] == token["chat_template_kwargs"] == {"enable_thinking": False}
    )
    assert wire["max_tokens"] == manifest["output_reserved"] == 6144
    assert manifest["prompt_tokens"] + 6144 <= manifest["total_limit"] == 16384
    assert wire["seed"] == 42 and wire["temperature"] == 0
    rows.append(response["usage"])
assert len(rows) == 6
minimal = json.loads((ROOT / "minimal/results.json").read_text())
assert len(minimal) <= 6
summary = dict(
    factory_responses=len(rows),
    factory_tokens=sum(r["total_tokens"] for r in rows),
    minimal_responses=len(minimal),
    minimal_tokens=sum(r["usage"]["total_tokens"] for r in minimal),
    factory_status=json.loads((ROOT / "factory/build/result.json").read_text())["status"],
    minimal_passed=any(r["passed"] for r in minimal),
    minimal_unique_candidates=len({r["candidate_digest"] for r in minimal}),
)
(HERE / "audit.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
