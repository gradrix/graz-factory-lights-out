"""Verify the actual broker and child SQLite linkage after environment sanitization."""

import json
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.ledger import WorkLedger

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/importflow-linkage-v1")
ROOT.mkdir(parents=True, exist_ok=False)
rows = []
command = (
    "python",
    "-B",
    "-c",
    "import json,sqlite3,subprocess,sys,os; child=subprocess.check_output([sys.executable,'-c','import sqlite3; print(sqlite3.sqlite_version)'],text=True).strip(); print(json.dumps({'parent':sqlite3.sqlite_version,'child':child,'ld_library_path':os.environ.get('LD_LIBRARY_PATH')}))",  # noqa: E501
)
for directory, expected in [
    ("provision", "3.46.1"),
    ("provision-sqlite", "3.46.1"),
    ("provision-sqlite-system", "3.51.3"),
]:
    image = (HERE / directory / "image-id.txt").read_text().strip()
    with WorkLedger(ROOT / (directory + ".db")) as ledger:
        broker = DockerBroker(ledger.artifacts, image)
        broker.qualify()
        digest = ledger.artifacts.publish(
            SourceBundle(files={"placeholder.txt": "probe"}).canonical().encode()
        )
        result = broker.execute(digest, command, purpose="validation")
        assert result.exit_code == 0, result
        data = json.loads(result.stdout)
        assert data == dict(parent=expected, child=expected, ld_library_path=None), data
        rows.append(
            dict(
                image=image,
                recipe=directory,
                observed=data,
                evidence_digest=ledger.artifacts.publish(result.canonical().encode()),
            )
        )
        print(directory, data, flush=True)
        (HERE / "sqlite-linkage.json").write_text(json.dumps(rows, indent=2) + "\n")
