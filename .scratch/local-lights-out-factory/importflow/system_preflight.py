"""Reference qualification with fixed SQLite proven inside actual worker execution."""

from pathlib import Path

import prepared_campaign as base

from gflo.gates import ProcessCase, ProcessGate

HERE = Path(__file__).resolve().parent
IMAGE = (HERE / "provision-sqlite-system/image-id.txt").read_text().strip()


def gates():
    checks = base.gates()
    case = ProcessCase(
        command=(
            "python",
            "-B",
            "-c",
            "import sqlite3,subprocess,sys; assert sqlite3.sqlite_version=='3.51.3'; assert subprocess.check_output([sys.executable,'-c','import sqlite3; print(sqlite3.sqlite_version)'],text=True).strip()=='3.51.3'; print('environment-ok')",
        ),
        expected_stdout="environment-ok\n",
        seconds=30,
    )
    checks["jobs"] = ProcessGate(cases=(case, *checks["jobs"].cases))
    return checks


if __name__ == "__main__":
    base.IMAGE = IMAGE
    base.preflight(
        root=Path(".gflo/evidence/importflow-system-preflight-v1"),
        summary=HERE / "system-preflight.json",
        checks=gates(),
    )
