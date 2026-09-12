"""Fresh model-planned repairs over two challenged complete projects."""

import argparse
import importlib.util
import json
from pathlib import Path

from gflo.autonomy import FeaturePolicy, build_feature
from gflo.broker import DockerBroker, SourceBundle
from gflo.gates import ProcessCase, ProcessGate
from gflo.ledger import WorkLedger
from gflo.planning import RepositoryFeatureRequest
from gflo.repository import snapshot_bundle

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/small-project-repair-v1")
spec = importlib.util.spec_from_file_location("base_campaign", HERE / "campaign.py")
assert spec and spec.loader
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

REGRESSIONS = """

@pytest.mark.parametrize("title", ["\\nvalid", "valid\\n", "\\rvalid", "valid\\r"])
def test_raw_title_linebreaks(tmp_path, title):
    path = tmp_path / "tasks.json"
    with pytest.raises(ValueError):
        api.add_task(path, title)
    assert not path.exists()

def test_version_float_rejected(tmp_path):
    path = tmp_path / "tasks.json"
    raw = '{"version": 1.0, "tasks": []}'
    path.write_text(raw)
    with pytest.raises(ValueError):
        api.list_tasks(path)
    assert path.read_text() == raw
"""


def checks():
    gates = base.gates()
    edge = ProcessCase(
        command=("python", "-B", "-c", (HERE / "edge_audit.py").read_text()),
        expected_stdout="edge-ok\n",
        seconds=30.0,
    )
    gates["api"] = ProcessGate(cases=(edge, *gates["api"].cases))
    mutants = {
        "raw-title": (
            "\n_saved_add = add_task\ndef add_task(path, title):\n    return _sav"
            "ed_add(path, title.strip() if isinstance(title, str) else title)\n"
        ),
        "version-float": (
            "\n_saved_list = list_tasks\ndef list_tasks(path, include_done=False"
            "):\n    import json\n    from pathlib import Path\n    if Path(path)"
            ".exists() and type(json.loads(Path(path).read_text()).get('versio"
            "n')) is float:\n        return []\n    return _saved_list(path, inc"
            "lude_done)\n"
        ),
    }
    case = gates["tests"].cases[0]
    script = case.command[-1]
    assert script.count("runner = ") == 1
    script = script.replace("runner = ", "mutants.update(" + repr(mutants) + ")\nrunner = ", 1)
    gates["tests"] = ProcessGate(
        cases=(case.model_copy(update={"command": ("python", "-B", "-c", script)}),)
    )
    return gates


