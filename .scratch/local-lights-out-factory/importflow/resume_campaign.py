"""One bounded supervised continuation; preserve passed modules and failed histories."""

import json
from pathlib import Path

import prepared_campaign as base
import system_preflight as system

from gflo.autonomy import FeaturePolicy, build_feature
from gflo.broker import DockerBroker, SourceBundle
from gflo.ledger import WorkLedger
from gflo.planning import RepositoryFeatureRequest
from gflo.qualification import prepared_planner
from gflo.repository import SnapshotSource, snapshot_bundle

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/importflow-resume-v1")
PRIOR = Path(".gflo/evidence/importflow-prepared-v1/trial-1")
FAILED = "3618249bac9396b0ee623d64f56edea5b248734d904daf5c94c3cff122a33314"


def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    root = ROOT / "trial-1"
    root.mkdir()
    prior = json.loads((PRIOR / "build/result.json").read_text())
    fixture = json.loads((PRIOR / "fixture.json").read_text())
    with WorkLedger(PRIOR / "ledger.db") as old:
        source = SnapshotSource(old.artifacts, prior["feature_result"]["source"])
        files = {p: source.read_bytes(p).decode() for p in source.files}
        draft = SourceBundle.model_validate_json(old.artifacts.read(FAILED))
        assert "tabular.py" not in files
        files["tabular.py"] = draft.files["tabular.py"]
    bundle = SourceBundle(files=files)
    (HERE / "resume-source.json").write_text(bundle.canonical() + "\n")
    checks = system.gates()
    with WorkLedger(root / "ledger.db") as ledger:
        source = snapshot_bundle(ledger.artifacts, bundle)
        # Recheck preserved provider bytes on the actually fixed runtime image.
        broker = DockerBroker(ledger.artifacts, system.IMAGE)
        broker.qualify()
        digest = ledger.artifacts.publish(bundle.canonical().encode())
        receipts = []
        for name in ("blobs", "jobs"):
            for case in checks[name].cases:
                result = broker.execute(
                    digest, case.command, seconds=case.seconds, purpose="validation"
                )
                evidence = ledger.artifacts.publish(result.canonical().encode())
                assert result.exit_code == 0 and result.stdout.decode() == case.expected_stdout, (
                    result
                )
                receipts.append(
                    dict(
                        gate=name,
                        gate_digest=checks[name].digest(),
                        evidence_digest=evidence,
                        candidate_digest=digest,
                    )
                )
        (HERE / "resume-provider-checks.json").write_text(json.dumps(receipts, indent=2) + "\n")
        request = RepositoryFeatureRequest.model_validate_json(json.dumps(fixture["request"]))
        allowed = tuple(p for p in base.OUTPUTS if p not in ("blobs.py", "jobs.py"))
        requirements = {
            key: value
            for key, value in request.requirements.items()
            if key not in ("blobs", "jobs")
        }
        requirements["tabular"] += (
            "\nObserved prior failure: empty input incorrectly returned []. Empty input has no required header and must raise ValueError with row 1. Preserve strict validation for every other case."
        )
        request = request.model_copy(
            update={
                "feature_id": "importflow-supervised-resume-1",
                "objective": "Complete the remaining Importflow modules from a partial model build. Preserve passed blobs.py and jobs.py. The existing tabular.py is a retained failed model candidate and requires correction; no prior parser acceptance is implied. Keep responses compact and change only the current task file.",
                "requirements": requirements,
                "allowed_paths": allowed,
                "source": source,
                "environments": {
                    "python": {
                        "image": system.IMAGE,
                        "description": "Pinned FastAPI environment; SQLite 3.51.3 proven after environment sanitization",
                    }
                },
            }
        )
        request = RepositoryFeatureRequest.model_validate_json(request.canonical())
        policy = FeaturePolicy.model_validate_json(json.dumps(fixture["policy"]))
        policy = policy.model_copy(
            update={
                "request_digest": request.digest(),
                "file_gates": {p: checks[base.FILES[p]] for p in allowed},
                "integration_gates": checks,
                "max_tasks": 6,
                "max_reserved_tokens": 663552,
            }
        )
        policy = FeaturePolicy.model_validate_json(policy.canonical())
        proposal = base.make_proposal(request)
        frozen = dict(
            request=request.model_dump(mode="json"),
            policy=policy.model_dump(mode="json"),
            proposal=proposal.model_dump(mode="json"),
        )
        (root / "fixture.json").write_text(json.dumps(frozen, indent=2) + "\n")
        (HERE / "resume-fixture.json").write_text(json.dumps(frozen, indent=2) + "\n")
        schedule = [
            dict(
                name="trial-1",
                request_digest=request.digest(),
                policy_digest=policy.digest(),
                max_responses=42,
                reserved_tokens=663552,
                prior_request_digest=prior["request_digest"],
                adopted_failed_candidate=FAILED,
            )
        ]
        (ROOT / "schedule.json").write_text(json.dumps(schedule, indent=2) + "\n")
        (HERE / "resume-schedule.json").write_text(json.dumps(schedule, indent=2) + "\n")
        print(
            "Preserved providers pass fixed image; continuation frozen with 663552 reserved tokens",
            flush=True,
        )
        result = build_feature(
            ledger,
            request,
            policy,
            root / "build",
            lambda: request.source,
            planner=prepared_planner(proposal),
        )
        print(result["status"], flush=True)


if __name__ == "__main__":
    main()
