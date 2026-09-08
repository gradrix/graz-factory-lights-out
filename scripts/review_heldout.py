#!/usr/bin/env python3
"""Supplement scored gates with frozen semantic probes on retained accepted outputs.

Prepare probes before inspecting model outputs. Review does not repair or rescore
an accepted artifact. Any discrepancy stays a discovered false acceptance.
"""

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import DockerBroker
from gflo.heldout import fixtures
from gflo.pilot import IMAGE

EXTRA = {
    "interval-union": [[[5, 8], [1, 2], [2, 6], [10, 10]], [[-9, -5], [-6, 0], [1, 1]]],
    "stable-unique": [["x", "X", "x", "", "X", ""], ["a", "b", "c", "b", "a"]],
    "run-length": ["abbcccddddaa", "\n\n aa"],
    "rotate": [{"items": [0, 1, 2, 3, 4], "steps": -12}, {"items": [None, False], "steps": 101}],
    "balanced-brackets": ["{a[b(c)d]e}", "{[}]", "(]", "}{", "((((()))))"],
    "word-frequency": ["Hello! hello HELLO!\nhello", "\n\t"],
    "transpose": [[[1], [2], [3]], [[0, False, None]]],
    "chunks": [{"items": [0, False, None, "x"], "size": 3}],
    "flatten-lists": [[[False], [[None, {"a": []}]], ["", []]]],
    "group-records": [
        [{"group": "a", "value": []}, {"group": "a", "value": {}}, {"group": "b", "value": 0}]
    ],
    "median": [[-8, 5, 1, 7, 7, 0], [2, 2, 2, 2], [-1, 0, 1]],
    "binary-search": [{"items": [0, 0, 0], "target": 0}, {"items": [-3, 0, 2], "target": 5}],
    "leap-year": [1600, 1700, 2400, 1996, 1999],
    "ceil-division": [{"a": -7, "b": 3}, {"a": 7, "b": -3}, {"a": 6, "b": 3}],
    "dedupe-last": [
        [
            {"id": "b", "v": 1},
            {"id": "a", "v": 2},
            {"id": "b", "v": 3},
            {"id": "c", "v": 4},
            {"id": "a", "v": 5},
        ]
    ],
    "range-intersection": [{"a": [-3, -1], "b": [0, 5]}, {"a": [1, 5], "b": [1, 5]}],
    "version-sort": [["1.0.0", "1", "01.00", "1.0.1", "1.0", "0.99"]],
    "sliding-sums": [{"items": [1, -1, 1, -1], "width": 4}, {"items": [0, 0, 0], "width": 2}],
    "path-normalize": ["/a/b/../../../c//./d/..", "/./../", "/a/..hidden/./x"],
    "csv-row": ['"","a,b",c', '"quoted ""word""", x ', "a,,,b"],
    "keyword-api": [{"text": "line\n", "prefix": "  "}, {"text": "ü", "prefix": "界"}],
    "record-result": ["one\ttwo\nthree", "  ", "one-word"],
    "optional-lookup": ["", "unknown", "b"],
    "iterator-api": [[-4, 3, -2, 0, 3, 1], [0, 0]],
    "unit-api": [9, -1, 100],
    "instance-api": [{"start": 7, "deltas": [-7, -1, 2, 0]}],
    "async-api": [101, -99],
    "context-api": ["x\ny", "界ü"],
    "batch-api": [["x", "c", "b", "a", "c", "z"]],
    "paged-api": [[1, 2, 3, 4], list(range(9))],
}


def prepare(path):
    tasks = {t.name: t for t in fixtures()}
    probes = []
    for name, values in EXTRA.items():
        fixture = tasks[name]
        expected = []
        with tempfile.TemporaryDirectory() as directory:
            for filename, content in fixture.reference.items():
                target = Path(directory) / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            for value in values:
                result = subprocess.run(
                    fixture.command,
                    input=json.dumps(value) + "\n",
                    cwd=directory,
                    text=True,
                    capture_output=True,
                    check=True,
                    timeout=10,
                )
                expected.append(json.loads(result.stdout))
        probes.append(dict(task=name, inputs=values, expected=expected))
    manifest = dict(
        kind="supplemental-semantic-probes-v1",
        probes=probes,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope="Additional reference comparisons; test-generation uses mandatory known-good and three seeded-mutant gates, plus retained-case inspection.",
    )
    with path.open("x") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")


def review(directory, manifest_path, repetition=None):
    manifest = json.loads(manifest_path.read_text())
    probes = {p["task"]: p for p in manifest["probes"]}
    results = json.loads((directory / "results.json").read_text())
    source_store = ArtifactStore(directory / "ledger.db.artifacts")
    if repetition is not None:
        results = [r for r in results if r["task"].startswith(f"heldout-v1-r{repetition}-")]
    output = directory / (
        "semantic-review" if repetition is None else f"semantic-review-r{repetition}"
    )
    output.mkdir(exist_ok=False)
    store = ArtifactStore(output / "artifacts")
    broker = DockerBroker(store, IMAGE)
    broker.qualify()
    observations = []
    # Execute all extra inputs in one clean container per accepted candidate.
    command = (
        "python",
        "-c",
        "import io,json,runpy,sys,contextlib\n"
        "inputs=json.load(sys.stdin); outputs=[]\n"
        "for value in inputs:\n"
        "    sys.stdin=io.StringIO(json.dumps(value)); captured=io.StringIO()\n"
        '    with contextlib.redirect_stdout(captured): runpy.run_path("main.py",run_name="__main__")\n'
        "    outputs.append(json.loads(captured.getvalue()))\n"
        "print(json.dumps(outputs,sort_keys=True))",
    )
    for row in results:
        if row["status"] != "accepted":
            continue
        name = row["task"].split("-", 3)[-1]
        if name not in probes:
            continue
        probe = probes[name]
        digest = store.publish(source_store.read(row["state"]["candidate_digest"]))
        checked = broker.execute(
            digest,
            command,
            stdin=json.dumps(probe["inputs"]) + "\n",
            seconds=10,
            purpose="validation",
        )
        try:
            observed = json.loads(checked.stdout)
        except (ValueError, UnicodeError):
            observed = None
        passed = (
            checked.outcome == "completed"
            and checked.exit_code == 0
            and observed == probe["expected"]
        )
        observations.append(
            dict(
                task=row["task"],
                passed=passed,
                execution=checked.digest(),
                expected=probe["expected"],
                observed=observed,
            )
        )
        (output / "results.json").write_text(json.dumps(observations, indent=2) + "\n")
        print(json.dumps(dict(task=row["task"], passed=passed)), flush=True)
    (output / "summary.json").write_text(
        json.dumps(
            dict(
                reviewed=len(observations), discrepancies=sum(not r["passed"] for r in observations)
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--campaign", type=Path)
    parser.add_argument("--repetition", type=int, choices=(1, 2, 3))
    args = parser.parse_args()
    if args.campaign:
        review(args.campaign, args.manifest, args.repetition)
    else:
        prepare(args.manifest)
