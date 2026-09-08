"""Held-out atom campaign v1. Freeze before scoring; never tune against results.

Small standard-library Python tasks, not evidence about arbitrary large builds.
Reference programs and gate examples stay outside each worker view.
"""

from __future__ import annotations

import json
from typing import Any

from gflo.pilot import OUTPUT, PRELUDE, Fixture


def fixtures() -> tuple[Fixture, ...]:
    tasks = []
    specifications: list[tuple[str, str, str, str, list[Any]]] = [
        (
            "implementation",
            "interval-union",
            (
                "Merge overlapping or touching integer [start,end] intervals,"
                " sorted by start. Return an empty list for no intervals."
            ),
            (
                "result=[]\nfor a,b in sorted(x):\n    if result and a <= resul"
                "t[-1][1]: result[-1][1]=max(result[-1][1],b)\n    else: resul"
                "t.append([a,b])"
            ),
            [[], [[3, 5], [1, 3], [8, 9]], [[1, 9], [2, 3]], [[-4, -1], [0, 2]]],
        ),
        (
            "implementation",
            "stable-unique",
            "Return the first occurrence of each string in input order, case-sensitive.",
            "result=list(dict.fromkeys(x))",
            [[], ["b", "a", "b", "A", "a"], ["", ""], ["x"]],
        ),
        (
            "implementation",
            "run-length",
            (
                "Encode a string as a list of [character, consecutive count] "
                "pairs. Preserve case and whitespace."
            ),
            (
                "result=[]\nfor c in x:\n    if result and result[-1][0]==c: re"
                "sult[-1][1]+=1\n    else: result.append([c,1])"
            ),
            ["", "aaabbAa", "  x ", "abc"],
        ),
        (
            "implementation",
            "rotate",
            (
                "Input has items list and integer steps. Rotate items to the "
                "right by steps; negative steps rotate left; empty stays empt"
                "y."
            ),
            'a=x["items"]; k=x["steps"]%len(a) if a else 0\nresult=a[-k:]+a[:-k] if k else a',
            [
                {"items": [], "steps": 5},
                {"items": [1, 2, 3], "steps": 1},
                {"items": [1, 2, 3], "steps": -1},
                {"items": [1, 2], "steps": 4},
            ],
        ),
        (
            "implementation",
            "balanced-brackets",
            (
                "Return whether (), [], {} brackets are balanced and properly"
                " nested in a string. Ignore all other characters."
            ),
            (
                'stack=[]; valid=True\nfor c in x:\n    if c in "([{": stack.ap'
                'pend(c)\n    elif c in ")]}":\n        if not stack or stack.p'
                'op() != dict(zip(")]}","([{ ".strip()))[c]: valid=False; bre'
                "ak\nresult=valid and not stack"
            ),
            ["", "a([{}])b", "([)]", "]", "(abc", "hello"],
        ),
        (
            "implementation",
            "word-frequency",
            (
                "Split input on whitespace, lowercase words, count occurrence"
                "s; punctuation remains part of words. Return a JSON object."
            ),
            "result={}\nfor w in x.lower().split(): result[w]=result.get(w,0)+1",
            ["", "A a B", "hi, hi HI", " x\nX\ty "],
        ),
        (
            "implementation",
            "transpose",
            "Transpose a rectangular matrix. Empty matrix or rows of length zero produce [].",
            "result=[list(col) for col in zip(*x)]",
            [[], [[], []], [[1, 2, 3], [4, 5, 6]], [[7]]],
        ),
        (
            "implementation",
            "chunks",
            (
                "Input has items and positive size. Split items into consecut"
                "ive chunks of at most size; retain a short final chunk."
            ),
            'result=[x["items"][i:i+x["size"]] for i in range(0,len(x["items"]),x["size"])]',
            [
                {"items": [], "size": 3},
                {"items": [1, 2, 3, 4, 5], "size": 2},
                {"items": [1, 2], "size": 5},
                {"items": [1, 2], "size": 1},
            ],
        ),
        (
            "implementation",
            "flatten-lists",
            (
                "Recursively flatten nested JSON lists, preserving all non-li"
                "st values including null, false and objects."
            ),
            (
                "def flatten(v):\n    if isinstance(v,list): return [z for a i"
                "n v for z in flatten(a)]\n    return [v]\nresult=flatten(x)"
            ),
            [[], [1, [2, [], [3]], None, False], [{"a": 1}, ["x"]], [[[]]]],
        ),
        (
            "implementation",
            "group-records",
            (
                "Input is a list of objects with string group and arbitrary v"
                "alue. Return an object mapping group to values in input orde"
                "r."
            ),
            'result={}\nfor row in x: result.setdefault(row["group"],[]).append(row["value"])',
            [
                [],
                [
                    {"group": "b", "value": 1},
                    {"group": "a", "value": None},
                    {"group": "b", "value": 2},
                ],
                [{"group": "", "value": False}],
            ],
        ),
        (
            "repair",
            "median",
            (
                "Fix median: sort numeric input; odd uses middle, even uses m"
                "ean of two middle values; empty returns null."
            ),
            (
                "a=sorted(x); n=len(a)\nresult=None if not n else a[n//2] if n"
                "%2 else (a[n//2-1]+a[n//2])/2"
            ),
            [[], [3, 1, 2], [9, 1, 2, 4], [-5, -1], [7]],
        ),
        (
            "repair",
            "binary-search",
            (
                "Fix search: input has sorted items and target. Return the fi"
                "rst matching index, or -1 if absent."
            ),
            (
                'import bisect\na=x["items"]; i=bisect.bisect_left(a,x["target'
                '"])\nresult=i if i<len(a) and a[i]==x["target"] else -1'
            ),
            [
                {"items": [], "target": 1},
                {"items": [1, 2, 2, 2, 4], "target": 2},
                {"items": [1, 3], "target": 2},
                {"items": [1], "target": 1},
            ],
        ),
        (
            "repair",
            "leap-year",
            "Fix Gregorian leap year: divisible by 4, except centuries unless divisible by 400.",
            "result=x%4==0 and (x%100!=0 or x%400==0)",
            [1900, 2000, 2024, 2023, 2100],
        ),
        (
            "repair",
            "ceil-division",
            (
                "Fix mathematical ceiling division for integers a and nonzero"
                " b, including negative operands."
            ),
            'result=-(-x["a"]//x["b"])',
            [
                {"a": 5, "b": 2},
                {"a": -5, "b": 2},
                {"a": 5, "b": -2},
                {"a": -5, "b": -2},
                {"a": 0, "b": 3},
            ],
        ),
        (
            "repair",
            "dedupe-last",
            (
                "Fix record deduplication by id: keep the last record for eac"
                "h id and order survivors by their last occurrence in input."
            ),
            (
                'last={r["id"]:i for i,r in enumerate(x)}\nresult=[r for i,r i'
                'n enumerate(x) if last[r["id"]]==i]'
            ),
            [
                [],
                [{"id": "a", "v": 1}, {"id": "b", "v": 2}, {"id": "a", "v": 3}],
                [{"id": 0, "v": False}],
            ],
        ),
        (
            "repair",
            "range-intersection",
            (
                "Fix intersection of two half-open integer ranges a and b. Re"
                "turn [max starts,min ends] if nonempty, otherwise null."
            ),
            (
                'lo=max(x["a"][0],x["b"][0]); hi=min(x["a"][1],x["b"][1])\nres'
                "ult=[lo,hi] if lo<hi else None"
            ),
            [
                {"a": [1, 3], "b": [3, 5]},
                {"a": [1, 8], "b": [2, 4]},
                {"a": [-5, 0], "b": [-2, 3]},
                {"a": [1, 1], "b": [0, 2]},
            ],
        ),
        (
            "repair",
            "version-sort",
            (
                "Fix sorting dotted nonnegative integer version strings numer"
                "ically by components, zero-padding missing components; ties "
                "preserve input order."
            ),
            (
                'width=max((len(v.split(".")) for v in x),default=0)\nresult=s'
                'orted(x,key=lambda v:tuple(map(int,v.split(".")))+(0,)*(widt'
                'h-len(v.split("."))))'
            ),
            [[], ["1.10", "1.2", "1", "1.0", "0.9"], ["2.0.1", "2", "2.0.0", "10"]],
        ),
        (
            "repair",
            "sliding-sums",
            (
                "Fix moving sums: input has items and positive width; return "
                "sums of every full contiguous window. Width larger than list"
                " gives []."
            ),
            'a=x["items"]; k=x["width"]\nresult=[sum(a[i:i+k]) for i in range(len(a)-k+1)]',
            [
                {"items": [], "width": 1},
                {"items": [1, 2, 3, 4], "width": 2},
                {"items": [-2, 3], "width": 1},
                {"items": [1], "width": 2},
            ],
        ),
        (
            "repair",
            "path-normalize",
            (
                "Normalize an absolute POSIX path lexically: collapse slashes"
                " and dot, resolve dot-dot without going above root. No files"
                "ystem access."
            ),
            (
                'parts=[]\nfor p in x.split("/"):\n    if p=="..":\n        if p'
                'arts: parts.pop()\n    elif p not in ("", "."): parts.append('
                'p)\nresult="/"+"/".join(parts)'
            ),
            ["/", "/a//b/../c/.", "/../../x", "/a/.../b/"],
        ),
        (
            "repair",
            "csv-row",
            (
                "Fix CSV parsing: parse one CSV record using standard comma d"
                "elimiter and double quote escaping; return list of fields; e"
                "mpty input gives []."
            ),
            "import csv\nresult=next(csv.reader([x]))",
            ["", "a,b,", '"a,b","c""d"', ",,"],
        ),
    ]
    bugs = {
        "median": "result=sorted(x)[len(x)//2] if x else 0",
        "binary-search": 'result=x["items"].index(x["target"]) if x["target"] in x["items"] else 0',
        "leap-year": "result=x%4==0",
        "ceil-division": 'result=x["a"]//x["b"]',
        "dedupe-last": 'result=list({r["id"]:r for r in x}.values())',
        "range-intersection": 'result=[max(x["a"][0],x["b"][0]),min(x["a"][1],x["b"][1])]',
        "version-sort": "result=sorted(x)",
        "sliding-sums": 'result=[sum(x["items"][i:i+x["width"]]) for i in range(len(x["items"]))]',
        "path-normalize": 'result=x.replace("//","/")',
        "csv-row": 'result=x.split(",")',
    }
    for category, name, objective, body, inputs in specifications:
        cases = []
        for value in inputs:
            env = {"x": value}
            exec(body, env)
            cases.append((value, env["result"]))
        initial = bugs.get(name, "result=x" if category == "migration" else "result=None")
        tasks.append(
            Fixture(
                name,
                category,
                objective,
                {"main.py": PRELUDE + initial + OUTPUT},
                {"main.py": PRELUDE + body + OUTPUT},
                tuple(cases),
            )
        )
    migration_specs: list[tuple[str, str, str, str, list[Any]]] = [
        (
            "keyword-api",
            "The provider now requires keyword-only text and prefix. "
            "Preserve prefix + text output.",
            "def render(*, text, prefix):\n    used(); return prefix+text\n",
            'result=api.render(text=x["text"],prefix=x["prefix"])',
            [
                {"text": "A", "prefix": ">"},
                {"text": "", "prefix": ""},
                {"text": " x ", "prefix": "!"},
            ],
        ),
        (
            "record-result",
            (
                "api.measure now returns a record with chars and words. Prese"
                "rve output as the integer word count."
            ),
            "def measure(text):\n    used(); "
            "return {'chars':len(text),'words':len(text.split())}\n",
            'result=api.measure(x)["words"]',
            ["", "one two", " x\ny  z "],
        ),
        (
            "optional-lookup",
            (
                "api.lookup now returns None for missing keys, otherwise a re"
                "cord with value. Preserve output: value when present, string"
                " missing otherwise; false and zero are present values."
            ),
            (
                "def lookup(key):\n    used(); return {'value':{'a':0,'b':Fals"
                "e,'c':'ok'}[key]} if key in ('a','b','c') else None\n"
            ),
            'row=api.lookup(x)\nresult="missing" if row is None else row["value"]',
            ["a", "b", "c", "z"],
        ),
        (
            "iterator-api",
            (
                "api.positives now yields an iterator. Preserve output as a J"
                "SON list of strictly positive input integers."
            ),
            "def positives(items):\n    used(); return (v for v in items if v>0)\n",
            "result=list(api.positives(x))",
            [[], [-1, 0, 2, 3], [5]],
        ),
        (
            "unit-api",
            (
                "api.duration now returns milliseconds. Preserve public outpu"
                "t in seconds, including fractional and negative values."
            ),
            "def duration(ticks):\n    used(); return ticks*250\n",
            "result=api.duration(x)/1000",
            [0, 1, 6, -3],
        ),
        (
            "instance-api",
            (
                "The provider now exposes Counter(start), then .add(delta) re"
                "turning the updated total. Migrate old module calls; output "
                "totals after each delta."
            ),
            (
                "class Counter:\n    def __init__(self,start): used(); self.va"
                "lue=start\n    def add(self,delta): self.value+=delta; return"
                " self.value\n"
            ),
            'counter=api.Counter(x["start"])\nresult=[counter.add(d) for d in x["deltas"]]',
            [
                {"start": 0, "deltas": []},
                {"start": 5, "deltas": [1, -3, 0]},
                {"start": -2, "deltas": [4]},
            ],
        ),
        (
            "async-api",
            (
                "api.double is now async. Preserve the integer result of doub"
                "ling input; correctly await completion."
            ),
            "async def double(value):\n    used(); return value*2\n",
            "import asyncio\nresult=asyncio.run(api.double(x))",
            [0, 3, -4],
        ),
        (
            "context-api",
            (
                "api.session now returns a context manager yielding a reader "
                "with .read(). Read inside the context and output the reverse"
                "d input text."
            ),
            (
                "from contextlib import contextmanager\n@contextmanager\ndef se"
                "ssion(text):\n    used()\n    class Reader:\n        active=Tru"
                "e\n        def read(self):\n            if not self.active: ra"
                "ise RuntimeError('closed')\n            return text[::-1]\n   "
                " r=Reader()\n    try: yield r\n    finally: r.active=False\n"
            ),
            "with api.session(x) as reader: result=reader.read()",
            ["", "Ab ", "xyz"],
        ),
        (
            "batch-api",
            (
                "api.lookup_many replaces per-key lookup. It returns a mappin"
                "g for present keys only. Output values in requested key orde"
                "r with null for missing keys, preserving duplicates."
            ),
            (
                "def lookup_many(keys):\n    used(); data={'a':1,'b':0,'c':Fal"
                "se}; return {k:data[k] for k in keys if k in data}\n"
            ),
            "rows=api.lookup_many(x)\nresult=[rows.get(k) for k in x]",
            [[], ["b", "x", "a", "b"], ["c"]],
        ),
        (
            "paged-api",
            (
                "api.page(items, cursor=None) now returns records and next cu"
                "rsor in pages of two. Fetch every page and output all record"
                "s in order, without dropping the final short page."
            ),
            (
                "def page(items,cursor=None):\n    used(); i=0 if cursor is No"
                "ne else cursor; end=i+2\n    return {'records':items[i:end],'"
                "next':end if end<len(items) else None}\n"
            ),
            (
                "result=[]; cursor=None\nwhile True:\n    page=api.page(x,curso"
                'r=cursor); result.extend(page["records"]); cursor=page["next'
                '"]\n    if cursor is None: break'
            ),
            [[], [1], [1, 2, 3, 4, 5], [0, False, None]],
        ),
    ]
    from types import SimpleNamespace

    for name, objective, provider, body, inputs in migration_specs:
        provider = "calls=0\ndef used():\n    global calls\n    calls+=1\n" + provider
        provider_env: dict[str, Any] = {}
        exec(provider, provider_env)
        cases = []
        for value in inputs:
            env = {"x": value, "api": SimpleNamespace(**provider_env)}
            exec(body, env)
            cases.append((value, env["result"]))
        source = {
            "main.py": PRELUDE + "import api\nresult=api.legacy(x)" + OUTPUT,
            "api.py": provider,
        }
        reference = source | {"main.py": PRELUDE + "import api\n" + body + OUTPUT}
        tasks.append(
            Fixture(
                name,
                "migration",
                objective + " Use the supplied read-only api.py; do not reimplement its behavior.",
                source,
                reference,
                tuple(cases),
                command=(
                    "python",
                    "-c",
                    (
                        "import api,runpy; runpy.run_path('main.py',run_name='__main_"
                        "_'); assert api.calls>0"
                    ),
                ),
            )
        )
    test_specs: list[tuple[str, str, str, list[str], list[Any]]] = [
        (
            "absolute",
            "Absolute value of an integer.",
            "abs(x)",
            ["x", "-x", "abs(x)+1"],
            [-3, 0, 2],
        ),
        (
            "even",
            "True exactly for even integers.",
            "x%2==0",
            ["x%2!=0", "x>0 and x%2==0", "True"],
            [-2, 0, 3],
        ),
        (
            "clamp",
            "Clamp an integer to the inclusive interval [0,10].",
            "max(0,min(10,x))",
            ["min(10,x)", "max(0,x)", "max(1,min(9,x))"],
            [-1, 0, 10, 11],
        ),
        (
            "suffix",
            "True if a string ends with lowercase .py, case-sensitive.",
            'x.endswith(".py")',
            ['".py" in x', 'x.lower().endswith(".py")', 'x.endswith("py")'],
            ["a.py", "a.pyx", "a.PY", "happy"],
        ),
        (
            "strip",
            "Remove leading and trailing whitespace from a string, preserving internal whitespace.",
            "x.strip()",
            ["x.lstrip()", "x.rstrip()", '"".join(x.split())'],
            [" a ", "a b", ""],
        ),
        (
            "nonempty",
            "True exactly when a JSON list has at least one item.",
            "len(x)>0",
            ["len(x)>1", "True", "all(x)"],
            [[], [0], [1, 2]],
        ),
        (
            "sum",
            "Sum a list of integers; empty sum is zero.",
            "sum(x)",
            ["sum(x)+1", "sum(v for v in x if v>0)", "sum(x[:-1])"],
            [[], [-2, 3], [4]],
        ),
        (
            "reverse",
            "Reverse a string, preserving case and whitespace.",
            "x[::-1]",
            ["x", "x[::-1].lower()", "x.strip()[::-1]"],
            ["Ab ", "xy", ""],
        ),
        (
            "minimum",
            "Minimum of a nonempty list of integers.",
            "min(x)",
            ["max(x)", "x[0]", "min(x)+1"],
            [[3, 1, 2], [-4], [0, 2]],
        ),
        (
            "unique-count",
            "Count distinct case-sensitive strings in a list.",
            "len(set(x))",
            ["len(x)", "len(set(v.lower() for v in x))", "max(1,len(set(x)))"],
            [[], ["a", "a"], ["a", "A"]],
        ),
    ]
    for name, requirement, expression, mutants, values in test_specs:
        driver = (
            "import json,sys\nfrom pathlib import Path\n"
            'cases=json.loads(Path("cases.json").read_text()); variant=json.load(sys.stdin)\n'
            f"def reference(x): return {expression}\n"
            "def mutant(x):\n    return ["
            + ",".join("lambda:" + m for m in mutants)
            + "][variant-1]()\n"
            "valid=isinstance(cases,list) and 1<=len(cases)<=20\n"
            'try:\n    valid=valid and all(isinstance(c,dict) and set(c)=={"input","expected"} '
            'and type(reference(c["input"])) is type(c["expected"]) '
            'and reference(c["input"])==c["expected"] for c in cases)\n'
            "except Exception: valid=False\n"
            'if not valid: print("INVALID")\nelif variant==0: print("PASS")\n'
            'else:\n    print("DETECTED" if any(type(mutant(c["input"])) i'
            's not type(c["expected"]) '
            'or mutant(c["input"])!=c["expected"] for c in cases) else "MISS")\n'
        )
        examples = [{"input": v, "expected": eval(expression, {"x": v})} for v in values]
        tasks.append(
            Fixture(
                "test-" + name,
                "test-generation",
                "Write cases.json as a JSON list of objects with exactly input and expected. "
                + requirement
                + (
                    " Include boundaries and representative values that distingui"
                    "sh plausible incorrect implementations. Maximum 20 cases."
                ),
                {"cases.json": "[]\n", "driver.py": driver},
                {"cases.json": json.dumps(examples) + "\n", "driver.py": driver},
                tuple((v, "PASS" if v == 0 else "DETECTED") for v in range(4)),
                writable="cases.json",
                prohibited=("driver.py",),
                command=("python", "-I", "driver.py"),
            )
        )
    return tuple(tasks)
