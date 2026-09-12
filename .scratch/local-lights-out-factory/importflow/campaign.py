"""Reusable section/file-gate preparation for frozen factory project qualification."""

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
ROOT = Path(".gflo/evidence/importflow-v1")
FILES = {
    "blobs.py": "blobs",
    "tabular.py": "tabular",
    "jobs.py": "jobs",
    "worker.py": "worker",
    "api.py": "api",
    "pyproject.toml": "package",
    "README.md": "docs",
    "tests/test_importflow.py": "tests",
}
OUTPUTS = tuple(FILES)
BASE = json.loads((HERE.parent / "window-reasoning/frozen-features.json").read_text())["2"]
IMAGE = (HERE / "provision/image-id.txt").read_text().strip()


def gates():
    checks = {}
    for name in FILES.values():
        checks[name] = ProcessGate(
            cases=(
                ProcessCase(
                    command=("python", "-B", "-c", (HERE / "checks" / f"{name}.py").read_text()),
                    expected_stdout=name + "-ok\n",
                    seconds=60,
                ),
            )
        )
    streaming = ProcessCase(
        command=("python", "-B", "-c", (HERE / "checks/streaming.py").read_text()),
        expected_stdout="streaming-ok\n",
        seconds=60,
    )
    checks["api"] = ProcessGate(cases=(*checks["api"].cases, streaming))
    return checks


def preflight():
    root = Path(".gflo/evidence/importflow-preflight-v2")
    root.mkdir(parents=True, exist_ok=False)
    rows = []
    with WorkLedger(root / "ledger.db") as ledger:
        broker = DockerBroker(ledger.artifacts, IMAGE)
        broker.qualify()
        source = SourceBundle(files={p: (HERE / "reference" / p).read_text() for p in OUTPUTS})
        digest = ledger.artifacts.publish(source.canonical().encode())
        checks = gates()
        checks["heldout"] = ProcessGate(
            cases=(
                ProcessCase(
                    command=("python", "-B", "-c", (HERE / "heldout.py").read_text()),
                    expected_stdout="heldout-ok\n",
                    seconds=60,
                ),
            )
        )
        for name, gate in checks.items():
            for number, case in enumerate(gate.cases):
                result = broker.execute(
                    digest, case.command, seconds=case.seconds, purpose="validation"
                )
                evidence = ledger.artifacts.publish(result.canonical().encode())
                stdout = base64.b64decode(result.stdout_base64).decode()
                rows.append(
                    dict(
                        gate=name,
                        case=number,
                        gate_digest=gate.digest(),
                        candidate_digest=digest,
                        evidence_digest=evidence,
                        exit_code=result.exit_code,
                        stdout_matches=stdout == case.expected_stdout,
                    )
                )
                (HERE / "preflight.json").write_text(json.dumps(rows, indent=2) + "\n")
                if result.exit_code != 0 or stdout != case.expected_stdout:
                    print(name, base64.b64decode(result.stderr_base64).decode(), stdout, flush=True)
                    raise AssertionError((name, result.exit_code))
                print("preflight", name, number, "passed", flush=True)


def main():
    checks = gates()
    preflight_rows = json.loads((HERE / "preflight.json").read_text())
    for name, gate in checks.items():
        for number, case in enumerate(gate.cases):
            row = next(r for r in preflight_rows if r["gate"] == name and r["case"] == number)
            assert (
                row["exit_code"] == 0
                and row["stdout_matches"]
                and row["gate_digest"] == gate.digest()
            )
    ROOT.mkdir(parents=True, exist_ok=False)
    brief = (HERE / "brief.md").read_text()
    introduction, *sections = brief.split("\n## ")
    requirements = {
        key: section
        for key, section in zip(
            ("blobs", "tabular", "jobs", "worker", "api", "package", "tests", "docs"),
            sections,
            strict=True,
        )
    }
    rows = []
    for number in (1, 2, 3):
        name = f"trial-{number}"
        path = ROOT / name
        path.mkdir()
        with WorkLedger(path / "ledger.db") as ledger:
            source = snapshot_bundle(
                ledger.artifacts,
                SourceBundle(
                    files={
                        "BRIEF.md": brief,
                        "ENVIRONMENT.md": (HERE / "ENVIRONMENT.md").read_text(),
                        "archive/preserved.txt": "Preserve original bytes.\n",
                    }
                ),
            )
            request = RepositoryFeatureRequest(
                feature_id=f"importflow-{number}",
                objective=introduction,
                requirements=requirements,
                source=source,
                allowed_paths=OUTPUTS,
                environments={
                    "python": dict(
                        image=IMAGE,
                        description=(
                            "Pinned FastAPI/uvicorn/httpx/pytest; no network; "
                            "SQLite WAL and local filesystem"
                        ),
                    )
                },
            )
            policy = FeaturePolicy(
                request_digest=request.digest(),
                file_gates={p: checks[g] for p, g in FILES.items()},
                execution_paths=("BRIEF.md", "ENVIRONMENT.md", *OUTPUTS),
                planning_paths=("BRIEF.md", "ENVIRONMENT.md"),
                integration_gates=checks,
                environment_id="python",
                model_profile=ModelProfile.model_validate_json(
                    json.dumps({**BASE["review"]["model_profile"], "profile_id": WINDOW_PROFILE})
                ),
                deployment=BASE["review"]["deployment"],
                context_budget=ContextBudget(total_tokens=16384, output_tokens=6144),
                max_tasks=8,
                max_attempts=2,
                max_model_turns=3,
                max_reserved_tokens=860160,
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
                    max_responses=54,
                    reserved_tokens=860160,
                )
            )
    (ROOT / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    (HERE / "schedule.json").write_text(json.dumps(rows, indent=2) + "\n")
    print("Three builds frozen; 2580480 tokens reserved", flush=True)
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
