"""End-to-end greenfield project trial; trusted references never reach workers."""

import argparse
import base64
import json
from pathlib import Path

from gflo.autonomy import FeaturePolicy, build_feature
from gflo.broker import DockerBroker, SourceBundle
from gflo.contracts import WINDOW_PROFILE
from gflo.gates import ProcessCase, ProcessGate
from gflo.ledger import WorkLedger
from gflo.model import ModelProfile
from gflo.planning import RepositoryFeatureRequest
from gflo.records import ContextBudget
from gflo.repository import snapshot_bundle

HERE = Path(__file__).resolve().parent
OUTPUTS = (
    "taskdock.py",
    "taskdock_cli.py",
    "pyproject.toml",
    "README.md",
    "tests/test_taskdock.py",
)
BASE = json.loads((HERE.parent / "window-reasoning/frozen-features.json").read_text())["2"]
IMAGE = BASE["request"]["environments"]["python"]["image"]


def gates():
    return {
        name: ProcessGate(
            cases=(
                ProcessCase(
                    command=("python", "-B", "-c", (HERE / f"checks/{name}.py").read_text()),
                    expected_stdout=name + "-ok\n",
                    seconds=30.0,
                ),
            )
        )
        for name in ("api", "cli", "package", "docs", "tests")
    }


def reference():
    return SourceBundle(files={p: (HERE / "reference" / Path(p).name).read_text() for p in OUTPUTS})


def preflight():
    root = Path(".gflo/evidence/small-project-preflight-v2")
    root.mkdir(parents=True, exist_ok=False)
    results = []
    summaries = []
    with WorkLedger(root / "ledger.db") as ledger:
        broker = DockerBroker(ledger.artifacts, IMAGE)
        broker.qualify()
        source = reference()
        digest = ledger.artifacts.publish(source.canonical().encode())
        checks = gates()
        checks["heldout"] = ProcessGate(
            cases=(
                ProcessCase(
                    command=("python", "-B", "-c", (HERE / "heldout.py").read_text()),
                    expected_stdout="heldout-ok\n",
                    seconds=30.0,
                ),
            )
        )
        for name, gate in checks.items():
            case = gate.cases[0]
            result = broker.execute(
                digest, case.command, seconds=case.seconds, purpose="validation"
            )
            results.append(dict(gate=name, execution=result.model_dump(mode="json")))
            (root / "preflight.json").write_text(json.dumps(results, indent=2) + "\n")
            summaries.append(
                dict(
                    gate=name,
                    gate_digest=gate.digest(),
                    candidate_digest=result.candidate_digest,
                    exit_code=result.exit_code,
                    outcome=result.outcome,
                    stdout_matches=base64.b64decode(result.stdout_base64).decode()
                    == case.expected_stdout,
                )
            )
            (HERE / "preflight.json").write_text(json.dumps(summaries, indent=2) + "\n")
            assert result.exit_code == 0, (name, result.model_dump(mode="json"))
            assert base64.b64decode(result.stdout_base64).decode() == case.expected_stdout
            print("preflight", name, "passed", flush=True)


def main(profile):
    checks = gates()
    preflight_rows = json.loads((HERE / "preflight.json").read_text())
    for name, gate in checks.items():
        row = next(row for row in preflight_rows if row["gate"] == name)
        assert row["exit_code"] == 0 and row["gate_digest"] == gate.digest()
        assert row["stdout_matches"]
    root = Path(".gflo/evidence/small-project-v1")
    root.mkdir(parents=True, exist_ok=False)
    brief = (HERE / "brief.md").read_text()
    introduction, sections = brief.split("## Storage API", 1)
    storage, sections = sections.split("## CLI", 1)
    cli, sections = sections.split("## Packaging", 1)
    packaging, tests_docs = sections.split("## Tests and documentation", 1)
    rows = []
    for number in (1, 2, 3):
        name = f"trial-{number}"
        path = root / name
        path.mkdir()
        with WorkLedger(path / "ledger.db") as ledger:
            source = snapshot_bundle(
                ledger.artifacts,
                SourceBundle(
                    files={
                        "BRIEF.md": brief,
                        "archive/preserved.txt": "Unrelated original bytes.\n",
                    }
                ),
            )
            request = RepositoryFeatureRequest(
                feature_id=f"taskdock-{name}",
                objective=introduction.strip(),
                requirements={
                    "storage": "Storage API" + storage,
                    "cli": "CLI" + cli,
                    "packaging": "Packaging" + packaging,
                    "tests-docs": tests_docs,
                },
                source=source,
                allowed_paths=OUTPUTS,
                environments={
                    "python": {
                        "image": IMAGE,
                        "description": "Pinned Python with setuptools, wheel and pytest; offline stdlib runtime",
                    }
                },
            )
            policy = FeaturePolicy(
                request_digest=request.digest(),
                file_gates=dict(
                    zip(OUTPUTS, (checks[n] for n in ("api", "cli", "package", "docs", "tests")))
                ),
                execution_paths=("BRIEF.md", *OUTPUTS),
                planning_paths=("BRIEF.md",),
                integration_gates=checks,
                environment_id="python",
                model_profile=ModelProfile.model_validate_json(
                    json.dumps({**BASE["review"]["model_profile"], "profile_id": profile})
                ),
                deployment=BASE["review"]["deployment"],
                context_budget=ContextBudget(total_tokens=16384, output_tokens=6144),
                max_tasks=5,
                max_attempts=2,
                max_model_turns=3,
                max_reserved_tokens=565248,
            )
            fixture = dict(
                request=request.model_dump(mode="json"), policy=policy.model_dump(mode="json")
            )
            (path / "fixture.json").write_text(json.dumps(fixture, indent=2) + "\n")
            (HERE / f"{name}-fixture.json").write_text(json.dumps(fixture, indent=2) + "\n")
            rows.append(
                dict(
                    name=name,
                    request_digest=request.digest(),
                    policy_digest=policy.digest(),
                    max_responses=36,
                    reserved_tokens=565248,
                )
            )
    (root / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    (HERE / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    print("Three complete-project builds frozen; 1695744 tokens reserved", flush=True)
    for row in rows:
        path = root / row["name"]
        fixture = json.loads((path / "fixture.json").read_text())
        request = RepositoryFeatureRequest.model_validate_json(json.dumps(fixture["request"]))
        policy = FeaturePolicy.model_validate_json(json.dumps(fixture["policy"]))
        with WorkLedger(path / "ledger.db") as ledger:
            result = build_feature(ledger, request, policy, path / "build", lambda: request.source)
            print(row["name"], result["status"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--profile", default=WINDOW_PROFILE)
    args = parser.parse_args()
    if args.preflight:
        preflight()
    else:
        assert (HERE / "preflight.json").exists(), "Preflight required before inference"
        main(args.profile)
