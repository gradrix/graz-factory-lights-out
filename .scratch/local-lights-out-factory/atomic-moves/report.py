"""Export every trial, independently audit accepted snapshots, and verify replay."""

import argparse
import importlib.util
import json
import sqlite3
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.autonomy import FeaturePolicy, build_feature
from gflo.broker import DockerBroker
from gflo.ledger import WorkLedger
from gflo.planning import RepositoryFeatureRequest
from gflo.repository import SnapshotSource

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--campaign", type=Path, default=Path(".gflo/evidence/atomic-moves-v2"))
parser.add_argument("--output", type=Path)
args = parser.parse_args()
ROOT = args.campaign
spec = importlib.util.spec_from_file_location(
    "prior_report", HERE.parent / "planner-recovery/report.py"
)
assert spec and spec.loader
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
rows = []
for name in ("trial-1", "trial-2", "trial-3"):
    path = ROOT / name
    fixture = json.loads((path / "fixture.json").read_text())
    request = RepositoryFeatureRequest.model_validate_json(json.dumps(fixture["request"]))
    policy = FeaturePolicy.model_validate_json(json.dumps(fixture["policy"]))
    state = json.loads((path / "build/planning/result.json").read_text())
    planning_store = ArtifactStore(path / "build/planning/artifacts")
    row = dict(
        name=name, fixture=fixture, planning=state, planner_responses=[], worker_responses=[]
    )
    for observation in state["observations"]:
        entry = prior.model_evidence(planning_store, observation["model_evidence_digest"])
        if "feedback_digest" in observation:
            entry["feedback"] = json.loads(planning_store.read(observation["feedback_digest"]))
        row["planner_responses"].append(entry)
    if (path / "build/planning/proposal.json").exists():
        row["proposal"] = json.loads((path / "build/planning/proposal.json").read_text())
    result = json.loads((path / "build/result.json").read_text())
    row["result"] = result
    with WorkLedger(path / "ledger.db") as ledger:
        with sqlite3.connect(path / "ledger.db") as connection:
            ids = [r[0] for r in connection.execute("select atom_id from atoms")]
        states = [ledger.status(atom) for atom in ids]
        row["atoms"] = states
        for atom in states:
            for attempt in atom["attempts"]:
                for event in attempt["events"]:
                    if event["kind"] == "observation" and event["details"]["kind"] == "model":
                        entry = prior.model_evidence(ledger.artifacts, event["details"]["digest"])
                        entry.update(atom=atom["atom_id"], attempt=attempt["ordinal"])
                        row["worker_responses"].append(entry)
        if result["status"] == "accepted":
            feature = result["feature_result"]
            source = SnapshotSource(ledger.artifacts, request.source)
            final = SnapshotSource(ledger.artifacts, feature["source"])
            changed = [p for p in final.files if source.files.get(p) != final.files[p]]
            assert set(changed) <= set(request.allowed_paths)
            assert set(source.files) <= set(final.files)
            row["preserved_original_files"] = len(source.files) - len(
                set(changed) & set(source.files)
            )
            row["changes"] = {p: final.read_bytes(p).decode() for p in changed}
            broker = DockerBroker(ledger.artifacts, request.environments["python"].image)
            broker.qualify()
            integration = ledger.status(feature["integration_atom"])
            execution = broker.execute(
                integration["candidate_digest"],
                ("python", "-B", "-c", (HERE / "heldout.py").read_text()),
                seconds=30,
                purpose="validation",
            )
            row["heldout"] = execution.model_dump(mode="json")
            # Fail closed and retain contradictory evidence if an accepted result fails audit.
            if execution.exit_code != 0:
                from gflo.records import AcceptanceFinding, WorkAtom

                atom = WorkAtom.model_validate_json(json.dumps(integration["contract"]))
                evidence = ledger.artifacts.publish(execution.canonical().encode())
                ledger.record_finding(
                    AcceptanceFinding(
                        atom_id=atom.atom_id,
                        contract_digest=atom.digest(),
                        candidate_digest=integration["candidate_digest"],
                        evidence_digest=evidence,
                        reason="Deferred commit failure does not preserve atomicity and recovery",
                    )
                )
                row["finding"] = evidence
            else:
                assert (
                    build_feature(ledger, request, policy, path / "build", lambda: request.source)[
                        "status"
                    ]
                    == "accepted"
                )
                assert states == [ledger.status(atom) for atom in ids]
                row["replay_unchanged"] = True
        usage = [
            r["response"]["usage"]
            for r in row["planner_responses"] + row["worker_responses"]
            if "response" in r
        ]
        row["cost"] = dict(responses=len(usage), total_tokens=sum(u["total_tokens"] for u in usage))
    rows.append(row)
    (args.output or HERE / "results.json").write_text(
        json.dumps(dict(campaign=ROOT.name, trials=rows), indent=2) + "\n"
    )
    print(
        name,
        result["status"],
        row["cost"],
        "heldout",
        row.get("heldout", {}).get("exit_code"),
        flush=True,
    )
