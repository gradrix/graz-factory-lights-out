"""Durable loop integration using real SQLite/artifacts and deterministic external doubles."""

import base64
import json
import sqlite3
from pathlib import Path

import pytest

from gflo.broker import Execution, SourceBundle
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.gates import ProcessCase, ProcessGate
from gflo.ledger import Conflict, WorkLedger
from gflo.model import ModelError, ModelProfile, ModelTurn
from gflo.records import WorkAtom
from gflo.worker import CandidateResult, InputSnapshot, ReadFileRequest


@pytest.fixture
def plan():
    source = SourceBundle(files={"main.py": "print(0)", "helper.py": "ANSWER=42"})
    gate = ProcessGate(cases=(ProcessCase(command=("python", "main.py"), expected_stdout="42\n"),))
    fields = json.loads((Path(__file__).parents[1] / "examples/work-atom.json").read_text())
    fields.update(
        writable_paths=["main.py"],
        prohibited_paths=[],
        max_attempts=2,
        required_gates=[{"gate_id": "behavior", "validator_digest": gate.digest()}],
    )
    fields["inputs_digest"] = InputSnapshot(
        source_digest=source.digest(), source_revision=fields["source_revision"]
    ).digest()
    import hashlib

    return RunPlan(
        atom=WorkAtom.model_validate_json(json.dumps(fields)),
        source=source,
        gates={"behavior": gate},
        deployment="fixture deployment",
        model_profile=ModelProfile(
            base_url="http://127.0.0.1:30000/v1",
            model="gflo-local",
            deployment_digest=hashlib.sha256(b"fixture deployment").hexdigest(),
        ),
        broker_image="sha256:" + "a" * 64,
        selected_paths=("main.py",),
    )


class FakeModel:
    def __init__(self, ledger, plan, actions=None):
        self.artifacts = ledger.artifacts
        self.profile = plan.model_profile
        self.ledger = ledger
        self.actions = list(
            actions or [CandidateResult(kind="candidate", changes={"main.py": "print(42)"})]
        )
        self.last_evidence_digest = None
        self.calls = []

    def turn(self, atom, source_digest, **kwargs):
        assert not self.ledger._db.in_transaction
        self.calls.append(kwargs)
        self.last_evidence_digest = self.artifacts.publish(
            json.dumps({"model-call": len(self.calls)}).encode()
        )
        action = self.actions.pop(0) if len(self.actions) > 1 else self.actions[0]
        if isinstance(action, BaseException):
            raise action
        return ModelTurn(
            manifest_digest=self.last_evidence_digest,
            response_digest=self.last_evidence_digest,
            result=action,
            prompt_tokens=100,
            completion_tokens=20,
            elapsed_seconds=0.1,
        )


class FakeBroker:
    def __init__(self, ledger, plan):
        self.ledger = ledger
        self.artifacts = ledger.artifacts
        self.image = plan.broker_image
        self.image_id = plan.broker_image
        self.qualification_digest = None
        self.calls = 0
        self.interrupt_at = None
        self.reconciliations = 0

    def reconcile(self):
        assert not self.ledger._db.in_transaction
        self.reconciliations += 1

    def qualify(self):
        assert not self.ledger._db.in_transaction
        self.qualification_digest = self.artifacts.publish(b"deterministic qualification double")

    def execute(self, digest, command, stdin, seconds, purpose):
        assert not self.ledger._db.in_transaction
        self.calls += 1
        if self.calls == self.interrupt_at:
            raise KeyboardInterrupt()
        source = SourceBundle.model_validate_json(self.artifacts.read(digest))
        output = b"42\n" if source.files["main.py"] == "print(42)" else b"0\n"
        return Execution(
            candidate_digest=digest,
            image_id=self.image,
            container_id=f"fake-{self.calls}",
            command=command,
            stdin=stdin,
            purpose=purpose,
            outcome="completed",
            exit_code=0,
            oom_killed=False,
            stdout_base64=base64.b64encode(output).decode(),
            stderr_base64="",
            elapsed_seconds=0.1,
        )


def setup(ledger, plan, actions=None):
    prepare_run(ledger, plan)
    model, broker = FakeModel(ledger, plan, actions), FakeBroker(ledger, plan)
    return Controller(ledger, model, broker), model, broker


def test_success_and_repeated_resume_do_not_repeat_work(tmp_path, plan):
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan)
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "accepted"
        assert len(model.calls) == 1 and broker.calls == 2
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan)
        assert controller.run(plan.atom.atom_id)["status"] == "accepted"
        assert model.calls == [] and broker.calls == 0
        assert ledger.audit_artifacts().missing == ()


