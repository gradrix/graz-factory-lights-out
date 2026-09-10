"""Fixed-budget comparison of one test worker and two behavior-scoped workers."""
# Preserve exact validator strings used by the pinned campaign.
# ruff: noqa: E501

import argparse
import hashlib
import json
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.contracts import InterfaceBundle
from gflo.gates import ProcessCase, ProcessGate
from gflo.ledger import WorkLedger
from gflo.model import ModelProfile
from gflo.planning import PlannedTask, PlanProposal, RepositoryFeatureRequest
from gflo.preparation import PlanReview, TaskReview
from gflo.progression import FeaturePlan, run_feature
from gflo.records import ContextBudget
from gflo.repository import snapshot_bundle

HERE = Path(__file__).parent
REQUIREMENTS = {
    "values": "Write pytest tests against actual large.chosen_value and consumer.render. "
    "chosen_value() returns 42. Built-in ints clamp to 0..100 inclusive: cover "
    "negative, both bounds, interior and over-100 inputs. render(value) returns "
    '"value=" followed by the decimal clamped value. Tests must detect unclamped, '
    "constant-return and incorrect caller-format implementations with assertions.",
    "types": "Write pytest tests against actual large.chosen_value. Only exact built-in ints "
    "are accepted. Booleans, integer subclasses, floats, strings, None and other "
    "non-integer types raise TypeError. Tests must detect a type-permissive "
    "implementation with assertions.",
}
VALUES = """from large import chosen_value
from consumer import render
import pytest

def test_default():
    assert chosen_value() == 42

@pytest.mark.parametrize('value,expected', [(-5,0),(0,0),(1,1),(42,42),(100,100),(105,100)])
def test_values(value, expected):
    assert chosen_value(value) == expected
    assert render(value) == 'value=' + str(expected)
"""
TYPES = """from large import chosen_value
import pytest
class SubInt(int):
    pass

@pytest.mark.parametrize('value', [True,False,SubInt(1),1.0,'1',None,[],{},1+0j])
def test_types(value):
    with pytest.raises(TypeError):
        chosen_value(value)
"""


def source():
    text = (
        "".join(f"constant_{i} = {i}\n" for i in range(5000))
        + (HERE / "accepted-function.py").read_text()
        + "".join(f"constant_{i} = {i}\n" for i in range(5000, 10000))
    )
    files = {
        "large.py": text,
        "consumer.py": "from large import chosen_value\ndef render(value):\n"
        '    return "value=" + str(chosen_value(value))\n',
    }
    fixture = json.loads((HERE / "fixture.json").read_text())
    assert {p: hashlib.sha256(t.encode()).hexdigest() for p, t in files.items()} == fixture[
        "source_files_sha256"
    ]
    return SourceBundle(files=files)


def gate(paths, faults):
    # The same fault definitions and verdict logic apply to both conditions.
    code = """import ast,hashlib,json,subprocess,sys
from pathlib import Path
paths=PATHS
faults=FAULTS
original={p:Path(p).read_text() for p in ['large.py','consumer.py']}
assert {p:hashlib.sha256(t.encode()).hexdigest() for p,t in original.items()} == EXPECTED
node=next(n for n in ast.parse(original['large.py']).body if isinstance(n,ast.FunctionDef) and n.name=='chosen_value')
lines=original['large.py'].splitlines(keepends=True)
prefix=''.join(lines[:node.lineno-1]); suffix=''.join(lines[node.end_lineno:])
for fault in ['correct']+faults:
    changed=dict(original)
    if fault=='unclamped':changed['large.py']=prefix+'def chosen_value(value=42):\\n    if type(value) is not int: raise TypeError()\\n    return value\\n'+suffix
    if fault=='constant':changed['large.py']=prefix+'def chosen_value(value=42):\\n    if type(value) is not int: raise TypeError()\\n    return 42\\n'+suffix
    if fault=='permissive':changed['large.py']=prefix+'def chosen_value(value=42):\\n    return max(0,min(100,value))\\n'+suffix
    if fault=='caller':changed['consumer.py']=original['consumer.py'].replace('"value="','"wrong="')
    for p,t in changed.items():Path(p).write_text(t)
    r=subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',*paths],capture_output=True,text=True)
    assert {p:Path(p).read_text() for p in original} == changed, 'tests mutated source'
    if fault=='correct':assert r.returncode==0,(r.stdout,r.stderr)
    else:assert r.returncode==1 and 'failed' in r.stdout and ('AssertionError' in r.stdout or 'Failed:' in r.stdout),(fault,r.stdout,r.stderr)
for p,t in original.items():Path(p).write_text(t)
print('qualified')
"""
    fixture = json.loads((HERE / "fixture.json").read_text())
    code = (
        code.replace("PATHS", repr(paths))
        .replace("FAULTS", repr(faults))
        .replace("EXPECTED", repr(fixture["source_files_sha256"]))
    )
    compile(code, "gate", "exec")
    return ProcessGate(
        cases=(
            ProcessCase(
                command=("python", "-B", "-c", code), expected_stdout="qualified\n", seconds=30
            ),
        )
    )


