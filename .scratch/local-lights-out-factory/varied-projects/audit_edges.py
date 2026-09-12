"""Bind newly discovered requirement failures to exact accepted candidates."""

import json
import sqlite3
from pathlib import Path

from gflo.broker import DockerBroker
from gflo.ledger import WorkLedger
from gflo.records import AcceptanceFinding, WorkAtom

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/varied-projects-v1")
rows = (
    json.loads((HERE / "edge-audit.json").read_text())
    if (HERE / "edge-audit.json").exists()
    else []
)
for path in sorted(ROOT.glob("*-*")):
    if not path.is_dir():
        continue
    script = "postreview_csv.py" if path.name.startswith("csvfold-") else "postreview_dag.py"
    command = ("python", "-B", "-c", (HERE / script).read_text())
    result_path = path / "build/result.json"
    if not result_path.exists() or json.loads(result_path.read_text())["status"] not in (
        "accepted",
        "task-halt",
        "integration-halt",
    ):
        continue
    fixture = json.loads((path / "fixture.json").read_text())
    with sqlite3.connect(path / "ledger.db") as db:
        ids = [row[0] for row in db.execute("select atom_id from atoms")]
    with WorkLedger(path / "ledger.db") as ledger:
        broker = DockerBroker(
            ledger.artifacts, fixture["request"]["environments"]["python"]["image"]
        )
        broker.qualify()
        for atom_id in ids:
            state = ledger.status(atom_id)
            if (
                state["status"] != "accepted"
                or "core.py" not in state["contract"]["writable_paths"]
            ):
                continue
            if any(
                row.get("kind") == path.name
                and row.get("candidate_digest") == state["candidate_digest"]
                for row in rows
            ):
                continue
            result = broker.execute(state["candidate_digest"], command, purpose="validation")
            evidence = ledger.artifacts.publish(result.canonical().encode())
            row = dict(
                kind=path.name,
                atom_id=atom_id,
                candidate_digest=state["candidate_digest"],
                evidence_digest=evidence,
                exit_code=result.exit_code,
            )
            if result.exit_code != 0:
                atom = WorkAtom.model_validate_json(json.dumps(state["contract"]))
                finding = AcceptanceFinding(
                    atom_id=atom_id,
                    contract_digest=atom.digest(),
                    candidate_digest=state["candidate_digest"],
                    evidence_digest=evidence,
                    reason=(
                        "Post-review explicit input validation failed: CSV quotes, "
                        "DAG name termination or invalid UTF-8 CLI handling"
                    ),
                )
                ledger.record_finding(finding)
                row["finding_digest"] = finding.digest()
            rows.append(row)
            (HERE / "edge-audit.json").write_text(json.dumps(rows, indent=2) + "\n")
            print(path.name, atom_id.split("/")[-1], result.exit_code, flush=True)
    source = HERE / "deliveries" / path.name
    if source.exists() and any(r.get("kind") == path.name and r["exit_code"] != 0 for r in rows):
        destination = HERE / "challenged" / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