def test_failure_diagnostic_drives_new_attempt(tmp_path, plan):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        bad = CandidateResult(kind="candidate", changes={"main.py": "print(0)"})
        good = CandidateResult(kind="candidate", changes={"main.py": "print(42)"})
        controller, model, broker = setup(ledger, plan, [bad, good])
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "accepted"
        assert len(result["attempts"]) == 2
        assert result["attempts"][0]["gate_receipts"][0]["outcome"] == "fail"
        diagnostic = model.calls[1]["diagnostic_digests"][0]
        assert "expected_stdout" not in ledger.artifacts.read(diagnostic).decode()
        assert result["attempts"][1]["retry_plan"]["new_evidence"] == diagnostic


def test_budget_exhaustion_quarantines_preserving_both_failures(tmp_path, plan):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(
            ledger, plan, [CandidateResult(kind="candidate", changes={"main.py": "print(0)"})]
        )
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "quarantined"
        assert len(model.calls) == 2
        assert all(a["events"][-1]["kind"] == "failed" for a in result["attempts"])
        assert all(a["gate_receipts"][0]["outcome"] == "fail" for a in result["attempts"])


def test_read_request_expands_a_fresh_view(tmp_path, plan):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(
            ledger,
            plan,
            [
                ReadFileRequest(kind="read_file", path="helper.py"),
                CandidateResult(kind="candidate", changes={"main.py": "print(42)"}),
            ],
        )
        assert controller.run(plan.atom.atom_id)["status"] == "accepted"
        assert model.calls[0]["selected_paths"] == ("main.py",)
        assert model.calls[1]["selected_paths"] == ("helper.py", "main.py")
        assert broker.calls == 2


def test_interrupted_generation_restarts_with_fenced_attempt(tmp_path, plan):
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan, [KeyboardInterrupt()])
        with pytest.raises(KeyboardInterrupt):
            controller.run(plan.atom.atom_id)
        old = ledger.active_lease(plan.atom.atom_id)
        assert ledger.status(plan.atom.atom_id)["status"] == "running"
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan)
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "accepted" and len(result["attempts"]) == 2
        with pytest.raises(Conflict):
            ledger.start(old)
        assert model.calls[0]["diagnostic_digests"]


def test_resume_validation_reuses_receipts_not_model(tmp_path, plan):
    fields = plan.model_dump(mode="json")
    fields["gates"]["second"] = fields["gates"]["behavior"]
    fields["atom"]["required_gates"].append(
        {"gate_id": "second", "validator_digest": plan.gates["behavior"].digest()}
    )
    plan = RunPlan.model_validate_json(json.dumps(fields))
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(ledger, plan)
        broker.interrupt_at = 3
        with pytest.raises(KeyboardInterrupt):
            controller.run(plan.atom.atom_id)
        assert ledger.status(plan.atom.atom_id)["status"] == "validating"
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "accepted" and len(result["attempts"]) == 1
        assert len(model.calls) == 1 and broker.calls == 4


def test_infrastructure_failure_halts_without_automatic_semantic_retry(tmp_path, plan):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(ledger, plan, [ModelError("server unavailable")])
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "retry-ready"
        assert len(model.calls) == 1 and broker.calls == 0
        assert result["attempts"][0]["events"][-1]["kind"] == "failed"


def test_run_plan_is_immutable(tmp_path, plan):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        prepare_run(ledger, plan)
        changed = RunPlan.model_validate_json(
            json.dumps(plan.model_dump(mode="json") | {"max_model_turns": 4})
        )
        with pytest.raises(Conflict, match="immutable"):
            prepare_run(ledger, changed)
        assert RunPlan.model_validate_json(ledger.run_plan(plan.atom.atom_id)) == plan


def test_version_one_migration_preserves_contract(tmp_path, plan):
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        ledger.submit(plan.atom)
    db = sqlite3.connect(path)
    try:
        db.execute("DROP TABLE run_plans")
        db.execute("PRAGMA user_version=1")
    finally:
        db.close()
    with WorkLedger(path) as ledger:
        assert ledger.status(plan.atom.atom_id)["contract"] == plan.atom.model_dump(mode="json")
        assert ledger._db.execute("PRAGMA user_version").fetchone()[0] == 2
        prepare_run(ledger, plan)
        with pytest.raises(sqlite3.IntegrityError):
            ledger._db.execute("DELETE FROM run_plans")


