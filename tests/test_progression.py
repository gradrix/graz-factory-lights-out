"""Graph progression with real ledger/artifacts and deterministic process/model doubles."""

import base64
import hashlib
import json

import pytest

from gflo.broker import Execution, SourceBundle
from gflo.ledger import Conflict, WorkLedger
from gflo.model import ModelTurn
from gflo.preparation import PreparedTask
from gflo.progression import FeaturePlan, run_feature
from gflo.records import AcceptanceFinding
from gflo.repository import Repository, SnapshotSource, SourceRef, snapshot_bundle
from gflo.worker import CandidateResult


def feature(ledger):
    source = snapshot_bundle(
        ledger.artifacts,
        SourceBundle(
            files={
                "main.py": "pass\n",
                "keep.txt": "preserved",
            }
        ),
    )
    request = dict(
        feature_id="answer",
        objective="Print an answer via a provider",
        requirements={"value": "value() returns 42", "cli": "main prints 42"},
        source=source.model_dump(mode="json"),
        allowed_paths=["provider.py", "main.py"],
        environments={"python": {"image": "sha256:" + "a" * 64, "description": "Pinned Python"}},
    )
    from gflo.preparation import RepositoryFeatureRequest

    request = RepositoryFeatureRequest.model_validate_json(json.dumps(request))
    from gflo.planning import PlanProposal

    proposal = PlanProposal.model_validate_json(
        json.dumps(
            dict(
                request_digest=request.digest(),
                questions=[],
                rationale="Provider then consumer",
                tasks=[
                    dict(
                        task_id="provider",
                        objective="Implement value() returning 42",
                        requirement_ids=["value"],
                        depends_on=[],
                        writable_paths=["provider.py"],
                        read_paths=[],
                        environment_id="python",
                        interface_contracts=["provider.value() -> int, returns 42"],
                        acceptance_checks=["42"],
                    ),
                    dict(
                        task_id="consumer",
                        objective="Import value and print it",
                        requirement_ids=["cli"],
                        depends_on=["provider"],
                        writable_paths=["main.py"],
                        read_paths=["provider.py"],
                        environment_id="python",
                        interface_contracts=["Import provider.value()"],
                        acceptance_checks=["42 on stdout"],
                    ),
                ],
            )
        )
    )

    def policy(paths):
        return dict(
            execution_paths=paths,
            context_paths=paths,
            gates={
                "behavior": {
                    "cases": [dict(command=["python", "-c", "print(42)"], expected_stdout="42\n")]
                }
            },
        )

    from gflo.preparation import PlanReview

    review = PlanReview.model_validate_json(
        json.dumps(
            dict(
                request_digest=request.digest(),
                proposal_digest=proposal.digest(),
                tasks={
                    "provider": policy(["main.py"]),
                    "consumer": policy(["provider.py", "main.py"]),
                },
                model_profile=dict(
                    base_url="http://127.0.0.1:30000/v1",
                    model="gflo-local",
                    deployment_digest=hashlib.sha256(b"fixture").hexdigest(),
                ),
                deployment="fixture",
                context_budget=dict(total_tokens=8192, output_tokens=2048),
            )
        )
    )
    return FeaturePlan.model_validate_json(
        json.dumps(
            dict(
                request=request.model_dump(mode="json"),
                proposal=proposal.model_dump(mode="json"),
                review=review.model_dump(mode="json"),
                integration=policy(["provider.py", "main.py"]),
                integration_environment="python",
            )
        )
    )