def main(fixed_symbols=False, scoped_requirements=False):
    global ROOT
    if scoped_requirements:
        ROOT = Path(".gflo/evidence/small-project-repair-v3")
    elif fixed_symbols:
        ROOT = Path(".gflo/evidence/small-project-repair-v2")
    prefix = "repair-v3" if scoped_requirements else "repair-v2" if fixed_symbols else "repair"
    ROOT.mkdir(parents=True, exist_ok=False)
    gates = checks()
    summaries = []
    # New reference tests qualify the added faults, never entering worker input.
    with WorkLedger(ROOT / "preflight.db") as ledger:
        broker = DockerBroker(ledger.artifacts, base.IMAGE)
        broker.qualify()
        source = base.reference()
        source = SourceBundle(
            files={
                **source.files,
                "tests/test_taskdock.py": source.files["tests/test_taskdock.py"] + REGRESSIONS,
            }
        )
        digest = ledger.artifacts.publish(source.canonical().encode())
        for name in ("api", "tests"):
            for case in gates[name].cases:
                result = broker.execute(
                    digest, case.command, seconds=case.seconds, purpose="validation"
                )
                evidence = ledger.artifacts.publish(result.canonical().encode())
                summaries.append(
                    dict(
                        gate=name,
                        exit_code=result.exit_code,
                        evidence_digest=evidence,
                        candidate_digest=digest,
                        gate_digest=gates[name].digest(),
                    )
                )
                (HERE / f"{prefix}-preflight.json").write_text(
                    json.dumps(summaries, indent=2) + "\n"
                )
                assert result.exit_code == 0, result
    rows = []
    for number in (1, 2):
        name = f"trial-{number}"
        path = ROOT / name
        path.mkdir()
        original = json.loads((HERE / f"{name}-fixture.json").read_text())
        source = SourceBundle.model_validate_json(
            (HERE / f"{name}-repair-source.json").read_bytes()
        )
        with WorkLedger(path / "ledger.db") as ledger:
            request = RepositoryFeatureRequest.model_validate_json(json.dumps(original["request"]))
            requirements = dict(request.requirements)
            requirements["tests-docs"] += (
                "\nAdd regression cases to tests/test_taskdock.py rejecting leading/trailing CR/LF "
                "in raw titles and storage version 1.0, preserving bytes on rejection. These tests "
                "must reject faults that strip raw line breaks before validation "
                "or accept a float version."
            )
            if scoped_requirements:
                requirements = {
                    "storage": requirements["storage"],
                    "tests": requirements["tests-docs"].split("README.md must", 1)[0]
                    + "\nAdd regression cases"
                    + requirements["tests-docs"].split("\nAdd regression cases", 1)[1],
                }
            request = request.model_copy(
                update={
                    "feature_id": f"taskdock-edge-repair-{number}",
                    "objective": (
                        "Repair taskdock.py and tests/test_taskdock.py in this challenged project "
                        "to meet the original requirements. Audit found raw leading/trailing CR/LF "
                        "titles and storage version 1.0 accepted. Preserve CLI, packaging, README "
                        "and all other files. Plan bounded repair work; prior historical "
                        "acceptance does not establish correctness."
                    ),
                    "requirements": requirements,
                    "allowed_paths": ("taskdock.py", "tests/test_taskdock.py"),
                    "source": snapshot_bundle(ledger.artifacts, source),
                }
            )
            policy = FeaturePolicy.model_validate_json(json.dumps(original["policy"]))
            policy = policy.model_copy(
                update={
                    "request_digest": request.digest(),
                    "file_gates": {
                        "taskdock.py": gates["api"],
                        "tests/test_taskdock.py": gates["tests"],
                    },
                    "planning_paths": ("taskdock.py", "tests/test_taskdock.py"),
                    "integration_gates": gates,
                    "max_tasks": 2,
                    "max_reserved_tokens": 270336,
                }
            )
            # Revalidate exact schemas before freezing each new work identity.
            request = RepositoryFeatureRequest.model_validate_json(request.canonical())
            policy = FeaturePolicy.model_validate_json(policy.canonical())
            fixture = dict(
                request=request.model_dump(mode="json"), policy=policy.model_dump(mode="json")
            )
            (path / "fixture.json").write_text(json.dumps(fixture, indent=2) + "\n")
            fixture_path = HERE / f"{name}-repair-fixture.json"
            if scoped_requirements:
                previous = json.loads(fixture_path.read_text())
                for field in ("file_gates", "integration_gates", "planning_paths"):
                    assert previous["policy"][field] == fixture["policy"][field]
                assert previous["request"]["source"] == fixture["request"]["source"]
                (HERE / f"{name}-repair-v3-fixture.json").write_text(
                    json.dumps(fixture, indent=2) + "\n"
                )
            elif fixed_symbols:
                assert json.loads(fixture_path.read_text()) == fixture
            else:
                fixture_path.write_text(json.dumps(fixture, indent=2) + "\n")
            rows.append(
                dict(
                    name=name,
                    request_digest=request.digest(),
                    policy_digest=policy.digest(),
                    max_responses=18,
                    reserved_tokens=270336,
                )
            )
    (ROOT / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    (HERE / f"{prefix}-schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(
        "Two repairs frozen after strengthened-gate preflight; 540672 tokens reserved", flush=True
    )
    for row in rows:
        path = ROOT / row["name"]
        fixture = json.loads((path / "fixture.json").read_text())
        request = RepositoryFeatureRequest.model_validate_json(json.dumps(fixture["request"]))
        policy = FeaturePolicy.model_validate_json(json.dumps(fixture["policy"]))
        with WorkLedger(path / "ledger.db") as ledger:
            result = build_feature(ledger, request, policy, path / "build", lambda: request.source)
            print(row["name"], result["status"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixed-symbols", action="store_true")
    parser.add_argument("--scoped-requirements", action="store_true")
    args = parser.parse_args()
    main(args.fixed_symbols, args.scoped_requirements)
