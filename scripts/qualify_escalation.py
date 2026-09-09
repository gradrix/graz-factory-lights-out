#!/usr/bin/env python3
"""Freeze, preflight, run and independently review eight prepared escalation tasks."""

import argparse
import dataclasses
import hashlib
import json
import random
import subprocess
import time
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import DockerBroker, SourceBundle
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.ledger import WorkLedger
from gflo.model import LocalModel
from gflo.pilot import IMAGE, OUTPUT, PRELUDE, Fixture, make_plan
from gflo.records import AcceptanceFinding
from gflo.reporting import cost_report

ROOT = Path(__file__).resolve().parents[1]


def tasks():
    rows = []
    rng = random.Random(20260910)

    def add(name, category, objective, reference, bad, oracle, inputs, review, api=None):
        source = {"main.py": PRELUDE + bad + OUTPUT}
        good = {"main.py": PRELUDE + reference + OUTPUT}
        if api is not None:
            source["api.py"] = good["api.py"] = api
            command = (
                "python",
                "-c",
                "import api,runpy; runpy.run_path('main.py',run_name='__main__'); assert api.calls>0",
            )
            objective += " Use the read-only api.py; do not reimplement its behavior."
        else:
            command = ("python", "main.py")
        fixture = Fixture(
            name,
            category,
            objective,
            source,
            good,
            tuple((x, oracle(x)) for x in inputs),
            prohibited=("api.py",) if api else (),
            command=command,
        )
        rows.append({"fixture": fixture, "review": [(x, oracle(x)) for x in review]})

    words = ["A", "a", "Straße", "STRASSE", "ß", "ss", "", " K ", "k"]
    add(
        "casefold-counts",
        "implementation",
        "Input is a list of strings. Count occurrences after Unicode casefold(), preserving whitespace. Output an object from casefolded string to integer count.",
        "result={}\nfor s in x:\n k=s.casefold(); result[k]=result.get(k,0)+1",
        "result={s:x.count(s) for s in x}",
        lambda x: {s.casefold(): sum(t.casefold() == s.casefold() for t in x) for s in x},
        [[], ["A", "a", "B"], ["Straße", "STRASSE", "ß", "ss"], ["", " ", ""]],
        [rng.choices(words, k=rng.randrange(20)) for _ in range(20)],
    )

    def grouped(xs):
        result = []
        for v in xs:
            if result and result[-1][-1] == v:
                result[-1].append(v)
            else:
                result.append([v])
        return result

    add(
        "consecutive-groups",
        "implementation",
        "Input is a list of integers. Return a list of maximal consecutive equal-value groups, preserving every value and original order. Empty input gives [].",
        "result=[]\nfor v in x:\n if result and result[-1][-1]==v: result[-1].append(v)\n else: result.append([v])",
        "result=[[v] for v in x]",
        grouped,
        [[], [1, 1, 2, 1], [0, 0, -1, -1, -1], [7]],
        [rng.choices([-2, -1, 0, 1, 2], k=rng.randrange(25)) for _ in range(20)],
    )

    def rank(x):
        return sorted(x["items"], key=lambda r: -r["score"])[: x["k"]]

    rank_values = [
        {
            "items": [
                {"name": f"n{i}", "score": rng.randrange(-2, 3)} for i in range(rng.randrange(15))
            ],
            "k": rng.randrange(20),
        }
        for _ in range(20)
    ]
    add(
        "stable-top-k",
        "repair",
        "Input has items (objects with name:string and score:integer) and nonnegative integer k. Return at most k items by descending score. Equal scores preserve input order. Preserve complete objects.",
        "result=sorted(x['items'],key=lambda r:-r['score'])[:x['k']]",
        "result=sorted(x['items'],key=lambda r:(-r['score'],r['name']))[:x['k']]",
        rank,
        [
            {"items": [], "k": 3},
            {
                "items": [
                    {"name": "z", "score": 2},
                    {"name": "a", "score": 2},
                    {"name": "b", "score": 3},
                ],
                "k": 2,
            },
            {"items": [{"name": "a", "score": -1}], "k": 0},
            {"items": [{"name": "a", "score": 1}], "k": 5},
        ],
        rank_values,
    )

    def multiple(x):
        return -(-x["n"] // x["step"]) * x["step"]

    add(
        "ceiling-multiple",
        "repair",
        "Input has integer n and positive integer step. Return the smallest integer multiple of step greater than or equal to n. Handle negative n, zero and arbitrarily large integers exactly.",
        "result=-(-x['n']//x['step'])*x['step']",
        "result=int(x['n']/x['step'])*x['step']",
        multiple,
        [
            {"n": 7, "step": 3},
            {"n": -7, "step": 3},
            {"n": 0, "step": 2},
            {"n": 10**25 + 1, "step": 10},
        ],
        [{"n": rng.randrange(-(10**26), 10**26), "step": rng.randrange(1, 100)} for _ in range(20)],
    )

    api = "calls=0\ndef lookup(data,*,key):\n global calls\n calls+=1\n return (key in data,data.get(key))\n"
    lookup = lambda x: {"found": x["key"] in x["data"], "value": x["data"].get(x["key"])}
    add(
        "keyword-lookup-pair",
        "migration",
        "Migrate main.py to lookup(data, *, key) returning (found,value). Input is {data:object,key:string}; output {found:boolean,value:stored value or null}. Stored false, 0, empty string and null count as found.",
        "from api import lookup\nfound,value=lookup(x['data'],key=x['key'])\nresult={'found':found,'value':value}",
        "from api import lookup\nv=lookup(x['data'],x['key'])\nresult={'found':bool(v),'value':v}",
        lookup,
        [
            {"data": {"a": 0}, "key": "a"},
            {"data": {}, "key": "a"},
            {"data": {"a": False}, "key": "a"},
            {"data": {"a": None}, "key": "a"},
        ],
        [
            {"data": {"a": v}, "key": key}
            for v in [0, False, None, "", [], {}, "value", -1]
            for key in ["a", "missing"]
        ],
        api,
    )

    api = "calls=0\ndef pages(items,*,size):\n global calls\n calls+=1\n for i in range(0,len(items),size):\n  yield {'values':items[i:i+size]}\n"
    add(
        "generator-pages",
        "migration",
        "Migrate main.py to pages(items, *, size), yielding objects with values lists. Input is {items:JSON list,size:positive integer}; output the concatenation of page values in order. Call the provider even on empty input.",
        "from api import pages\nresult=[v for p in pages(x['items'],size=x['size']) for v in p['values']]",
        "from api import pages\nresult=pages(x['items'],x['size'])",
        lambda x: x["items"],
        [
            {"items": [], "size": 2},
            {"items": [1, 2, 3, 4, 5], "size": 2},
            {"items": [False, None, 0], "size": 1},
            {"items": ["a"], "size": 9},
        ],
        [
            {
                "items": rng.choices([0, False, None, "a", [], {}], k=rng.randrange(20)),
                "size": rng.randrange(1, 8),
            }
            for _ in range(20)
        ],
        api,
    )

    for name, requirement, domain, expression, mutants, values in [
        (
            "divisible-three",
            "For an integer, return true exactly when divisible by 3, including zero and negative integers.",
            "type(x) is int",
            "x%3==0",
            ["x>0 and x%3==0", "x%3!=0", "True"],
            [-3, 0, 2, 3],
        ),
        (
            "ascii-prefix",
            'For a string, return true exactly when it begins with case-sensitive ASCII prefix "ab". Preserve whitespace and case.',
            "type(x) is str",
            "x.startswith('ab')",
            ["'ab' in x", "x.lower().startswith('ab')", "x.strip().startswith('ab')"],
            ["ab", "zab", "AB", " ab", ""],
        ),
    ]:
        driver = (
            "import json,sys\nfrom pathlib import Path\ncases=json.loads(Path('cases.json').read_text()); variant=json.load(sys.stdin)\n"
            f"def domain(x): return {domain}\ndef reference(x): return {expression}\n"
            "def mutant(x): return ["
            + ",".join("lambda:" + m for m in mutants)
            + "][variant-1]()\n"
            "valid=isinstance(cases,list) and 1<=len(cases)<=20\n"
            "try:\n valid=valid and all(isinstance(c,dict) and set(c)=={'input','expected'} and domain(c['input']) and type(reference(c['input'])) is type(c['expected']) and reference(c['input'])==c['expected'] for c in cases)\n"
            "except Exception: valid=False\n"
            "if not valid: print('INVALID')\nelif variant==0: print('PASS')\n"
            "else: print('DETECTED' if any(mutant(c['input'])!=c['expected'] for c in cases) else 'MISS')\n"
        )
        examples = [{"input": v, "expected": eval(expression, {"x": v})} for v in values]
        fixture = Fixture(
            "tests-" + name,
            "test-generation",
            "Write cases.json as a JSON list of 1–20 objects with exactly input and expected. "
            + requirement
            + " Include boundaries and distinguish plausible wrong implementations.",
            {"cases.json": "[]\n", "driver.py": driver},
            {"cases.json": json.dumps(examples) + "\n", "driver.py": driver},
            tuple((i, "PASS" if i == 0 else "DETECTED") for i in range(4)),
            writable="cases.json",
            prohibited=("driver.py",),
            command=("python", "-I", "driver.py"),
        )
        rows.append({"fixture": fixture, "review": [], "test_kind": name})
    return rows


def check(broker, bundle, cases, command):
    digest = broker.artifacts.publish(bundle.canonical().encode())
    observations = []
    for given, expected in cases:
        e = broker.execute(
            digest, command, stdin=json.dumps(given) + "\n", seconds=10, purpose="validation"
        )
        passed = (
            e.outcome == "completed" and e.exit_code == 0 and e.stdout == (expected + "\n").encode()
        )
        observations.append({"passed": passed, "execution_digest": e.digest()})
        if not passed:
            break
    return {"passed": all(o["passed"] for o in observations), "observations": observations}


def review_candidate(ledger, broker, task, bundle):
    fixture = task["fixture"]
    if fixture.category == "test-generation":
        values = json.loads(bundle.files["cases.json"])
        if task["test_kind"] == "divisible-three":
            oracle = lambda x: type(x) is int and divmod(x, 3)[1] == 0
            domain = lambda x: type(x) is int
        else:
            oracle = lambda x: x[:2] == "ab"
            domain = lambda x: type(x) is str
        passed = (
            isinstance(values, list)
            and 1 <= len(values) <= 20
            and all(
                isinstance(v, dict)
                and set(v) == {"input", "expected"}
                and domain(v["input"])
                and type(v["expected"]) is bool
                and oracle(v["input"]) == v["expected"]
                for v in values
            )
        )
        return {
            "passed": passed,
            "kind": "independent-domain-and-oracle-review",
            "case_count": len(values),
        }
    # One independent workflow runs additional inputs in subprocesses. Expected outputs stay host-side.
    driver = (
        "import json,subprocess,sys\nfor x in json.load(sys.stdin):\n r=subprocess.run("
        + repr(list(fixture.command))
        + ",input=json.dumps(x),text=True,capture_output=True,check=True,timeout=2)\n print(r.stdout,end='')\n"
    )
    digest = ledger.artifacts.publish(bundle.canonical().encode())
    e = broker.execute(
        digest,
        ("python", "-c", driver),
        stdin=json.dumps([x for x, y in task["review"]]),
        seconds=60,
        purpose="validation",
    )
    expected = "".join(json.dumps(y, sort_keys=True) + "\n" for x, y in task["review"])
    return {
        "passed": e.outcome == "completed" and e.exit_code == 0 and e.stdout == expected.encode(),
        "kind": "additional-input-review",
        "case_count": len(task["review"]),
        "execution_digest": e.digest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--profile",
        choices=("vllm-python-worker-escalating-v1", "vllm-python-worker-escalating-low-v1"),
        default="vllm-python-worker-escalating-v1",
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=args.resume)
    config_path = ROOT / "infra/serving/vllm-5090-graphs.example.json"
    deployment = config_path.read_text()
    config = json.loads(deployment)
    identity = json.loads(
        subprocess.check_output(
            ["docker", "inspect", config["managed"]["name"]], text=True, timeout=15
        )
    )[0]
    image = json.loads(
        subprocess.check_output(
            ["docker", "image", "inspect", config["managed"]["image"]], text=True, timeout=15
        )
    )[0]
    command = identity["Config"]["Cmd"]
    if not identity["State"]["Running"] or identity["Image"] != image["Id"]:
        raise RuntimeError("Pinned deployment not running")
    for flag in ["--revision", "--tokenizer-revision"]:
        if command[command.index(flag) + 1] != config["managed"]["revision"]:
            raise RuntimeError("Revision drift")
    samples = tasks()
    plans = []
    for repetition in range(1, 4):
        for task in samples:
            data = make_plan(
                task["fixture"], deployment, ROOT / "examples/work-atom.json"
            ).model_dump(mode="json")
            atom_id = f"escalation-v1-r{repetition}-{task['fixture'].name}"
            data["atom"].update(atom_id=atom_id, idempotency_key=atom_id, max_attempts=2)
            data["atom"]["context_budget"] = {"total_tokens": 8192, "output_tokens": 4096}
            data["max_model_turns"] = 1
            data["model_profile"]["profile_id"] = args.profile
            plans.append(RunPlan.model_validate_json(json.dumps(data)))
    sources = sorted((ROOT / "gflo").glob("*.py")) + [Path(__file__).resolve()]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    manifest = {
        "scope": "Eight newly authored tasks, three repetitions; bounded progression check, not large-system qualification",
        "policy": {
            "max_attempts": 2,
            "max_model_turns_per_attempt": 1,
            "first_output": 2048,
            "retry_output": 4096,
            "total_context": 8192,
            "minimum_verified": 22,
            "minimum_per_class": 5,
            "maximum_discovered_false_acceptances": 0,
        },
        "runtime": {"image_id": image["Id"], "command": command},
        "source_sha256": hashes,
        "tasks": [dict(t, fixture=dataclasses.asdict(t["fixture"])) for t in samples],
        "plans": [p.model_dump(mode="json") for p in plans],
    }
    manifest_path = args.output / "manifest.json"
    if args.resume:
        if json.loads(manifest_path.read_text()) != manifest:
            raise RuntimeError("Frozen campaign drift")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        for name in hashes:
            dest = args.output / "runtime-source" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((ROOT / name).read_bytes())
    if not (args.output / "preflight.json").exists():
        broker = DockerBroker(ArtifactStore(args.output / "preflight-artifacts"), IMAGE)
        broker.qualify()
        preflight = []
        for task in samples:
            f = task["fixture"]
            cases = [
                (x, y if f.category == "test-generation" else json.dumps(y, sort_keys=True))
                for x, y in f.cases
            ]
            good = check(broker, SourceBundle(files=f.reference), cases, f.command)
            bad = check(broker, SourceBundle(files=f.source), cases, f.command)
            preflight.append({"task": f.name, "reference": good, "starting_fault": bad})
            if not good["passed"] or bad["passed"]:
                raise RuntimeError("Preflight failed for " + f.name)
        (args.output / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n")
        print("Preflight: all eight references pass and starting faults fail", flush=True)
    results_path = args.output / "results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else []
    done = {r["atom_id"] for r in results if r["state"]["status"] in ("accepted", "quarantined")}
    with WorkLedger(args.output / "ledger.db", reserve_bytes=256 * 1024 * 1024) as ledger:
        broker = DockerBroker(ledger.artifacts, IMAGE)
        for index, plan in enumerate(plans):
            if plan.atom.atom_id in done:
                continue
            task = samples[index % len(samples)]
            prepare_run(ledger, plan)
            start = time.monotonic()
            state = Controller(
                ledger, LocalModel(ledger.artifacts, plan.model_profile), broker
            ).run(plan.atom.atom_id)
            review = None
            if state["status"] == "accepted":
                bundle = SourceBundle.model_validate_json(
                    ledger.artifacts.read(state["candidate_digest"])
                )
                review = review_candidate(ledger, broker, task, bundle)
                if not review["passed"]:
                    evidence = ledger.artifacts.publish(json.dumps(review, sort_keys=True).encode())
                    ledger.record_finding(
                        AcceptanceFinding(
                            atom_id=plan.atom.atom_id,
                            contract_digest=plan.atom.digest(),
                            candidate_digest=state["candidate_digest"],
                            evidence_digest=evidence,
                            reason="Prospective supplemental qualification review contradicted acceptance",
                        )
                    )
                    state = ledger.status(plan.atom.atom_id)
            row = {
                "atom_id": plan.atom.atom_id,
                "category": task["fixture"].category,
                "state": state,
                "review": review,
                "cost": cost_report(ledger, plan.atom.atom_id),
                "elapsed_seconds": time.monotonic() - start,
            }
            results = [r for r in results if r["atom_id"] != row["atom_id"]]
            results.append(row)
            results_path.write_text(json.dumps(results, indent=2) + "\n")
            print(
                json.dumps(
                    {
                        "atom": row["atom_id"],
                        "status": state["status"],
                        "attempts": len(state["attempts"]),
                        "review": None if review is None else review["passed"],
                    }
                ),
                flush=True,
            )
            if state["status"] not in ("accepted", "quarantined"):
                raise RuntimeError("Infrastructure halt: preserve evidence, then resume explicitly")
            failures = [r for r in results if not (r["review"] and r["review"]["passed"])]
            per_class_failures = {
                c: sum(r["category"] == c for r in failures)
                for c in ("implementation", "repair", "migration", "test-generation")
            }
            if len(failures) > 2 or max(per_class_failures.values(), default=0) > 1:
                print("Stopped: frozen numerical target is unreachable", flush=True)
                break
        audit = dataclasses.asdict(ledger.audit_artifacts())
    drift = any(
        hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
        for name, digest in hashes.items()
    )
    verified = [r for r in results if r["review"] and r["review"]["passed"]]
    false = [r["atom_id"] for r in results if r["review"] and not r["review"]["passed"]]
    counts = {
        c: sum(r["category"] == c for r in verified)
        for c in ["implementation", "repair", "migration", "test-generation"]
    }
    qualified = (
        len(results) == 24
        and len(verified) >= 22
        and min(counts.values()) >= 5
        and not false
        and not drift
        and not audit["missing"]
        and not audit["corrupt"]
    )
    summary = {
        "qualified": qualified,
        "runs": len(results),
        "unscored": len(plans) - len(results),
        "verified": len(verified),
        "per_class": counts,
        "false_acceptances": false,
        "source_drift": drift,
        "audit": audit,
        "attempts": sum(len(r["state"]["attempts"]) for r in results),
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
