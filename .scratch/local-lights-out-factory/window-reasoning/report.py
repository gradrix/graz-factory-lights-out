"""Audit accepted results, verify wire budgets, and export all runs without retrying halts."""

import argparse
import importlib.util
import json
from pathlib import Path

from gflo.broker import DockerBroker
from gflo.contracts import WINDOW_REASONING_PROFILE
from gflo.ledger import WorkLedger
from gflo.progression import FeaturePlan
from gflo.records import AcceptanceFinding, WorkAtom

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--campaign", type=Path, default=Path(".gflo/evidence/window-reasoning-v1"))
parser.add_argument("--output", type=Path, default=HERE / "results.json")
args = parser.parse_args()
ROOT = args.campaign
spec = importlib.util.spec_from_file_location(
    "prior_report", HERE.parent / "test-decomposition/report.py"
)
assert spec and spec.loader
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
rows = []
for scheduled in json.loads((ROOT / "schedule.json").read_text()):
    path = ROOT / scheduled["name"]
    result = json.loads((path / "result.json").read_text())
    plan = FeaturePlan.model_validate_json((path / "plan.json").read_bytes())
    heldout = None
    if result["status"] == "accepted":
        with WorkLedger(path / "ledger.db") as ledger:
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
                evidence = ledger.artifacts.publish(heldout.canonical().encode())
                ledger.record_finding(
                    AcceptanceFinding(
                        atom_id=atom.atom_id,
                        contract_digest=atom.digest(),
                        candidate_digest=state["candidate_digest"],
                        evidence_digest=evidence,
                        reason="Deferred commit recovery audit failed",
                    )
                )
    row = prior.trial_report(path)
    row["reserved_model_responses"] = scheduled["responses_reserved"]
    row["reserved_tokens"] = scheduled["tokens_reserved"]
    row["heldout"] = heldout.model_dump(mode="json") if heldout else None
    # Every completion request must match its tokenizer and the frozen profile/budget.
    with WorkLedger(path / "ledger.db") as ledger:
        for response in row["responses"]:
            exchanges = response["evidence"]["exchanges"]
            requests = {
                e["path"]: json.loads(ledger.artifacts.read(e["request_digest"]))
                for e in exchanges
                if e["path"] in ("/tokenize", "/v1/chat/completions")
            }
            tokenize = requests["/tokenize"]
            generate = requests["/v1/chat/completions"]
            expected = {"enable_thinking": False}
            if plan.review.model_profile.profile_id == WINDOW_REASONING_PROFILE:
                expected = {"enable_thinking": True, "reasoning_effort": "low"}
            assert tokenize["chat_template_kwargs"] == generate["chat_template_kwargs"] == expected
            assert generate["max_tokens"] == 6144
            assert tokenize["messages"] == generate["messages"]
            manifest = json.loads(ledger.artifacts.read(response["evidence"]["manifest_digest"]))
            assert manifest["output_reserved"] == 6144 and manifest["total_limit"] == 16384
    row["wire_verified"] = True
    rows.append(row)
    args.output.write_text(
        json.dumps(
            dict(
                campaign=ROOT.name,
                schedule=json.loads((ROOT / "schedule.json").read_text()),
                trials=rows,
            ),
            indent=2,
        )
        + "\n"
    )
    print(
        row["name"],
        row["status"],
        row["cost"],
        "audit",
        row["heldout"]["exit_code"] if row["heldout"] else None,
        flush=True,
    )
