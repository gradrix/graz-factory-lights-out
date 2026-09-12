"""Audit frozen profile requests, accepted results and unchanged replay."""

import importlib.util
import json
import sqlite3
from pathlib import Path

from gflo.broker import DockerBroker
from gflo.ledger import WorkLedger
from gflo.progression import FeaturePlan, run_feature
from gflo.records import AcceptanceFinding, WorkAtom

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/definition-context-v1")
spec = importlib.util.spec_from_file_location("prior", HERE.parent / "test-decomposition/report.py")
assert spec and spec.loader
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)

rows = []
raw_rows = []
for scheduled in json.loads((ROOT / "schedule.json").read_text()):
    path = ROOT / scheduled["name"]
    if not (path / "result.json").exists():
        continue
    plan = FeaturePlan.model_validate_json((path / "plan.json").read_bytes())
    result = json.loads((path / "result.json").read_text())
    heldout = None
    with WorkLedger(path / "ledger.db") as ledger:
        if result["status"] == "accepted":
            state = ledger.status(result["integration_atom"])
            broker = DockerBroker(ledger.artifacts, plan.request.environments["python"].image)
            broker.qualify()
            heldout = broker.execute(
                state["candidate_digest"],
                ("python", "-B", "-c", (HERE.parent / "atomic-moves/heldout.py").read_text()),
                seconds=30,
                purpose="validation",
            )
            if heldout.exit_code != 0:
                atom = WorkAtom.model_validate_json(json.dumps(state["contract"]))
                ledger.record_finding(
                    AcceptanceFinding(
                        atom_id=atom.atom_id,
                        contract_digest=atom.digest(),
                        candidate_digest=state["candidate_digest"],
                        evidence_digest=ledger.artifacts.publish(heldout.canonical().encode()),
                        reason="Independent deferred-commit recovery audit failed",
                    )
                )
        row = prior.trial_report(path)
        wire = []
        for response in row["responses"]:
            evidence = response["evidence"]
            exchanges = {e["path"]: e for e in evidence["exchanges"]}
            if "/v1/chat/completions" not in exchanges:
                continue
            req = json.loads(
                ledger.artifacts.read(exchanges["/v1/chat/completions"]["request_digest"])
            )
            tok = json.loads(ledger.artifacts.read(exchanges["/tokenize"]["request_digest"]))
            manifest = json.loads(ledger.artifacts.read(evidence["manifest_digest"]))
            assert req["messages"] == tok["messages"]
            assert (
                req["chat_template_kwargs"]
                == tok["chat_template_kwargs"]
                == {"enable_thinking": True, "reasoning_effort": "low"}
            )
            assert req["max_tokens"] == manifest["output_reserved"] == 6144
            assert manifest["prompt_tokens"] + 6144 <= manifest["total_limit"] == 16384
            view = json.loads(req["messages"][1]["content"])
            context = view["instruction"].get("definition_context")
            assert bool(context) == scheduled["name"].endswith("definitions")
            wire.append(
                dict(
                    view_digest=evidence["view_digest"],
                    manifest_digest=evidence["manifest_digest"],
                    definition_context=context,
                    source_bytes=sum(len(t.encode()) for t in view["source_files"].values()),
                )
            )
        row["wire"] = wire
        row["heldout"] = heldout.model_dump(mode="json") if heldout else None
        row.update({k: v for k, v in scheduled.items() if k != "name"})
        # Terminal failures must replay without consuming new attempts too.
        if result["status"] != "accepted":
            with sqlite3.connect(path / "ledger.db") as db:
                ids = [r[0] for r in db.execute("select atom_id from atoms")]
            before = [ledger.status(a) for a in ids]
            replay = run_feature(ledger, plan, lambda: plan.request.source)
            assert replay.status == result["status"]
            assert before == [ledger.status(a) for a in ids]
            row["replay_unchanged"] = True
    raw_rows.append(row)
    (ROOT / "report.json").write_text(json.dumps(raw_rows, indent=2) + "\n")
    portable = {k: v for k, v in row.items() if k not in ("atoms", "responses", "plan", "heldout")}
    portable["atoms"] = [
        dict(
            atom_id=a["atom_id"],
            status=a["status"],
            attempts=len(a["attempts"]),
            candidate_digest=a.get("candidate_digest"),
        )
        for a in row["atoms"]
    ]
    portable["evidence_digests"] = [r["evidence_digest"] for r in row["responses"]]
    if heldout:
        portable["heldout"] = dict(
            exit_code=heldout.exit_code, candidate_digest=heldout.candidate_digest
        )
    rows.append(portable)
    (HERE / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(
        row["name"],
        row["status"],
        row["cost"],
        "hints",
        sum(bool(w["definition_context"] and w["definition_context"]["hints"]) for w in wire),
        flush=True,
    )
