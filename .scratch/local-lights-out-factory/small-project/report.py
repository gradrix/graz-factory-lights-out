"""Retain all project outcomes, independently audit acceptance, export exact bytes."""

import argparse
import importlib.util
import json
import sqlite3
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.autonomy import FeaturePolicy, build_feature
from gflo.broker import DockerBroker
from gflo.ledger import Conflict, WorkLedger
from gflo.model import LocalModel
from gflo.planning import RepositoryFeatureRequest
from gflo.progression import FeaturePlan, run_feature
from gflo.records import AcceptanceFinding, WorkAtom
from gflo.repository import SnapshotSource

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repair", action="store_true")
parser.add_argument("--fixed-symbols", action="store_true")
parser.add_argument("--scoped-requirements", action="store_true")
args = parser.parse_args()
if args.scoped_requirements:
    args.fixed_symbols = True
if args.fixed_symbols:
    args.repair = True
ROOT = Path(
    ".gflo/evidence/small-project-repair-v1" if args.repair else ".gflo/evidence/small-project-v1"
)
OUTPUT = HERE / ("repair-results.json" if args.repair else "results.json")
if args.fixed_symbols:
    ROOT = Path(".gflo/evidence/small-project-repair-v2")
    OUTPUT = HERE / "repair-v2-results.json"
if args.scoped_requirements:
    ROOT = Path(".gflo/evidence/small-project-repair-v3")
    OUTPUT = HERE / "repair-v3-results.json"
spec = importlib.util.spec_from_file_location("prior", HERE.parent / "planner-recovery/report.py")
assert spec and spec.loader
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


def no_model(*args, **kwargs):
    raise AssertionError("Replay attempted new model work")


class ReplayModel(LocalModel):
    def turn(self, *args, **kwargs):
        raise AssertionError("Replay attempted inference")