class Services:
    def __init__(self):
        self.model_calls = []
        self.broker_calls = 0
        self.fail_provider = False
        self.fail_final = False
        self.interrupt = False
        self.interrupt_at = 3
        self.after_model = lambda: None

    def model(self, store, profile):
        services = self

        class Model:
            artifacts = store
            last_evidence_digest = None

            def turn(self, atom, source_digest, **kwargs):
                source = SourceBundle.model_validate_json(store.read(source_digest))
                services.model_calls.append((atom, source))
                provider = atom.writable_paths == ("provider.py",)
                if not provider:
                    assert source.files["provider.py"] == "def value(): return 42\n"
                changes = (
                    {"provider.py": "def value(): return 42\n"}
                    if provider
                    else {"main.py": "from provider import value\nprint(value())\n"}
                )
                self.last_evidence_digest = store.publish(b"model double")
                services.after_model()
                return ModelTurn(
                    manifest_digest=self.last_evidence_digest,
                    response_digest=self.last_evidence_digest,
                    result=CandidateResult(kind="candidate", changes=changes),
                    prompt_tokens=100,
                    completion_tokens=50,
                    elapsed_seconds=0.1,
                )

        model = Model()
        model.profile = profile
        return model

    def broker(self, store, image):
        services = self

        class Broker:
            artifacts = store
            image_id = image
            qualification_digest = None

            def reconcile(self):
                pass

            def qualify(self):
                self.qualification_digest = store.publish(b"qualified double")

            def execute(self, digest, command, stdin="", seconds=10, purpose="candidate"):
                services.broker_calls += 1
                if services.interrupt and services.broker_calls == services.interrupt_at:
                    raise KeyboardInterrupt()
                # Two calls per task (smoke + gate), fifth call is final validation.
                failed = (
                    services.fail_provider
                    and services.broker_calls <= 4
                    or services.fail_final
                    and services.broker_calls >= 5
                )
                return Execution(
                    candidate_digest=digest,
                    image_id=image,
                    container_id=f"double-{services.broker_calls}",
                    command=command,
                    stdin=stdin,
                    purpose=purpose,
                    outcome="completed",
                    exit_code=0,
                    oom_killed=False,
                    stdout_base64=base64.b64encode(b"0\n" if failed else b"42\n").decode(),
                    stderr_base64="",
                    elapsed_seconds=0.1,
                )

        broker = Broker()
        broker.image = image
        return broker


def run(ledger, plan, services, current=None):
    return run_feature(
        ledger,
        plan,
        current or (lambda: plan.request.source),
        model_factory=services.model,
        broker_factory=services.broker,
    )


def test_progression_preserves_dependencies_and_resumes_without_model_work(tmp_path):
    services = Services()
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        plan = feature(ledger)
        result = run(ledger, plan, services)
        assert result.status == "accepted"
        assert len(services.model_calls) == 2
        assert services.broker_calls == 5
        consumer = PreparedTask.model_validate_json(ledger.artifacts.read(result.tasks[1]))
        assert consumer.proposal_digest == plan.proposal.digest()
        assert consumer.run.atom.dependency_artifacts
        assert consumer.run.atom.capability_profile == "python-snapshot-v1"
        assert consumer.source != plan.request.source
        repo = Repository(SnapshotSource(ledger.artifacts, result.source))
        assert repo.read("keep.txt").content == "preserved"
    with WorkLedger(path) as ledger:
        assert run(ledger, plan, services) == result
    assert len(services.model_calls) == 2
    assert services.broker_calls == 5


@pytest.mark.parametrize(
    "failure,status,count", [("provider", "task-halt", 2), ("final", "integration-halt", 2)]
)
def test_failures_do_not_claim_feature_acceptance(tmp_path, failure, status, count):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        services = Services()
        services.fail_provider = failure == "provider"
        services.fail_final = failure == "final"
        result = run(ledger, plan, services)
        assert result.status == status
        assert len(services.model_calls) == count
        if failure == "provider":
            assert not result.tasks
            assert all(atom.writable_paths == ("provider.py",) for atom, _ in services.model_calls)


