#!/usr/bin/env python3
"""Review seen version-sort candidates against seeded input partitions in Docker."""

import argparse
import hashlib
import json
import random
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import DockerBroker, SourceBundle
from gflo.pilot import IMAGE


def cases():
    rng = random.Random(20260909)
    values = [
        "0",
        "0.0",
        "00.000",
        "1",
        "1.0",
        "01.00",
        "1.0.0",
        "1.0.1",
        "1.01",
        "2",
        "10",
        "9",
        "999999999999999999999",
        "1000000000000000000000",
        "2.0.0.0.0",
        "0.0.0.1",
    ]
    return [[], ["1.0.0", "1"], ["0.0", "0", "00.000"], values, values[::-1]] + [
        rng.choices(values, k=rng.randrange(1, 24)) for _ in range(64)
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    inputs = cases()

    def expected(items):
        width = max((len(x.split(".")) for x in items), default=0)
        return sorted(
            items, key=lambda x: tuple(map(int, x.split("."))) + (0,) * (width - len(x.split(".")))
        )

    expected_stdout = "".join(json.dumps(expected(x), sort_keys=True) + "\n" for x in inputs)
    driver = (
        "import json,subprocess,sys\nfor x in json.load(sys.stdin):\n"
        ' r=subprocess.run([sys.executable,"main.py"],input=json.dumps(x),'
        'text=True,capture_output=True,check=True,timeout=2)\n print(r.stdout,end="")\n'
    )
    plan = json.loads((args.campaign / "manifest.json").read_text())["plans"][0]["plan"]
    store = ArtifactStore(args.output / "artifacts")
    broker = DockerBroker(store, IMAGE)
    broker.qualify()
    bundles = [("retained-bad", SourceBundle.model_validate_json(json.dumps(plan["source"])))]
    # This control qualifies the review harness; it is never submitted as a worker repair.
    control = SourceBundle(
        files={
            "main.py": "import json,sys\nx=json.load(sys.stdin)\n"
            'n=max((len(s.split(".")) for s in x),default=0)\n'
            'print(json.dumps(sorted(x,key=lambda s:tuple(map(int,s.split(".")))'
            '+(0,)*(n-len(s.split(".")))),sort_keys=True))\n'
        }
    )
    bundles.append(("reference-control", control))
    for row in json.loads((args.campaign / "results.json").read_text()):
        if row["state"]["status"] == "accepted":
            digest = row["state"]["candidate_digest"]
            bundles.append(
                (
                    row["atom_id"],
                    SourceBundle.model_validate_json(
                        (args.campaign / "ledger.db.artifacts" / digest).read_bytes()
                    ),
                )
            )
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "scope": "Supplemental checks on seen-task repairs, not held-out scoring",
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "inputs": inputs,
                "expected_stdout": expected_stdout,
                "command": ["python", "-c", driver],
                "candidates": {name: b.digest() for name, b in bundles},
            },
            indent=2,
        )
        + "\n"
    )
    rows = []
    for name, bundle in bundles:
        digest = store.publish(bundle.canonical().encode())
        e = broker.execute(
            digest,
            ("python", "-c", driver),
            stdin=json.dumps(inputs),
            seconds=60,
            purpose="validation",
        )
        rows.append(
            {
                "candidate": name,
                "passed": e.outcome == "completed"
                and e.exit_code == 0
                and e.stdout == expected_stdout.encode(),
                "execution_digest": e.digest(),
                "source_digest": digest,
            }
        )
    (args.output / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps(rows), flush=True)
    if rows[0]["passed"] or not all(r["passed"] for r in rows[1:]):
        raise RuntimeError("Review failed; inspect retained executions before reuse")


if __name__ == "__main__":
    main()