rows = []
raw_rows = []
for scheduled in json.loads((ROOT / "schedule.json").read_text()):
    path = ROOT / scheduled["name"]
    if not (path / "build/result.json").exists():
        continue
    result = json.loads((path / "build/result.json").read_text())
    if result["status"] == "execution-interrupted":
        continue
    fixture = json.loads((path / "fixture.json").read_text())
    request = RepositoryFeatureRequest.model_validate_json(json.dumps(fixture["request"]))
    policy = FeaturePolicy.model_validate_json(json.dumps(fixture["policy"]))
    planning = json.loads((path / "build/planning/result.json").read_text())
    row = dict(
        **scheduled, result=result, planning=planning, planner_responses=[], worker_responses=[]
    )
    store = ArtifactStore(path / "build/planning/artifacts")
    for observation in planning.get("observations", []):
        row["planner_responses"].append(
            prior.model_evidence(store, observation["model_evidence_digest"])
        )
    proposal = path / "build/planning/proposal.json"
    if proposal.exists():
        row["proposal"] = json.loads(proposal.read_text())
    with WorkLedger(path / "ledger.db") as ledger:
        with sqlite3.connect(path / "ledger.db") as db:
            ids = [r[0] for r in db.execute("select atom_id from atoms")]
        states = [ledger.status(a) for a in ids]
        row["atoms"] = states
        if any(state.get("acceptance_challenged") for state in states):
            row["acceptance_challenged"] = True
        for state in states:
            for attempt in state["attempts"]:
                for event in attempt["events"]:
                    if event["kind"] == "observation" and event["details"]["kind"] == "model":
                        evidence = prior.model_evidence(
                            ledger.artifacts, event["details"]["digest"]
                        )
                        evidence.update(atom=state["atom_id"], attempt=attempt["ordinal"])
                        row["worker_responses"].append(evidence)
        if result["status"] == "accepted":
            feature = result["feature_result"]
            original = SnapshotSource(ledger.artifacts, request.source)
            final = SnapshotSource(ledger.artifacts, feature["source"])
            assert set(original.files) <= set(final.files)
            assert all(
                final.files[p] == original.files[p]
                for p in original.files
                if p not in request.allowed_paths
            )
            changed = {
                p: final.read_bytes(p).decode()
                for p in final.files
                if original.files.get(p) != final.files[p]
            }
            assert set(changed) == set(request.allowed_paths)
            row["preserved_original_files"] = len(set(original.files) - set(changed))
            state = ledger.status(feature["integration_atom"])
            broker = DockerBroker(ledger.artifacts, request.environments["python"].image)
            broker.qualify()
            audit = broker.execute(
                state["candidate_digest"],
                ("python", "-B", "-c", (HERE / "heldout.py").read_text()),
                seconds=30,
                purpose="validation",
            )
            row["heldout"] = audit.model_dump(mode="json")
            if state.get("acceptance_challenged"):
                row["acceptance_challenged"] = True
            elif audit.exit_code != 0:
                atom = WorkAtom.model_validate_json(json.dumps(state["contract"]))
                ledger.record_finding(
                    AcceptanceFinding(
                        atom_id=atom.atom_id,
                        contract_digest=atom.digest(),
                        candidate_digest=state["candidate_digest"],
                        evidence_digest=ledger.artifacts.publish(audit.canonical().encode()),
                        reason="Held-out state-sequence or completion-replacement audit failed",
                    )
                )
                row["acceptance_challenged"] = True
            else:
                row["changes"] = changed
                prefix = (
                    "repair-v3-"
                    if args.scoped_requirements
                    else "repair-v2-"
                    if args.fixed_symbols
                    else "repair-"
                    if args.repair
                    else ""
                )
                destination = HERE / "deliveries" / (prefix + path.name)
                delivered = {
                    p: final.read_bytes(p).decode()
                    for p in (
                        "taskdock.py",
                        "taskdock_cli.py",
                        "pyproject.toml",
                        "README.md",
                        "tests/test_taskdock.py",
                    )
                }
                for name, text in delivered.items():
                    target = destination / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        assert target.read_text() == text
                    else:
                        target.write_text(text)
        if row.get("acceptance_challenged"):
            before = [ledger.status(a) for a in ids]
            plan = FeaturePlan.model_validate_json((path / "build/feature-plan.json").read_bytes())
            try:
                run_feature(ledger, plan, lambda: request.source, model_factory=ReplayModel)
            except Conflict as error:
                row["replay_blocked"] = str(error)
            else:
                raise AssertionError("Challenged project reused")
            assert before == [ledger.status(a) for a in ids]
        else:
            before = [ledger.status(a) for a in ids]
            replay = build_feature(
                ledger,
                request,
                policy,
                path / "build",
                lambda: request.source,
                planner=no_model,
                model_factory=ReplayModel,
            )
            assert replay["status"] == result["status"]
            assert before == [ledger.status(a) for a in ids]
            row["replay_unchanged"] = True
    responses = row["planner_responses"] + row["worker_responses"]
    usage = [r["response"]["usage"] for r in responses if "response" in r]
    row["cost"] = dict(
        responses=len(usage),
        prompt_tokens=sum(u["prompt_tokens"] for u in usage),
        completion_tokens=sum(u["completion_tokens"] for u in usage),
        total_tokens=sum(u["total_tokens"] for u in usage),
        model_seconds=sum(r["evidence"].get("elapsed_seconds", 0) for r in responses),
    )
    raw_rows.append(row)
    (ROOT / "report.json").write_text(json.dumps(raw_rows, indent=2) + "\n")
    portable = {
        k: v
        for k, v in row.items()
        if k
        not in ("result", "planning", "atoms", "planner_responses", "worker_responses", "heldout")
    }
    portable["status"] = result["status"]
    portable["planning_status"] = planning.get("status")
    portable["questions"] = result.get("questions", [])
    portable["reason"] = result.get("reason")
    portable["evidence_digests"] = [r["evidence_digest"] for r in responses]
    portable["atoms"] = [
        dict(
            atom_id=a["atom_id"],
            status=a["status"],
            attempts=len(a["attempts"]),
            candidate_digest=a.get("candidate_digest"),
        )
        for a in states
    ]
    if "heldout" in row:
        portable["heldout"] = dict(
            exit_code=row["heldout"]["exit_code"],
            candidate_digest=row["heldout"]["candidate_digest"],
        )
    rows.append(portable)
    OUTPUT.write_text(json.dumps(rows, indent=2) + "\n")
    print(
        row["name"],
        result["status"],
        row["cost"],
        "audit",
        row.get("heldout", {}).get("exit_code"),
        flush=True,
    )
