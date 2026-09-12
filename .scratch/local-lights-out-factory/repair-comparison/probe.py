"""Retained parser regression, always executed inside the admitted broker."""

import base64
import json
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.ledger import WorkLedger

HERE = Path(__file__).resolve().parent
IMPORT = HERE.parent / "importflow"
IMAGE = (IMPORT / "provision-sqlite-system/image-id.txt").read_text().strip()
CHECK = (IMPORT / "checks/tabular.py").read_text()
SOURCE = json.loads((IMPORT / "resume-source.json").read_text())["files"]["tabular.py"]


def check(ledger, code):
    bundle = SourceBundle(files={"tabular.py": code})
    digest = ledger.artifacts.publish(bundle.canonical().encode())
    broker = DockerBroker(ledger.artifacts, IMAGE)
    broker.qualify()
    result = broker.execute(digest, ("python", "-B", "-c", CHECK), seconds=60, purpose="validation")
    evidence = ledger.artifacts.publish(result.canonical().encode())
    return dict(
        passed=result.exit_code == 0 and result.stdout.decode() == "tabular-ok\n",
        candidate_digest=digest,
        evidence_digest=evidence,
        stderr=base64.b64decode(result.stderr_base64).decode(),
        stdout=result.stdout.decode(),
    )


if __name__ == "__main__":
    Path(".gflo/evidence/repair-comparison-probe").mkdir(parents=True, exist_ok=True)
    with WorkLedger(Path(".gflo/evidence/repair-comparison-probe/ledger.db")) as ledger:
        result = check(ledger, SOURCE)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["passed"] else 1)