def plan(store, name, split):
    fixture = json.loads((HERE / "fixture.json").read_text())
    ref = snapshot_bundle(store, source())
    groups = (
        [("values", ("values",)), ("types", ("types",))]
        if split
        else [("all", ("values", "types"))]
    )
    paths = tuple(f"tests/test_{name}.py" for name, _ in groups)
    request = RepositoryFeatureRequest(
        feature_id=name,
        objective="Add isolated regression tests for the accepted clamp and caller. "
        "Do not change production code, substitute imports, mock the tested functions, "
        "or mutate source from tests. Cover the assigned requirement groups concisely.",
        requirements=REQUIREMENTS,
        source=ref,
        allowed_paths=paths,
        environments={
            "python": {
                "image": fixture["image"],
                "description": "Pinned offline Python with pytest",
            }
        },
    )
    tasks = []
    reviews = {}
    for (task, ids), path in zip(groups, paths):
        faults = (
            ["unclamped", "constant", "caller"]
            if task == "values"
            else ["permissive"]
            if task == "types"
            else ["unclamped", "constant", "caller", "permissive"]
        )
        tasks.append(
            PlannedTask(
                task_id=task,
                objective="Write only the assigned " + ", ".join(ids) + " regression tests.",
                requirement_ids=ids,
                depends_on=(),
                writable_paths=(path,),
                read_paths=("large.py", "consumer.py"),
                environment_id="python",
                interface_contracts=(InterfaceBundle(declarations=()).canonical(),),
                acceptance_checks=(
                    "Tests pass the real implementation and reject assigned faults.",
                ),
            )
        )
        reviews[task] = TaskReview(
            execution_paths=("large.py", "consumer.py"),
            context_paths=("large.py", "consumer.py"),
            gates={"faults": gate([path], faults)},
        )
    proposal = PlanProposal(
        request_digest=request.digest(),
        questions=(),
        rationale="Reviewed experiment: fixed behavior groups and disjoint output ownership; no model planning.",
        tasks=tuple(tasks),
    )
    review = PlanReview(
        request_digest=request.digest(),
        proposal_digest=proposal.digest(),
        tasks=reviews,
        model_profile=ModelProfile.model_validate_json(json.dumps(fixture["profile"])),
        deployment=fixture["deployment"],
        context_budget=ContextBudget(total_tokens=12288, output_tokens=4096),
        max_attempts=1 if split else 2,
        max_model_turns=3,
    )
    return FeaturePlan(
        request=request,
        proposal=proposal,
        review=review,
        integration=TaskReview(
            execution_paths=("large.py", "consumer.py", *paths),
            context_paths=(),
            gates={
                "combined": gate(list(paths), ["unclamped", "constant", "caller", "permissive"])
            },
        ),
        integration_environment="python",
    )


def preflight(root):
    fixture = json.loads((HERE / "fixture.json").read_text())
    with WorkLedger(root / "preflight.db") as ledger:
        broker = DockerBroker(ledger.artifacts, fixture["image"])
        broker.qualify()
        reports = []
        for paths, texts, faults in [
            (
                ["tests/test_all.py"],
                [VALUES + "\n" + TYPES],
                ["unclamped", "constant", "caller", "permissive"],
            ),
            (["tests/test_values.py"], [VALUES], ["unclamped", "constant", "caller"]),
            (["tests/test_types.py"], [TYPES], ["permissive"]),
            (
                ["tests/test_values.py", "tests/test_types.py"],
                [VALUES, TYPES],
                ["unclamped", "constant", "caller", "permissive"],
            ),
        ]:
            bundle = SourceBundle(files={**source().files, **dict(zip(paths, texts))})
            digest = ledger.artifacts.publish(bundle.canonical().encode())
            case = gate(paths, faults).cases[0]
            execution = broker.execute(
                digest, case.command, seconds=case.seconds, purpose="validation"
            )
            reports.append(execution.model_dump(mode="json"))
            (root / "preflight.json").write_text(json.dumps(reports, indent=2) + "\n")
            assert execution.exit_code == 0 and execution.stdout == b"qualified\n", execution
    print("preflight passed", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    root = args.output
    root.mkdir(parents=True, exist_ok=False)
    preflight(root)
    if args.preflight_only:
        return
    # Freeze six runs before inference; alternate ordering to reduce simple order effects.
    schedule = [
        ("solo-1", False),
        ("split-1", True),
        ("split-2", True),
        ("solo-2", False),
        ("solo-3", False),
        ("split-3", True),
    ]
    (root / "schedule.json").write_text(json.dumps(schedule) + "\n")
    for name, split in schedule:
        trial = root / name
        trial.mkdir()
        with WorkLedger(trial / "ledger.db") as ledger:
            feature = plan(ledger.artifacts, name, split)
            assert (
                len(feature.proposal.tasks)
                * feature.review.max_attempts
                * feature.review.max_model_turns
                == 6
            )
            (trial / "plan.json").write_text(feature.canonical() + "\n")
            result = run_feature(ledger, feature, lambda: feature.request.source)
            (trial / "result.json").write_text(result.canonical() + "\n")
            print(name, result.status, flush=True)


if __name__ == "__main__":
    main()