@pytest.mark.parametrize("window", ["model", "after-accept"])
def test_process_death_and_resume_without_duplicate_acceptance(tmp_path, plan, window):
    import subprocess
    import sys

    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        prepare_run(ledger, plan)
    code = """
import os, sys
sys.path.insert(0, sys.argv[3])
from test_controller import FakeModel, FakeBroker
from gflo.controller import RunPlan, Controller
from gflo.ledger import WorkLedger
with WorkLedger(sys.argv[1]) as ledger:
    plan = RunPlan.model_validate_json(ledger.run_plan(sys.argv[2]))
    model, broker = FakeModel(ledger, plan), FakeBroker(ledger, plan)
    if sys.argv[4] == "model":
        model.turn = lambda *a, **k: os._exit(23)
    else:
        accept = ledger.accept
        def crash(*a, **k):
            accept(*a, **k)
            os._exit(23)
        ledger.accept = crash
    Controller(ledger, model, broker).run(plan.atom.atom_id)
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(path),
            plan.atom.atom_id,
            str(Path(__file__).parent),
            window,
        ],
        timeout=15,
    )
    assert result.returncode == 23
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan)
        snapshot = controller.run(plan.atom.atom_id)
        assert snapshot["status"] == "accepted"
        assert sum(e["kind"] == "accepted" for a in snapshot["attempts"] for e in a["events"]) == 1
        assert len(model.calls) == (1 if window == "model" else 0)


def test_cli_submit_run_then_status_and_run(tmp_path, plan, monkeypatch, capsys):
    from gflo import cli

    path = tmp_path / "ledger.db"
    manifest = tmp_path / "run.json"
    manifest.write_text(plan.model_dump_json())
    prefix = ["gflo", "--db", str(path)]
    monkeypatch.setattr("sys.argv", prefix + ["submit-run", str(manifest)])
    assert cli.main() == 0
    assert json.loads(capsys.readouterr().out)["atom_id"] == plan.atom.atom_id
    # Actual CLI/controller/ledger path; deterministic external-operation doubles.
    with WorkLedger(path) as external:
        monkeypatch.setattr(cli, "LocalModel", lambda store, profile: FakeModel(external, plan))
        monkeypatch.setattr(cli, "DockerBroker", lambda store, image: FakeBroker(external, plan))
        monkeypatch.setattr("sys.argv", prefix + ["run", plan.atom.atom_id])
        assert cli.main() == 0
        assert json.loads(capsys.readouterr().out)["status"] == "accepted"
        monkeypatch.setattr("sys.argv", prefix + ["resume", plan.atom.atom_id])
        assert cli.main() == 0
        assert json.loads(capsys.readouterr().out)["status"] == "accepted"


def test_resume_after_retry_claim_preserves_its_diagnostic(tmp_path, plan):
    from gflo.controller import OWNER

    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(ledger, plan)
        lease = ledger.claim(plan.atom.atom_id, OWNER)
        ledger.start(lease)
        controller._failure(lease, "Retained compiler observation", {"error": "fixture"})
        retry = controller._retry(ledger.status(plan.atom.atom_id))
        ledger.claim(plan.atom.atom_id, OWNER, retry=retry)
        assert controller.run(plan.atom.atom_id)["status"] == "accepted"
        assert model.calls[0]["diagnostic_digests"] == (retry.new_evidence,)


def test_repeated_tool_requests_are_bounded(tmp_path, plan):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(
            ledger, plan, [ReadFileRequest(kind="read_file", path="helper.py")]
        )
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "quarantined"
        assert len(model.calls) == 4 and broker.calls == 0


def test_expired_attempt_reconciles_into_bounded_retry(tmp_path, plan):
    from gflo.controller import OWNER

    now = [1000.0]
    with WorkLedger(tmp_path / "ledger.db", clock=lambda: now[0]) as ledger:
        controller, model, broker = setup(ledger, plan)
        ledger.claim(plan.atom.atom_id, OWNER, lease_seconds=1)
        now[0] = 1002.0
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "accepted"
        assert result["attempts"][0]["events"][-1]["kind"] == "expired"
        assert model.calls[0]["diagnostic_digests"]


@pytest.mark.parametrize("interrupted", [False, True])
def test_low_disk_resume_preserves_attempt_until_space_recovers(
    tmp_path, plan, monkeypatch, interrupted
):
    import shutil

    from gflo.storage import StoragePressure

    with WorkLedger(tmp_path / "ledger.db") as ledger:
        prepare_run(ledger, plan)
        model = FakeModel(ledger, plan)
        broker = FakeBroker(ledger, plan)
        controller = Controller(ledger, model, broker)
        ledger.artifacts.reserve_bytes = 100
        if interrupted:
            from gflo.controller import OWNER

            lease = ledger.claim(plan.atom.atom_id, OWNER)
            ledger.start(lease)
        before = ledger.status(plan.atom.atom_id)
        usage = shutil.disk_usage(tmp_path)
        with monkeypatch.context() as patch:
            patch.setattr(shutil, "disk_usage", lambda path: usage._replace(free=99))
            with pytest.raises(StoragePressure):
                controller.run(plan.atom.atom_id)
        assert ledger.status(plan.atom.atom_id) == before
        assert not model.calls
        assert controller.run(plan.atom.atom_id)["status"] == "accepted"


def test_history_keeps_failed_diffs_and_compares_each_attempt_to_original(tmp_path, plan):
    from gflo.artifacts import ArtifactError
    from gflo.history import change_history, render_history

    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(
            ledger,
            plan,
            [
                CandidateResult(kind="candidate", changes={"main.py": "print(1)"}),
                CandidateResult(kind="candidate", changes={"main.py": "print(42)"}),
            ],
        )
        state = controller.run(plan.atom.atom_id)
        calls = (len(model.calls), broker.calls)
        history = change_history(ledger, plan.atom.atom_id)
        first, second = history["attempts"]
        assert first["outcome"] == "failed" and second["outcome"] == "accepted"
        assert "-print(0)" in first["candidates"][0]["changes"][0]["diff"]
        assert "+print(1)" in first["candidates"][0]["changes"][0]["diff"]
        patch = second["candidates"][0]["changes"][0]["diff"]
        assert "-print(0)" in patch and "+print(42)" in patch
        assert "No newline at end of file" in patch
        assert history["accepted_candidate_digest"] == second["candidates"][0]["digest"]
        assert "Gate behavior: fail" in render_history(history)
        assert change_history(ledger, plan.atom.atom_id) == history
        assert ledger.status(plan.atom.atom_id) == state
        assert (len(model.calls), broker.calls) == calls
        old = ledger.artifacts.root / first["candidates"][0]["digest"]
        old.chmod(0o600)
        old.write_bytes(b"corrupt failed candidate")
        with pytest.raises(ArtifactError, match="Corrupt"):
            change_history(ledger, plan.atom.atom_id)


def test_history_without_candidate_does_not_invent_changes(tmp_path, plan):
    from gflo.history import change_history, render_history

    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, _, _ = setup(ledger, plan, [ModelError("server unavailable")])
        controller.run(plan.atom.atom_id)
        history = change_history(ledger, plan.atom.atom_id)
        assert history["accepted_candidate_digest"] is None
        assert history["attempts"][0]["candidates"] == []
        assert "No published candidate." in render_history(history)
        history["objective"] = "untrusted\x1b[2J"
        assert "\x1b" not in render_history(history)


@pytest.mark.parametrize("window", ["before_commit", "after_commit", "before_commit_full"])
def test_acceptance_commit_failure_resumes_without_duplicate_work(tmp_path, plan, window):
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan)
        connection = ledger._db

        class CommitFault:
            fired = False

            def __getattr__(self, name):
                return getattr(connection, name)

            def execute(self, sql, *args):
                if (
                    sql == "COMMIT"
                    and not self.fired
                    and connection.execute("SELECT count(*) FROM acceptances").fetchone()[0]
                ):
                    self.fired = True
                    if window == "after_commit":
                        connection.execute(sql, *args)
                    error = sqlite3.OperationalError("injected acceptance commit failure")
                    if window == "before_commit_full":
                        connection.execute("ROLLBACK")
                        error.sqlite_errorcode = sqlite3.SQLITE_FULL
                        error.sqlite_errorname = "SQLITE_FULL"
                    raise error
                return connection.execute(sql, *args)

        fault = CommitFault()
        ledger._db = fault
        try:
            with pytest.raises(sqlite3.OperationalError, match="injected acceptance commit"):
                controller.run(plan.atom.atom_id)
            assert fault.fired
        finally:
            ledger._db = connection
        status = ledger.status(plan.atom.atom_id)
        assert status["status"] == ("accepted" if window == "after_commit" else "validating")
        assert len(model.calls) == 1
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan)
        accepted = controller.run(plan.atom.atom_id)
        assert accepted["status"] == "accepted"
        assert not model.calls and broker.calls == 0
        assert controller.run(plan.atom.atom_id) == accepted
        assert ledger._db.execute("SELECT count(*) FROM acceptances").fetchone()[0] == 1
        assert (
            len(
                [
                    event
                    for event in accepted["attempts"][0]["events"]
                    if event["kind"] == "accepted"
                ]
            )
            == 1
        )


@pytest.mark.parametrize(
    "window", ["lookup", "tokenize", "generation", "between_turns", "persistent"]
)
def test_model_failure_windows_preserve_evidence_and_bounded_resume(tmp_path, plan, window):
    from gflo.model import LocalModel
    from gflo.reporting import cost_report

    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        prepare_run(ledger, plan)

        class ProtocolModel(LocalModel):
            failing = True
            generations = 0

            def _request(self, route, payload, deadline, exchanges):
                fail_at = {
                    "lookup": "/v1/models",
                    "tokenize": "/tokenize",
                    "generation": "/v1/chat/completions",
                    "persistent": "/v1/models",
                }
                failing = self.failing and (
                    route == fail_at.get(window)
                    or (window == "between_turns" and self.generations == 1)
                )
                exchange = {
                    "path": route,
                    "request_digest": self.artifacts.publish(json.dumps(payload).encode()),
                }
                exchanges.append(exchange)
                if failing:
                    raise ModelError("injected endpoint loss at " + route)
                if route == "/v1/models":
                    response = {"data": [{"id": "gflo-local"}]}
                elif route == "/tokenize":
                    response = {"count": 100, "max_model_len": 16384}
                else:
                    self.generations += 1
                    content = (
                        {"kind": "read_file", "path": "helper.py"}
                        if window == "between_turns" and self.generations == 1
                        else {"kind": "candidate", "changes": {"main.py": "print(42)"}}
                    )
                    response = {
                        "model": "gflo-local",
                        "choices": [
                            {
                                "finish_reason": "stop",
                                "message": {"role": "assistant", "content": json.dumps(content)},
                            }
                        ],
                        "usage": {
                            "prompt_tokens": 100,
                            "completion_tokens": 20,
                            "total_tokens": 120,
                        },
                    }
                exchange["response_digest"] = self.artifacts.publish(json.dumps(response).encode())
                return response

        model = ProtocolModel(ledger.artifacts, plan.model_profile)
        broker = FakeBroker(ledger, plan)
        controller = Controller(ledger, model, broker)
        failed = controller.run(plan.atom.atom_id)
        assert failed["status"] == "retry-ready" and broker.calls == 0
        assert failed["candidate_digest"] is None
        assert (
            cost_report(ledger, plan.atom.atom_id)["totals"]["observations_without_validated_usage"]
            == 1
        )
        old = ledger.active_lease(plan.atom.atom_id)
        model.failing = window == "persistent"
        recovered = controller.run(plan.atom.atom_id)
        assert recovered["attempts"][0] == failed["attempts"][0]
        assert len(recovered["attempts"]) == 2
        assert recovered["status"] == ("quarantined" if window == "persistent" else "accepted")
        with pytest.raises(Conflict):
            ledger.start(old)
        assert controller.run(plan.atom.atom_id) == recovered
        assert not ledger.audit_artifacts().missing
        assert not ledger.audit_artifacts().corrupt


@pytest.mark.parametrize(
    "window", ["before_launch", "during_case", "between_cases", "before_receipt", "after_receipt"]
)
def test_gate_interruption_windows_resume_without_false_acceptance(
    tmp_path, plan, window, monkeypatch
):
    fields = plan.model_dump(mode="json")
    gate = ProcessGate(cases=plan.gates["behavior"].cases * 2)
    fields["gates"]["behavior"] = gate.model_dump(mode="json")
    fields["atom"]["required_gates"][0]["validator_digest"] = gate.digest()
    plan = RunPlan.model_validate_json(json.dumps(fields))
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan)
        execute, record = broker.execute, ledger.record_gate
        fired = False

        def interrupted_execute(*args, **kwargs):
            nonlocal fired
            # Call 1 is candidate smoke; calls 2 and 3 are mandatory gate cases.
            target = 3 if window == "between_cases" else 2
            if (
                not fired
                and window in ("before_launch", "during_case", "between_cases")
                and broker.calls + 1 == target
            ):
                fired = True
                if window == "during_case":
                    execute(*args, **kwargs)
                raise KeyboardInterrupt()
            return execute(*args, **kwargs)

        def interrupted_record(*args, **kwargs):
            nonlocal fired
            if not fired and window in ("before_receipt", "after_receipt"):
                fired = True
                if window == "after_receipt":
                    record(*args, **kwargs)
                raise KeyboardInterrupt()
            return record(*args, **kwargs)

        with monkeypatch.context() as patch:
            patch.setattr(broker, "execute", interrupted_execute)
            patch.setattr(ledger, "record_gate", interrupted_record)
            with pytest.raises(KeyboardInterrupt):
                controller.run(plan.atom.atom_id)
        assert fired
        interrupted = ledger.status(plan.atom.atom_id)
        assert interrupted["status"] == "validating"
        assert ledger._db.execute("SELECT count(*) FROM acceptances").fetchone()[0] == 0
    with WorkLedger(path) as ledger:
        controller, model, broker = setup(ledger, plan)
        recovered = controller.run(plan.atom.atom_id)
        assert recovered["status"] == "accepted" and len(recovered["attempts"]) == 1
        assert not model.calls
        assert broker.calls == (0 if window == "after_receipt" else 2)
        assert controller.run(plan.atom.atom_id) == recovered
        assert ledger._db.execute("SELECT count(*) FROM acceptances").fetchone()[0] == 1


def test_later_mandatory_case_cannot_be_skipped_by_earlier_success(tmp_path, plan):
    fields = plan.model_dump(mode="json")
    gate = ProcessGate(
        cases=(
            plan.gates["behavior"].cases[0],
            ProcessCase(command=("python", "main.py"), expected_stdout="different\n"),
        )
    )
    fields["gates"]["behavior"] = gate.model_dump(mode="json")
    fields["atom"]["required_gates"][0]["validator_digest"] = gate.digest()
    plan = RunPlan.model_validate_json(json.dumps(fields))
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, _, broker = setup(ledger, plan)
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "quarantined"
        assert broker.calls == 6  # smoke plus both mandatory cases, on both Attempts
        for attempt in result["attempts"]:
            receipt = attempt["gate_receipts"][0]
            assert receipt["outcome"] == "fail"
            report = json.loads(ledger.artifacts.read(receipt["evidence_digest"]))
            assert len(report["executions"]) == 2
        assert ledger._db.execute("SELECT count(*) FROM acceptances").fetchone()[0] == 0


@pytest.mark.parametrize("cases", [[], [{}]])
def test_empty_or_malformed_gate_plan_cannot_bind_a_run(tmp_path, plan, cases):
    from pydantic import ValidationError

    fields = plan.model_dump(mode="json")
    fields["gates"]["behavior"]["cases"] = cases
    with pytest.raises(ValidationError):
        RunPlan.model_validate_json(json.dumps(fields))


@pytest.mark.parametrize("fault", ["wrong-candidate", "malformed", "reused-container"])
def test_invalid_evaluator_report_halts_and_recovers_with_new_evidence(tmp_path, plan, fault):
    fields = plan.model_dump(mode="json")
    gate = ProcessGate(cases=plan.gates["behavior"].cases * 2)
    fields["gates"]["behavior"] = gate.model_dump(mode="json")
    fields["atom"]["required_gates"][0]["validator_digest"] = gate.digest()
    plan = RunPlan.model_validate_json(json.dumps(fields))
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(ledger, plan)
        execute = broker.execute
        reported_container = None

        def invalid(*args, **kwargs):
            nonlocal reported_container
            result = execute(*args, **kwargs)
            if kwargs["purpose"] != "validation":
                return result
            if fault == "malformed":
                return None
            if fault == "wrong-candidate":
                return result.model_copy(update={"candidate_digest": "b" * 64})
            reported_container = reported_container or result.container_id
            return result.model_copy(update={"container_id": reported_container})

        broker.execute = invalid
        failed = controller.run(plan.atom.atom_id)
        assert failed["status"] == "retry-ready"
        assert len(model.calls) == 1
        assert failed["attempts"][0]["gate_receipts"][0]["outcome"] == "inconclusive"
        assert ledger._db.execute("SELECT count(*) FROM acceptances").fetchone()[0] == 0
        broker.execute = execute
        accepted = controller.run(plan.atom.atom_id)
        assert accepted["status"] == "accepted" and len(accepted["attempts"]) == 2
        assert accepted["attempts"][0] == failed["attempts"][0]
        assert model.calls[-1]["diagnostic_digests"]
        assert controller.run(plan.atom.atom_id) == accepted
        assert ledger._db.execute("SELECT count(*) FROM acceptances").fetchone()[0] == 1


def escalating(plan, profile_id="vllm-python-worker-escalating-v1", **changes):
    fields = plan.model_dump(mode="json")
    fields["model_profile"]["profile_id"] = profile_id
    fields["max_model_turns"] = 3 if profile_id == "vllm-python-worker-escalating-tools-v1" else 1
    fields["atom"]["max_attempts"] = 2
    fields["atom"]["context_budget"] = {"total_tokens": 8192, "output_tokens": 4096}
    for key, value in changes.items():
        if key == "max_model_turns":
            fields[key] = value
        elif key in ("total_tokens", "output_tokens"):
            fields["atom"]["context_budget"][key] = value
        else:
            fields["atom"][key] = value
    return RunPlan.model_validate_json(json.dumps(fields))


@pytest.mark.parametrize(
    "changes",
    [
        {"max_attempts": 3},
        {"max_model_turns": 2},
        {"total_tokens": 16384},
        {"output_tokens": 2048},
    ],
)
def test_escalation_rejects_unbounded_or_ambiguous_schedule(plan, changes):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        escalating(plan, **changes)


def test_escalation_resume_keeps_aggregate_attempt_allowance(tmp_path, plan):
    plan = escalating(plan)
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(ledger, plan, [ModelError("service stopped")])
        assert controller.run(plan.atom.atom_id)["status"] == "retry-ready"
        assert len(model.calls) == 1
        model.actions = [CandidateResult(kind="candidate", changes={"main.py": "print(0)"})]
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "quarantined"
        assert len(result["attempts"]) == 2
        assert model.calls[0]["diagnostic_digests"] == ()
        assert model.calls[1]["diagnostic_digests"]
        controller.run(plan.atom.atom_id)
        assert len(model.calls) == 2


def test_failed_escalation_cannot_change_profile_in_place(tmp_path, plan):
    plan = escalating(plan)
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(ledger, plan, [ModelError("offline")])
        assert controller.run(plan.atom.atom_id)["status"] == "retry-ready"
        changed = escalating(plan, profile_id="vllm-python-worker-escalating-low-v1")
        with pytest.raises(Conflict, match="immutable"):
            prepare_run(ledger, changed)
        assert RunPlan.model_validate_json(ledger.run_plan(plan.atom.atom_id)) == plan
        assert len(ledger.status(plan.atom.atom_id)["attempts"]) == 1


def test_tool_escalation_can_read_then_edit_in_one_attempt(tmp_path, plan):
    plan = escalating(plan, profile_id="vllm-python-worker-escalating-tools-v1")
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(
            ledger,
            plan,
            [
                ReadFileRequest(kind="read_file", path="helper.py"),
                CandidateResult(kind="candidate", changes={"main.py": "print(42)"}),
            ],
        )
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "accepted"
        assert len(result["attempts"]) == 1 and len(model.calls) == 2
        assert model.calls[1]["selected_paths"] == ("helper.py", "main.py")
        assert all(call["diagnostic_digests"] == () for call in model.calls)
        controller.run(plan.atom.atom_id)
        assert len(model.calls) == 2


def test_tool_escalation_cannot_exceed_six_turns(tmp_path, plan):
    fields = plan.model_dump(mode="json")
    fields["source"]["files"].update({"x.py": "X=1", "y.py": "Y=2"})
    source = SourceBundle.model_validate_json(json.dumps(fields["source"]))
    fields["atom"]["inputs_digest"] = InputSnapshot(
        source_digest=source.digest(), source_revision=plan.atom.source_revision
    ).digest()
    plan = escalating(
        RunPlan.model_validate_json(json.dumps(fields)),
        profile_id="vllm-python-worker-escalating-tools-v1",
    )
    actions = [
        ReadFileRequest(kind="read_file", path=p)
        for p in ("helper.py", "x.py", "y.py", "helper.py", "x.py", "y.py")
    ]
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(ledger, plan, actions)
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "quarantined"
        assert len(result["attempts"]) == 2 and len(model.calls) == 6
        controller.run(plan.atom.atom_id)
        assert len(model.calls) == 6


def test_remaining_turn_budget_counts_down_and_resets_after_failure(tmp_path, plan):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        bad = CandidateResult(kind="candidate", changes={"main.py": "print(0)"})
        good = CandidateResult(kind="candidate", changes={"main.py": "print(42)"})
        controller, model, _ = setup(
            ledger,
            plan,
            [
                ReadFileRequest(kind="read_file", path="helper.py"),
                bad,
                good,
            ],
        )
        assert controller.run(plan.atom.atom_id)["status"] == "accepted"
        assert [call["remaining_model_turns"] for call in model.calls] == [3, 2, 3]


def test_development_failure_repairs_within_attempt_and_still_runs_final_gate(tmp_path, plan):
    plan = plan.model_copy(
        update={
            "model_profile": plan.model_profile.model_copy(
                update={"profile_id": "vllm-python-worker-repair-v1"}
            )
        }
    )
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        bad = CandidateResult(kind="candidate", changes={"main.py": "print(1)"})
        good = CandidateResult(kind="candidate", changes={"main.py": "print(42)"})
        controller, model, broker = setup(ledger, plan, [bad, good])
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "accepted" and len(result["attempts"]) == 1
        assert broker.calls == 4  # two development checks, smoke, independent gate
        assert model.calls[1]["diagnostic_digests"]
        draft = SourceBundle.model_validate_json(
            ledger.artifacts.read(model.calls[1]["draft_digest"])
        )
        assert draft.files["main.py"] == "print(1)"
        assert len(result["attempts"][0]["gate_receipts"]) == 1
        assert ledger.audit_artifacts().missing == ()


def test_development_pass_cannot_replace_independent_acceptance(tmp_path, plan):
    from gflo.escalation import review_handoff

    plan = plan.model_copy(
        update={
            "model_profile": plan.model_profile.model_copy(
                update={"profile_id": "vllm-python-worker-repair-v1"}
            )
        }
    )
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(ledger, plan)
        original = broker.execute

        def execute(*args, **kwargs):
            result = original(*args, **kwargs)
            if result.purpose == "validation":
                return result.model_copy(
                    update={"stdout_base64": base64.b64encode(b"wrong").decode()}
                )
            return result

        broker.execute = execute
        result = controller.run(plan.atom.atom_id)
        assert result["status"] == "quarantined"
        assert all(a["gate_receipts"][0]["outcome"] == "fail" for a in result["attempts"])
        packet = review_handoff(ledger, plan.atom.atom_id)
        assert packet["status"] == "needs-review"
        assert packet["latest_unaccepted_draft"]["files"]["main.py"] == "print(42)"
        assert packet["diagnostics"]
        assert ledger.status(plan.atom.atom_id)["status"] == "quarantined"
        assert model.calls[1]["draft_digest"] == packet["latest_unaccepted_draft_digest"]


def test_repair_profile_retains_draft_after_interrupted_check(tmp_path, plan):
    plan = plan.model_copy(
        update={
            "model_profile": plan.model_profile.model_copy(
                update={"profile_id": "vllm-python-worker-repair-v1"}
            )
        }
    )
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(ledger, plan)
        broker.interrupt_at = 1
        with pytest.raises(KeyboardInterrupt):
            controller.run(plan.atom.atom_id)
        assert ledger.status(plan.atom.atom_id)["status"] == "running"
        broker.interrupt_at = None
        assert controller.run(plan.atom.atom_id)["status"] == "accepted"
        retained = SourceBundle.model_validate_json(
            ledger.artifacts.read(model.calls[1]["draft_digest"])
        )
        assert retained.files["main.py"] == "print(42)"
        assert len(ledger.status(plan.atom.atom_id)["attempts"]) == 2


def test_audit_detects_missing_unsubmitted_development_draft(tmp_path, plan):
    plan = plan.model_copy(
        update={
            "model_profile": plan.model_profile.model_copy(
                update={"profile_id": "vllm-python-worker-repair-v1"}
            )
        }
    )
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        controller, model, broker = setup(ledger, plan)
        broker.interrupt_at = 1
        with pytest.raises(KeyboardInterrupt):
            controller.run(plan.atom.atom_id)
        events = ledger.status(plan.atom.atom_id)["attempts"][0]["events"]
        event = next(
            e
            for e in events
            if e["kind"] == "observation" and e["details"]["kind"] == "development"
        )
        draft = json.loads(ledger.artifacts.read(event["details"]["digest"]))["draft_digest"]
        (ledger.artifacts.root / draft).unlink()
        assert draft in ledger.audit_artifacts().missing
