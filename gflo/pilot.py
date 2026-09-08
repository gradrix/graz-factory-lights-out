"""Development pilot v1: frozen small fixtures, separate from held-out evaluation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gflo.broker import SourceBundle
from gflo.controller import RunPlan
from gflo.gates import ProcessCase, ProcessGate
from gflo.model import ModelProfile
from gflo.records import WorkAtom
from gflo.worker import InputSnapshot

IMAGE = "python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca"
PRELUDE = "import json, sys\nx = json.load(sys.stdin)\n"
OUTPUT = "\nprint(json.dumps(result, sort_keys=True))\n"


@dataclass(frozen=True)
class Fixture:
    name: str
    category: str
    objective: str
    source: dict[str, str]
    reference: dict[str, str]
    cases: tuple[tuple[Any, Any], ...]
    writable: str = "main.py"
    prohibited: tuple[str, ...] = ()
    selected: tuple[str, ...] | None = None
    command: tuple[str, ...] = ("python", "main.py")


# The model writes only JSON test data. The immutable driver never executes
# candidate code and verifies every expected value against the reference before
# checking whether the test data distinguishes each independently seeded mutant.
MUTATION_DRIVER = (
    "import json, sys\nfrom pathlib import Path\nkind, variant"
    " = json.load(sys.stdin)\ncases = json.loads(Path('cases."
    "json').read_text())\ndef reference(x):\n    if kind == 'a"
    "ge': return 18 <= x <= 65\n    if kind == 'shipping': re"
    "turn 0 if x >= 5000 else 500\n    v = x.strip().lower()\n"
    "    return True if v == 'true' else False if v == 'fals"
    "e' else None\ndef mutant(x):\n    if kind == 'age':\n     "
    "   return [lambda:18 < x <= 65, lambda:18 <= x < 65, la"
    "mbda:True][variant-1]()\n    if kind == 'shipping':\n    "
    "    return [lambda:0 if x > 5000 else 500, lambda:500 i"
    "f x >= 5000 else 0,\n                lambda:0 if x >= 50"
    "00 else 400][variant-1]()\n    v = x.lower() if variant "
    "== 1 else x.strip() if variant == 2 else x.strip().lowe"
    "r()\n    return True if v == 'true' else False if v == '"
    "false' else False if variant == 3 else None\nvalid = isi"
    "nstance(cases, list) and 1 <= len(cases) <= 20\nif valid"
    ":\n    for case in cases:\n        if not isinstance(case"
    ", dict) or set(case) != {'input','expected'}:\n         "
    "   valid = False; break\n        x, expected = case['inp"
    "ut'], case['expected']\n        if (kind in ('age','ship"
    "ping') and type(x) is not int) or (kind == 'shipping' a"
    "nd x < 0) or (kind == 'boolean' and type(x) is not str)"
    ":\n            valid = False; break\n        answer = ref"
    "erence(x)\n        if type(answer) is not type(expected)"
    " or answer != expected:\n            valid = False; brea"
    "k\nif not valid: print('INVALID')\nelif variant == 0: pri"
    "nt('PASS')\nelse:\n    caught = any(type(mutant(c['input'"
    "])) is not type(c['expected']) or mutant(c['input']) !="
    " c['expected'] for c in cases)\n    print('DETECTED' if "
    "caught else 'MISS')\n"
)


def fixtures() -> tuple[Fixture, ...]:
    tasks = [
        Fixture(
            "01-slug",
            "implementation",
            (
                "Implement main.py: input is a JSON string. Lowercase it"
                ", replace each maximal run of characters outside ASCII "
                "a-z and 0-9 with one hyphen, and strip leading/trailing"
                " hyphens. Return the resulting JSON string."
            ),
            {"main.py": PRELUDE + "result = x" + OUTPUT},
            {
                "main.py": PRELUDE
                + "import re\nresult = re.sub('[^a-z0-9]+', '-', x.lower()).strip('-')"
                + OUTPUT
            },
            ((" Hello, WORLD!! ", "hello-world"), ("", ""), ("A___B  C", "a-b-c"), ("---", "")),
        ),
        Fixture(
            "02-counts",
            "implementation",
            (
                "Implement main.py: input is a JSON list of strings. Ret"
                "urn an object mapping each distinct case-sensitive stri"
                "ng to its frequency, including empty strings."
            ),
            {"main.py": PRELUDE + "result = {}" + OUTPUT},
            {
                "main.py": PRELUDE
                + "result = {}\nfor item in x: result[item] = result.get(item, 0) + 1"
                + OUTPUT
            },
            (
                (["a", "b", "a"], {"a": 2, "b": 1}),
                ([], {}),
                (["", "A", "a", ""], {"": 2, "A": 1, "a": 1}),
            ),
        ),
        Fixture(
            "03-chunks",
            "implementation",
            (
                "Implement main.py: input has items (a JSON list) and si"
                "ze (an integer). Split items into consecutive chunks of"
                " at most size, preserving order and the final short chu"
                'nk. Empty items gives []. For size <= 0 return {"error"'
                ':"size"}.'
            ),
            {"main.py": PRELUDE + "result = [x['items']]" + OUTPUT},
            {
                "main.py": PRELUDE
                + (
                    "n = x['size']\nresult = {'error':'size'} if n <= 0 else "
                    "[x['items'][i:i+n] for i in range(0,len(x['items']),n)]"
                )
                + OUTPUT
            },
            (
                ({"items": [1, 2, 3, 4, 5], "size": 2}, [[1, 2], [3, 4], [5]]),
                ({"items": [], "size": 3}, []),
                ({"items": [1], "size": 0}, {"error": "size"}),
                ({"items": [1, 2], "size": 9}, [[1, 2]]),
            ),
        ),
        Fixture(
            "04-mean",
            "repair",
            (
                "Repair main.py: input is a JSON list of integers. Retur"
                "n its arithmetic mean as a JSON floating-point number, "
                "or null for an empty list. Negative values and fraction"
                "al means must work."
            ),
            {"main.py": PRELUDE + "result = sum(x) // len(x)" + OUTPUT},
            {"main.py": PRELUDE + "result = sum(x) / len(x) if x else None" + OUTPUT},
            (([1, 2], 1.5), ([], None), ([-4, 1], -1.5), ([2, 2], 2.0)),
        ),
        Fixture(
            "05-overlap",
            "repair",
            (
                "Repair main.py: input is two intervals [[a,b],[c,d]] wi"
                "th a<=b and c<=d. Return whether the half-open interval"
                "s [a,b) and [c,d) overlap. Touching endpoints and empty"
                " intervals do not overlap."
            ),
            {"main.py": PRELUDE + "result = max(x[0][0],x[1][0]) <= min(x[0][1],x[1][1])" + OUTPUT},
            {"main.py": PRELUDE + "result = max(x[0][0],x[1][0]) < min(x[0][1],x[1][1])" + OUTPUT},
            (
                ([[1, 3], [3, 5]], False),
                ([[1, 4], [2, 3]], True),
                ([[2, 2], [1, 4]], False),
                ([[-3, 1], [0, 2]], True),
            ),
        ),
        Fixture(
            "06-last-unique",
            "repair",
            (
                "Repair main.py: input is a JSON list of integers. Keep "
                "only each value's last occurrence, retaining the origin"
                "al order of those final occurrences. For [3,1,3,2,1], r"
                "eturn [3,2,1]. Handle empty arrays and negative values."
            ),
            {"main.py": PRELUDE + "result = sorted(set(x))" + OUTPUT},
            {
                "main.py": PRELUDE
                + (
                    "seen=set()\nresult=[]\nfor item in reversed(x):\n    if it"
                    "em not in seen: seen.add(item); result.append(item)\nres"
                    "ult.reverse()"
                )
                + OUTPUT
            },
            (
                ([3, 1, 3, 2, 1], [3, 2, 1]),
                ([], []),
                ([-1, 2, -1, 3, 2], [-1, 3, 2]),
                ([4, 4], [4]),
            ),
        ),
    ]
    provider = "def lookup(data, key):\n    return {'found': key in data, 'value': data.get(key)}\n"
    tasks.append(
        Fixture(
            "07-lookup-consumer",
            "migration",
            (
                "Read provider.py to learn the current lookup API. Migra"
                "te only main.py. Input is {data: object, key: string}; "
                "output {found: boolean, value: stored value or null}. S"
                "tored false, zero and null still count as found. Do not"
                " change provider.py."
            ),
            {
                "provider.py": provider,
                "main.py": PRELUDE
                + (
                    "from provider import lookup\nv=lookup(x['data'],x['key']"
                    ")\nresult={'found': bool(v), 'value':v}"
                )
                + OUTPUT,
            },
            {
                "provider.py": provider,
                "main.py": PRELUDE
                + "from provider import lookup\nresult=lookup(x['data'],x['key'])"
                + OUTPUT,
            },
            (
                ({"data": {"a": 0}, "key": "a"}, {"found": True, "value": 0}),
                ({"data": {}, "key": "a"}, {"found": False, "value": None}),
                ({"data": {"a": None}, "key": "a"}, {"found": True, "value": None}),
            ),
            selected=("main.py",),
        )
    )
    provider = (
        "def quote(unit_cents, quantity):\n    return {'subtotal_"
        "cents':unit_cents*quantity, 'currency':'EUR'}\n"
    )
    tasks.append(
        Fixture(
            "08-price-consumer",
            "migration",
            (
                "Read provider.py and migrate only main.py to its quote "
                "API. Input has unit_cents and quantity, both nonnegativ"
                "e integers. Output {total: a decimal string with exactl"
                "y two fractional digits, currency: the provider currenc"
                "y}. Use integer cents without rounding errors; do not c"
                "hange provider.py."
            ),
            {
                "provider.py": provider,
                "main.py": PRELUDE
                + (
                    "from provider import quote\nresult={'total':format(quote"
                    "(x['unit_cents'],x['quantity']),'.2f'),'currency':'USD'"
                    "}"
                )
                + OUTPUT,
            },
            {
                "provider.py": provider,
                "main.py": PRELUDE
                + (
                    "from provider import quote\nq=quote(x['unit_cents'],x['q"
                    "uantity']); n=q['subtotal_cents']\nresult={'total':f'{n/"
                    "/100}.{n%100:02d}','currency':q['currency']}"
                )
                + OUTPUT,
            },
            (
                ({"unit_cents": 1234, "quantity": 2}, {"total": "24.68", "currency": "EUR"}),
                ({"unit_cents": 1, "quantity": 3}, {"total": "0.03", "currency": "EUR"}),
                ({"unit_cents": 999, "quantity": 0}, {"total": "0.00", "currency": "EUR"}),
            ),
            selected=("main.py",),
        )
    )
    provider = (
        "def fetch_page(items, cursor=None):\n    start=0 if curs"
        "or is None else cursor\n    end=start+2\n    return items"
        "[start:end], (end if end<len(items) else None)\n"
    )
    tasks.append(
        Fixture(
            "09-page-consumer",
            "migration",
            (
                "Read provider.py and migrate only main.py to the new fe"
                "tch_page API. Input is a JSON list. Fetch all pages, fo"
                "llowing the provider cursor until it signals completion"
                "; output the flattened items in original order. Empty i"
                "nput must return []. Do not change provider.py."
            ),
            {
                "provider.py": provider,
                "main.py": PRELUDE
                + "from provider import fetch_page\nresult=fetch_page(x)"
                + OUTPUT,
            },
            {
                "provider.py": provider,
                "main.py": PRELUDE
                + (
                    "from provider import fetch_page\nresult=[]; cursor=None\n"
                    "while True:\n    page,cursor=fetch_page(x,cursor); resul"
                    "t.extend(page)\n    if cursor is None: break"
                )
                + OUTPUT,
            },
            (([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]), ([], []), (["a", "b"], ["a", "b"])),
            selected=("main.py",),
        )
    )
    requirements: list[tuple[str, str, list[tuple[Any, Any]]]] = [
        (
            "age",
            (
                "An eligibility function takes an integer age and return"
                "s true exactly for ages 18 through 65 inclusive, otherw"
                "ise false."
            ),
            [(17, False), (18, True), (65, True), (66, False)],
        ),
        (
            "shipping",
            (
                "A shipping function takes a nonnegative integer subtota"
                "l in cents. Shipping costs zero when subtotal is at lea"
                "st 5000, and 500 cents otherwise."
            ),
            [(0, 500), (4999, 500), (5000, 0), (5001, 0)],
        ),
        (
            "boolean",
            (
                "A parser takes a string, strips surrounding whitespace,"
                " and compares case-insensitively. It returns true for t"
                "rue, false for false, and null for any other text."
            ),
            [(" TRUE ", True), ("False", False), ("unknown", None), ("", None)],
        ),
    ]
    for index, (kind, requirement, examples) in enumerate(requirements, 10):
        tasks.append(
            Fixture(
                f"{index:02d}-tests-{kind}",
                "test-generation",
                requirement
                + (
                    " Write only cases.json as a JSON array of 1 to 20 objec"
                    "ts with exactly input and expected fields. Derive tests"
                    " from the requirement: include normal, boundary and rel"
                    "evant invalid cases. The controller will check every ex"
                    "pected value against a known-good implementation and re"
                    "quire the tests to detect independently seeded defects."
                    " Do not edit or request driver.py."
                ),
                {"cases.json": "[]", "driver.py": MUTATION_DRIVER},
                {
                    "cases.json": json.dumps([{"input": x, "expected": y} for x, y in examples]),
                    "driver.py": MUTATION_DRIVER,
                },
                tuple(
                    ([kind, variant], "PASS" if variant == 0 else "DETECTED")
                    for variant in range(4)
                ),
                writable="cases.json",
                prohibited=("driver.py",),
                command=("python", "-I", "driver.py"),
            )
        )
    return tuple(tasks)


def make_plan(fixture: Fixture, deployment: str, template: Path) -> RunPlan:
    config = json.loads(deployment)
    source = SourceBundle(files=fixture.source)
    is_tests = fixture.category == "test-generation"
    gate = ProcessGate(
        cases=tuple(
            ProcessCase(
                command=fixture.command,
                stdin=json.dumps(given) + "\n",
                expected_stdout=(expected if is_tests else json.dumps(expected, sort_keys=True))
                + "\n",
            )
            for given, expected in fixture.cases
        )
    )
    atom = json.loads(template.read_text())
    atom.update(
        atom_id="pilot-v1-" + fixture.name,
        idempotency_key="pilot-v1-" + fixture.name,
        objective=fixture.objective
        + (
            ""
            if is_tests
            else (
                " Read stdin using json.load(sys.stdin); "
                "print only json.dumps(result, sort_keys=True)."
            )
        ),
        source_revision="pilot-v1-" + fixture.name,
        writable_paths=[fixture.writable],
        prohibited_paths=list(fixture.prohibited),
        allowed_tools=["read", "edit"],
        max_attempts=3,
        required_gates=[{"gate_id": "behavior", "validator_digest": gate.digest()}],
        expected_outputs=[
            {
                "name": "candidate",
                "schema_digest": hashlib.sha256(
                    json.dumps(SourceBundle.model_json_schema(), sort_keys=True).encode()
                ).hexdigest(),
            }
        ],
    )
    atom["inputs_digest"] = InputSnapshot(
        source_digest=source.digest(), source_revision=atom["source_revision"]
    ).digest()
    profile = ModelProfile(
        base_url=config["base_url"],
        model=config["model"],
        deployment_digest=hashlib.sha256(deployment.encode()).hexdigest(),
    )
    return RunPlan(
        atom=WorkAtom.model_validate_json(json.dumps(atom)),
        source=source,
        gates={"behavior": gate},
        model_profile=profile,
        deployment=deployment,
        broker_image=IMAGE,
        selected_paths=fixture.selected,
        max_model_turns=3,
    )