def test_provider_finding_blocks_completed_feature_reuse(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        services = Services()
        result = run(ledger, plan, services)
        package = PreparedTask.model_validate_json(ledger.artifacts.read(result.tasks[0]))
        state = ledger.status(package.run.atom.atom_id)
        ledger.record_finding(
            AcceptanceFinding(
                atom_id=package.run.atom.atom_id,
                contract_digest=package.run.atom.digest(),
                candidate_digest=state["candidate_digest"],
                evidence_digest=ledger.artifacts.publish(b"counterexample"),
                reason="Contradiction",
            )
        )
        with pytest.raises(Conflict, match="finding|contradict"):
            run(ledger, plan, services)
        assert len(services.model_calls) == 2


def test_external_source_change_stops_before_consumer(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        services = Services()
        current = [plan.request.source]
        services.after_model = lambda: current.__setitem__(
            0, SourceRef(kind="repository-snapshot-v1", artifact_digest="b" * 64)
        )
        with pytest.raises(Conflict, match="External source"):
            run(ledger, plan, services, lambda: current[0])
        assert len(services.model_calls) == 1


def test_interrupted_consumer_resumes_without_rebuilding_provider(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        services = Services()
        services.interrupt = True
        with pytest.raises(KeyboardInterrupt):
            run(ledger, plan, services)
        services.interrupt = False
        result = run(ledger, plan, services)
        assert result.status == "accepted"
        assert len(services.model_calls) == 2


def test_changed_review_cannot_reuse_prior_tasks(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        services = Services()
        first = run(ledger, plan, services)
        data = plan.model_dump(mode="json")
        data["review"]["max_model_turns"] = 2
        changed = FeaturePlan.model_validate_json(json.dumps(data))
        second = run(ledger, changed, services)
        assert first.tasks[0] != second.tasks[0]
        assert len(services.model_calls) == 4


def test_direct_consumer_reuse_rechecks_provider_finding(tmp_path):
    from gflo.controller import Controller

    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        services = Services()
        result = run(ledger, plan, services)
        provider, consumer = [
            PreparedTask.model_validate_json(ledger.artifacts.read(d)) for d in result.tasks
        ]
        state = ledger.status(provider.run.atom.atom_id)
        ledger.record_finding(
            AcceptanceFinding(
                atom_id=provider.run.atom.atom_id,
                contract_digest=provider.run.atom.digest(),
                candidate_digest=state["candidate_digest"],
                evidence_digest=ledger.artifacts.publish(b"new contradiction"),
                reason="Late finding",
            )
        )
        controller = Controller(
            ledger,
            services.model(ledger.artifacts, plan.review.model_profile),
            services.broker(ledger.artifacts, consumer.run.broker_image),
        )
        with pytest.raises(Conflict, match="finding|contradict"):
            controller.run(consumer.run.atom.atom_id)


def test_finding_during_consumer_blocks_acceptance(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        services = Services()

        def finding():
            if len(services.model_calls) != 2:
                return
            provider = services.model_calls[0][0]
            state = ledger.status(provider.atom_id)
            ledger.record_finding(
                AcceptanceFinding(
                    atom_id=provider.atom_id,
                    contract_digest=provider.digest(),
                    candidate_digest=state["candidate_digest"],
                    evidence_digest=ledger.artifacts.publish(b"concurrent contradiction"),
                    reason="Finding",
                )
            )

        services.after_model = finding
        with pytest.raises(Conflict, match="finding|contradict"):
            run(ledger, plan, services)
        consumer = services.model_calls[1][0]
        assert ledger.status(consumer.atom_id)["status"] != "accepted"


def test_interrupted_final_validation_resumes_without_model_work(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        services = Services()
        services.interrupt = True
        services.interrupt_at = 5
        with pytest.raises(KeyboardInterrupt):
            run(ledger, plan, services)
        services.interrupt = False
        result = run(ledger, plan, services)
        assert result.status == "accepted"
        assert len(services.model_calls) == 2
        assert result.integration_selection.whole_repository is False


def test_snapshot_worker_provenance_does_not_enable_arbitrary_dependencies(tmp_path):
    from gflo.records import WorkAtom
    from gflo.worker import compose_view

    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = feature(ledger)
        services = Services()
        result = run(ledger, plan, services)
        consumer = PreparedTask.model_validate_json(ledger.artifacts.read(result.tasks[1]))
        data = consumer.run.atom.model_dump(mode="json")
        data["dependency_artifacts"] = [ledger.artifacts.publish(b"{}")]
        atom = WorkAtom.model_validate_json(json.dumps(data))
        with pytest.raises(ValueError):
            compose_view(ledger.artifacts, atom, consumer.run.source.digest())
        data = consumer.run.atom.model_dump(mode="json")
        data["capability_profile"] = "python-pilot-v1"
        atom = WorkAtom.model_validate_json(json.dumps(data))
        with pytest.raises(ValueError, match="self-contained"):
            compose_view(ledger.artifacts, atom, consumer.run.source.digest())


def test_feature_cli_executes_the_reviewed_graph(tmp_path, monkeypatch, capsys):
    from gflo.cli import main

    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        plan = feature(ledger)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(plan.canonical())
    services = Services()
    monkeypatch.setattr(
        "gflo.cli.run_feature", lambda ledger, plan, current: run(ledger, plan, services, current)
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "gflo",
            "--db",
            str(path),
            "run-feature",
            str(plan_path),
            "--current",
            plan.request.source.artifact_digest,
        ],
    )
    assert main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "accepted"
    assert len(result["tasks"]) == 2
    assert result["integration_selection"]["whole_repository"] is False
