"""Post-run held-out coverage checks; findings preserve historical acceptance."""
# Keep executed validator strings intact.
# ruff: noqa: E501

import argparse
import json
import sqlite3
from pathlib import Path

from gflo.broker import DockerBroker
from gflo.ledger import Conflict, WorkLedger
from gflo.progression import FeaturePlan, run_feature
from gflo.records import AcceptanceFinding

HERE = Path(__file__).parent


def command(paths, faults):
    code = """import json,subprocess,sys
from pathlib import Path
original=Path('large.py').read_text()
results=[]
for fault in FAULTS:
    old,new = (('value: int = 42','value: int = 0') if fault=='default'
               else ('if type(value) is not int:', 'if not isinstance(value, int):'))
    assert original.count(old)==1
    changed=original.replace(old,new)
    Path('large.py').write_text(changed)
    r=subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',*PATHS],capture_output=True,text=True)
    assert Path('large.py').read_text()==changed
    results.append(dict(fault=fault,exit_code=r.returncode,
        detected=r.returncode==1 and 'failed' in r.stdout and ('AssertionError' in r.stdout or 'Failed:' in r.stdout),
        stdout=r.stdout[-5000:],stderr=r.stderr[-2000:]))
Path('large.py').write_text(original)
print(json.dumps(results))
"""
    return (
        "python",
        "-B",
        "-c",
        code.replace("FAULTS", repr(faults)).replace("PATHS", repr(paths)),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError(
            "Audit output already exists; inspect retained findings instead of rerunning"
        )
    fixture = json.loads((HERE / "fixture.json").read_text())
    initial = json.loads((HERE / "results.json").read_text())
    reports = []
    for trial in initial["trials"]:
        if trial["status"] != "accepted":
            continue
        root = args.campaign / trial["name"]
        row = {"trial": trial["name"], "checks": [], "findings": []}
        with WorkLedger(root / "ledger.db") as ledger:
            broker = DockerBroker(ledger.artifacts, fixture["image"])
            broker.qualify()
            for state in trial["atoms"]:
                ids = state["contract"]["requirement_ids"]
                faults = []
                if "values" in ids:
                    faults.append("default")
                if "types" in ids:
                    faults.append("subclass")
                if not faults:
                    continue
                paths = [p for p in state["contract"]["writable_paths"] if p.startswith("tests/")]
                # Final integration has no write paths; inspect the full combined suite.
                integration = state["atom_id"].startswith("feature-final-")
                if integration:
                    paths = list(trial["tests"])
                if not paths:
                    continue
                execution = broker.execute(
                    state["candidate_digest"],
                    command(paths, faults),
                    seconds=30,
                    purpose="validation",
                )
                assert execution.exit_code == 0, execution
                evidence_digest = ledger.artifacts.publish(execution.canonical().encode())
                checks = json.loads(execution.stdout)
                row["checks"].append(
                    {
                        "atom": state["atom_id"],
                        "paths": paths,
                        "execution_digest": evidence_digest,
                        "results": checks,
                    }
                )
                missed = [r["fault"] for r in checks if not r["detected"]]
                if missed:
                    # A surviving mutant on accepted tests contradicts assigned coverage.
                    from gflo.records import WorkAtom

                    atom = WorkAtom.model_validate_json(json.dumps(state["contract"]))
                    finding = AcceptanceFinding(
                        atom_id=state["atom_id"],
                        contract_digest=atom.digest(),
                        candidate_digest=state["candidate_digest"],
                        evidence_digest=evidence_digest,
                        reason="Assigned test coverage omitted required behavior: surviving held-out "
                        + ", ".join(missed)
                        + " mutant. Original receipts remain historical evidence.",
                    )
                    ledger.record_finding(finding)
                    row["findings"].append(finding.model_dump(mode="json"))
            plan = FeaturePlan.model_validate_json((root / "plan.json").read_bytes())
            with sqlite3.connect(root / "ledger.db") as connection:
                count = connection.execute("select count(*) from events").fetchone()[0]
            try:
                replay = run_feature(ledger, plan, lambda: plan.request.source)
                row["replay"] = replay.status
                assert not row["findings"]
            except Conflict as error:
                assert row["findings"]
                row["replay"] = "blocked"
                row["replay_reason"] = str(error)
            with sqlite3.connect(root / "ledger.db") as connection:
                assert count == connection.execute("select count(*) from events").fetchone()[0]
            row["replay_added_events"] = 0
        reports.append(row)
        args.output.write_text(json.dumps(reports, indent=2) + "\n")
        print(trial["name"], len(row["findings"]), "findings", row["replay"], flush=True)


if __name__ == "__main__":
    main()
