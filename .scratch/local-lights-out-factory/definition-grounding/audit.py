"""Export narrow source-visibility evidence from the retained run; no inference."""

import json
from pathlib import Path

from gflo.artifacts import ArtifactStore

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/window-reasoning-truncation-v1/feature-2-reasoning")
report = json.loads((HERE.parent / "window-reasoning/truncation-results.json").read_text())
trial = report["trials"][0]
store = ArtifactStore(ROOT / "ledger.db.artifacts")
rows = []
for response in trial["responses"]:
    evidence = response["evidence"]
    view = json.loads(store.read(evidence["view_digest"]))
    exchange = next(e for e in evidence["exchanges"] if e["path"] == "/v1/chat/completions")
    request = json.loads(store.read(exchange["request_digest"]))
    wire = "\n".join(m["content"] for m in request["messages"])
    manifest = json.loads(store.read(evidence["manifest_digest"]))
    assert manifest["view_digest"] == evidence["view_digest"]
    assert manifest["prompt_tokens"] + manifest["output_reserved"] <= manifest["total_limit"]
    reply = json.loads(store.read(exchange["response_digest"]))["choices"][0]
    content = reply["message"].get("content")
    result = json.loads(content) if content else {}
    definitions = [
        d
        for d in view["instruction"]["definitions"]
        if d["qualified_name"] in ("RecorderDb.createPlayer", "RecorderDb.createGame")
    ]
    assert len(definitions) == 2
    assert all(f"def {name}(" not in wire for name in ("createPlayer", "createGame"))
    rows.append(
        dict(
            atom=response["atom"],
            attempt=response["attempt"],
            view_digest=evidence["view_digest"],
            request_digest=exchange["request_digest"],
            manifest_digest=evidence["manifest_digest"],
            source_digest=view["source_digest"],
            windows=list(view["instruction"]["source_windows"].values()),
            definitions=definitions,
            signatures_in_wire={
                name: f"def {name}(" in wire for name in ("createPlayer", "createGame")
            },
            omissions=view["instruction"]["window_omissions"],
            index_truncated=view["instruction"]["definition_index"]["truncated"],
            prompt_tokens=manifest["prompt_tokens"],
            output_reserved=manifest["output_reserved"],
            total_limit=manifest["total_limit"],
            result_kind=result.get("kind"),
            read=result if result.get("kind") == "read_window" else None,
            helper_calls=[
                line.strip()
                for text in result.get("changes", {}).values()
                for line in text.splitlines()
                if "createPlayer(" in line or "createGame(" in line
            ],
        )
    )

# Preserve just the real provider and failed call site needed for the CPU visibility
# reproduction. These are data, never executed or supplied as repaired candidates.
repair = trial["responses"][4]["evidence"]
assert rows[3]["result_kind"] == rows[4]["result_kind"] == "candidate"
assert any("1000, 1000" in line for line in rows[3]["helper_calls"])
assert not any("1000, 1000" in line for line in rows[4]["helper_calls"])
assert any("createGame(1000, 3," in line for line in rows[4]["helper_calls"])
view = json.loads(store.read(repair["view_digest"]))
base = json.loads(store.read(view["source_digest"]))
earlier = trial["responses"][3]["evidence"]
exchange = next(e for e in earlier["exchanges"] if e["path"] == "/v1/chat/completions")
draft = json.loads(
    json.loads(store.read(exchange["response_digest"]))["choices"][0]["message"]["content"]
)
fixture = dict(
    provenance=dict(
        view_digest=repair["view_digest"],
        source_digest=view["source_digest"],
        response_digest=exchange["response_digest"],
    ),
    provider=base["files"]["game_server/state/recorderdb.py"],
    caller=draft["changes"]["tests/test_atomic_moves.py"],
    diagnostic="tests/test_atomic_moves.py:19: TypeError: RecorderDb.createPlayer() "
    "takes from 2 to 3 positional arguments but 5 were given",
)
(HERE / "fixture.json").write_text(json.dumps(fixture, indent=2) + "\n")
(HERE / "visibility.json").write_text(json.dumps(rows, indent=2) + "\n")
print(f"Audited {len(rows)} retained requests; exported immutable source/call-site fixture.")
