"""Two fresh projects, two trials each, with independent gate preflight."""

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
ROOT = Path(".gflo/evidence/varied-projects-v1")
NAMES = ("csvfold", "dagorder")
OUTPUTS = ("core.py", "cli.py", "pyproject.toml", "README.md", "tests/test_core.py")
BASE = json.loads((HERE.parent / "window-reasoning/frozen-features.json").read_text())["2"]
IMAGE = BASE["request"]["environments"]["python"]["image"]


def gates(name):
    return {
        key: ProcessGate(
            cases=(
                ProcessCase(
                    command=(
                        "python",
                        "-B",
                        "-c",
                        (HERE / name / "checks" / f"{key}.py").read_text(),
                    ),
                    expected_stdout=key + "-ok\n",
                    seconds=60,
                ),
            )
        )
        for key in ("api", "cli", "package", "docs", "tests")
    }


def preflight():
    root = Path(".gflo/evidence/varied-projects-preflight-v1")
    root.mkdir(parents=True, exist_ok=False)
    rows = []
    with WorkLedger(root / "ledger.db") as ledger:
        broker = DockerBroker(ledger.artifacts, IMAGE)
        broker.qualify()
        for name in NAMES:
            source = SourceBundle(
                files={p: (HERE / name / "reference" / p).read_text() for p in OUTPUTS}
            )
            digest = ledger.artifacts.publish(source.canonical().encode())
            checks = gates(name)
            checks["heldout"] = ProcessGate(
                cases=(
                    ProcessCase(
                        command=("python", "-B", "-c", (HERE / name / "heldout.py").read_text()),
                        expected_stdout="heldout-ok\n",
                        seconds=30,
                    ),
                )
            )
            for key, gate in checks.items():
                case = gate.cases[0]
                result = broker.execute(
                    digest, case.command, seconds=case.seconds, purpose="validation"
                )
                evidence = ledger.artifacts.publish(result.canonical().encode())
                stdout = base64.b64decode(result.stdout_base64).decode()
                rows.append(
                    dict(
                        project=name,
                        gate=key,
                        gate_digest=gate.digest(),
                        evidence_digest=evidence,
                        exit_code=result.exit_code,
                        stdout_matches=stdout == case.expected_stdout,
                    )
                )
                (HERE / "preflight.json").write_text(json.dumps(rows, indent=2) + "\n")
                assert result.exit_code == 0 and stdout == case.expected_stdout, (name, key, result)
                print("preflight", name, key, "passed", flush=True)


def main():
    checked = json.loads((HERE / "preflight.json").read_text())
    for name in NAMES:
        for key, gate in gates(name).items():
            row = next(r for r in checked if r["project"] == name and r["gate"] == key)
            assert (
                row["gate_digest"] == gate.digest()
                and row["exit_code"] == 0
                and row["stdout_matches"]
            )
    ROOT.mkdir(parents=True, exist_ok=False)
    rows = []
    for name in NAMES:
        checks = gates(name)
        for number in (1, 2):
            trial = f"{name}-{number}"
            path = ROOT / trial
            path.mkdir()
            with WorkLedger(path / "ledger.db") as ledger:
                source = snapshot_bundle(
                    ledger.artifacts,
                    SourceBundle(
                        files={
                            "BRIEF.md": (HERE / name / "brief.md").read_text(),
                            "archive/preserved.txt": "Preserve these original bytes.\n",
                        }
                    ),
                )
                request = RepositoryFeatureRequest(
                    feature_id=trial,
                    objective=(
                        f"Create complete {name} project exactly as specified. "
                        "Model produces all five output files; preserve initial brief and sentinel."
                    ),
                    requirements=json.loads((HERE / name / "requirements.json").read_text()),
                    source=source,
                    allowed_paths=OUTPUTS,
                    environments={
                        "python": dict(
                            image=IMAGE,
                            description=(
                                "Offline Python with setuptools, wheel, pytest; stdlib runtime"
                            ),
                        )
                    },
                )
                policy = FeaturePolicy(
                    request_digest=request.digest(),
                    file_gates=dict(
                        zip(
                            OUTPUTS, (checks[n] for n in ("api", "cli", "package", "docs", "tests"))
                        )
                    ),
                    execution_paths=("BRIEF.md", *OUTPUTS),
                    planning_paths=("BRIEF.md",),
                    integration_gates=checks,
                    environment_id="python",
                    model_profile=ModelProfile.model_validate_json(
                        json.dumps(
                            {**BASE["review"]["model_profile"], "profile_id": WINDOW_PROFILE}
                        )
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
                (HERE / f"{trial}-fixture.json").write_text(json.dumps(fixture, indent=2) + "\n")
                rows.append(
                    dict(
                        name=trial,
                        project=name,
                        request_digest=request.digest(),
                        policy_digest=policy.digest(),
                        max_responses=36,
                        reserved_tokens=565248,
                    )
                )
    (ROOT / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    (HERE / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    print("Four builds frozen; 2260992 tokens reserved", flush=True)
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
    parser.add_argument("--preflight", action="store_true")
    if parser.parse_args().preflight:
        preflight()
    else:
        main()
