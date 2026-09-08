"""Real SQLite/CLI tests for durable recovery and acceptance integrity."""

import hashlib
import json
import sqlite3
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from pydantic import ValidationError

from gflo.ledger import Conflict, WorkLedger
from gflo.records import GateEvidence, Lease, RetryPlan, WorkAtom

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = hashlib.sha256(b"candidate").hexdigest()
EVIDENCE = hashlib.sha256(b"evidence").hexdigest()


@pytest.fixture
def atom():
    return WorkAtom.model_validate_json((ROOT / "examples/work-atom.json").read_bytes())


@pytest.fixture
def clock():
    return [1000.0]


@pytest.fixture
def ledger(tmp_path, clock):
    with WorkLedger(tmp_path / "ledger.db", clock=lambda: clock[0]) as value:
        yield value


def validating(ledger, atom):
    ledger.submit(atom)
    lease = ledger.claim(atom.atom_id, "controller")
    ledger.start(lease)
    ledger.artifacts.publish(b"candidate")
    ledger.artifacts.publish(b"evidence")
    ledger.candidate(lease, CANDIDATE)
    return lease


def receipt(atom, lease, gate, **changes):
    fields = dict(
        attempt_id=lease.attempt_id,
        contract_digest=atom.digest(),
        inputs_digest=atom.inputs_digest,
        candidate_digest=CANDIDATE,
        gate_id=gate.gate_id,
        validator_digest=gate.validator_digest,
        outcome="pass",
        evidence_digest=EVIDENCE,
        runner_id="trusted-runner-v1",
    )
    return GateEvidence(**(fields | changes))


def pass_gates(ledger, atom, lease):
    for gate in atom.required_gates:
        ledger.record_gate(lease, receipt(atom, lease, gate))


def test_submit_survives_reopen_and_is_idempotent(tmp_path, atom):
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        assert ledger.submit(atom) == atom.atom_id
    with WorkLedger(path) as ledger:
        assert ledger.submit(atom) == atom.atom_id
        snapshot = ledger.status(atom.atom_id)
        assert snapshot["status"] == "ready"
        assert snapshot["attempts"] == []
        assert snapshot["contract"] == atom.model_dump(mode="json")
        changed = WorkAtom.model_validate_json(
            atom.model_dump_json().replace(atom.objective, "New task")
        )
        with pytest.raises(Conflict):
            ledger.submit(changed)
        # A new ID cannot silently reuse the same idempotency key.
        with pytest.raises(Conflict):
            ledger.submit(
                WorkAtom.model_validate_json(
                    atom.model_dump_json().replace(
                        '"atom_id":"example-provider-edit"', '"atom_id":"different"'
                    )
                )
            )


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"max_attempts": True},
        {"max_attempts": 11},
        {"max_attempts": "2"},
        {"inputs_digest": "missing"},
        {"required_gates": []},
        {"writable_paths": ["../controller"]},
        {"writable_paths": ["/tmp"]},
        {"writable_paths": ["src//a"]},
        {"state": "accepted"},
        {"objective": "   "},
        {"context_budget": {"total_tokens": 10, "output_tokens": 10}},
    ],
)
def test_invalid_contract_rejected_before_persistence(tmp_path, atom, change):
    contract = tmp_path / "atom.json"
    contract.write_text(json.dumps(atom.model_dump(mode="json") | change))
    db = tmp_path / "invalid.db"
    result = subprocess.run(
        [sys.executable, "-m", "gflo", "--db", str(db), "submit", str(contract)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert json.loads(result.stderr)["error"] == "Invalid work contract"
    assert not db.exists()


def test_unvalidated_model_cannot_bypass_submission(ledger, atom):
    forged = atom.model_copy(update={"max_attempts": -1})
    with pytest.raises(ValidationError):
        ledger.submit(forged)
    with pytest.raises(KeyError):
        ledger.status(atom.atom_id)


def test_competing_connections_get_only_one_lease(tmp_path, atom):
    path = tmp_path / "race.db"
    with WorkLedger(path) as ledger:
        ledger.submit(atom)
    barrier = threading.Barrier(2)

    def claim(owner):
        with WorkLedger(path) as ledger:
            barrier.wait(timeout=10)
            try:
                return ledger.claim(atom.atom_id, owner)
            except Conflict:
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, ["one", "two"]))
    assert sum(result is not None for result in results) == 1
    with WorkLedger(path) as ledger:
        assert len(ledger.status(atom.atom_id)["attempts"]) == 1


def test_expiry_fences_late_results_and_requires_new_attempt(ledger, atom, clock):
    old = validating(ledger, atom)
    pass_gates(ledger, atom, old)
    clock[0] = old.expires_at
    for operation in (
        lambda: ledger.accept(old, current_inputs_digest=atom.inputs_digest),
        lambda: ledger.fail(old, "too late"),
        lambda: ledger.record_gate(old, receipt(atom, old, atom.required_gates[0])),
    ):
        with pytest.raises(Conflict):
            operation()
    assert ledger.reconcile() == [atom.atom_id]
    before = ledger.status(atom.atom_id)
    assert ledger.reconcile() == []
    failure_id = before["attempts"][0]["events"][-1]["event_id"]
    assert before["attempts"][0]["events"][-1]["kind"] == "expired"
    with pytest.raises(Conflict):
        ledger.claim(atom.atom_id, "new")
    fresh = ledger.claim(
        atom.atom_id,
        "new",
        retry=RetryPlan(failure_event=failure_id, strategy="reconcile prior sandbox and rebuild"),
    )
    assert fresh.attempt_id != old.attempt_id
    assert ledger.status(atom.atom_id)["attempts"][0] == before["attempts"][0]
    with pytest.raises(Conflict):
        ledger.start(old)
    ledger.start(fresh)
    ledger.candidate(fresh, CANDIDATE)
    # Even an identical candidate cannot reuse another attempt's passing evidence.
    with pytest.raises(Conflict):
        ledger.accept(fresh, current_inputs_digest=atom.inputs_digest)


def test_recovery_budget_and_retry_evidence(ledger, atom):
    atom = WorkAtom.model_validate_json(
        json.dumps(atom.model_dump(mode="json") | {"max_attempts": 2})
    )
    ledger.submit(atom)
    first = ledger.claim(atom.atom_id, "worker")
    failure = ledger.fail(first, "compiler diagnostic")
    for retry in (
        None,
        RetryPlan(failure_event=failure + 1, strategy="repair"),
        RetryPlan(failure_event=failure, strategy="initial"),
    ):
        with pytest.raises(Conflict):
            ledger.claim(atom.atom_id, "worker", retry=retry)
    second = ledger.claim(
        atom.atom_id,
        "worker",
        retry=RetryPlan(failure_event=failure, strategy="repair using compiler diagnostic"),
    )
    ledger.fail(second, "repair still fails")
    state = ledger.status(atom.atom_id)
    assert state["status"] == "quarantined"
    assert [a["ordinal"] for a in state["attempts"]] == [1, 2]
    assert all(a["events"][-1]["kind"] == "failed" for a in state["attempts"])
    with pytest.raises(Conflict):
        ledger.claim(atom.atom_id, "worker")


@pytest.mark.parametrize("outcome", ["fail", "inconclusive"])
def test_missing_or_nonpassing_gates_never_accept(ledger, atom, outcome):
    lease = validating(ledger, atom)
    with pytest.raises(Conflict):
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
    ledger.record_gate(lease, receipt(atom, lease, atom.required_gates[0]))
    with pytest.raises(Conflict):
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
    ledger.record_gate(lease, receipt(atom, lease, atom.required_gates[1], outcome=outcome))
    with pytest.raises(Conflict):
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
    with pytest.raises(Conflict):
        ledger.record_gate(lease, receipt(atom, lease, atom.required_gates[1]))
    assert ledger.status(atom.atom_id)["status"] == "validating"


@pytest.mark.parametrize(
    "change",
    [
        {"attempt_id": "wrong"},
        {"contract_digest": "0" * 64},
        {"inputs_digest": "0" * 64},
        {"candidate_digest": "0" * 64},
        {"validator_digest": "0" * 64},
        {"gate_id": "unrequested"},
    ],
)
def test_mismatched_gate_evidence_rejected(ledger, atom, change):
    lease = validating(ledger, atom)
    with pytest.raises(Conflict):
        ledger.record_gate(lease, receipt(atom, lease, atom.required_gates[0], **change))
    assert len(ledger.status(atom.atom_id)["attempts"][0]["events"]) == 3


def test_preconditions_and_forged_lease_cannot_accept(ledger, atom):
    lease = validating(ledger, atom)
    pass_gates(ledger, atom, lease)
    with pytest.raises(Conflict):
        ledger.accept(lease, current_inputs_digest="0" * 64)
    forged = Lease.model_validate(lease.model_copy(update={"token": "forged"}))
    with pytest.raises(Conflict):
        ledger.accept(forged, current_inputs_digest=atom.inputs_digest)
    assert ledger.status(atom.atom_id)["status"] == "validating"


def test_acceptance_is_atomic_and_idempotent_across_connections(tmp_path, atom):
    path = tmp_path / "accept.db"
    with WorkLedger(path) as ledger:
        lease = validating(ledger, atom)
        pass_gates(ledger, atom, lease)
    barrier = threading.Barrier(2)

    def accept(_):
        with WorkLedger(path) as ledger:
            barrier.wait(timeout=10)
            return ledger.accept(lease, current_inputs_digest=atom.inputs_digest)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(accept, range(2)))
    assert results[0] == results[1]
    with WorkLedger(path, clock=lambda: lease.expires_at + 100) as ledger:
        assert ledger.accept(lease, current_inputs_digest=atom.inputs_digest) == results[0]
        state = ledger.status(atom.atom_id)
        assert state["status"] == "accepted"
        assert [e["kind"] for e in state["attempts"][0]["events"]].count("accepted") == 1
        assert ledger.reconcile() == []
        assert lease.token not in json.dumps(state)


def test_crash_mid_transition_rolls_back_state_and_event(tmp_path, atom):
    path = tmp_path / "crash.db"
    with WorkLedger(path) as ledger:
        ledger.submit(atom)
        lease = ledger.claim(atom.atom_id, "controller")
    # Kill the process after state changes but before its corresponding event/commit.
    code = """
import os, sys
from gflo.ledger import WorkLedger
from gflo.records import Lease
with WorkLedger(sys.argv[1]) as ledger:
    ledger._event = lambda *args: os._exit(23)
    ledger.start(Lease.model_validate_json(sys.argv[2]))
"""
    result = subprocess.run([sys.executable, "-c", code, str(path), lease.model_dump_json()])
    assert result.returncode == 23
    with WorkLedger(path) as ledger:
        state = ledger.status(atom.atom_id)
        assert state["status"] == "leased"
        assert [e["kind"] for e in state["attempts"][0]["events"]] == ["leased"]
        ledger.start(lease)
        assert ledger.status(atom.atom_id)["status"] == "running"


def test_immutable_history_and_unknown_schema(tmp_path, atom):
    path = tmp_path / "history.db"
    with WorkLedger(path) as ledger:
        lease = validating(ledger, atom)
        pass_gates(ledger, atom, lease)
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
    connection = sqlite3.connect(path)
    try:
        for table in ("atoms", "attempts", "events", "gates", "acceptances"):
            with pytest.raises(sqlite3.IntegrityError, match="immutable history"):
                connection.execute(f"DELETE FROM {table}")
            connection.rollback()
        connection.execute("PRAGMA user_version=99")
    finally:
        connection.close()
    with pytest.raises(ValueError, match="Unsupported ledger schema"):
        WorkLedger(path)


def test_cli_submission_status_and_restart_reconciliation(tmp_path, atom):
    path = tmp_path / "cli.db"
    prefix = [sys.executable, "-m", "gflo", "--db", str(path)]
    submitted = subprocess.run(
        prefix + ["submit", str(ROOT / "examples/work-atom.json")],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(submitted.stdout)["atom_id"] == atom.atom_id
    with WorkLedger(path, clock=lambda: 1000.0) as ledger:
        lease = ledger.claim(atom.atom_id, "old-controller", lease_seconds=1)
        ledger.start(lease)
    resumed = subprocess.run(prefix + ["resume"], capture_output=True, text=True, check=True)
    assert json.loads(resumed.stdout) == {
        "reconciled_atoms": [atom.atom_id],
        "workers_dispatched": False,
    }
    status = subprocess.run(
        prefix + ["status", atom.atom_id], capture_output=True, text=True, check=True
    )
    assert json.loads(status.stdout)["status"] == "retry-ready"
    missing = subprocess.run(prefix + ["status", "absent"], capture_output=True, text=True)
    assert missing.returncode == 1
    assert "error" in json.loads(missing.stderr)


def test_expiry_of_final_attempt_quarantines_after_reopen(tmp_path, atom):
    path = tmp_path / "expired.db"
    atom = WorkAtom.model_validate_json(
        json.dumps(atom.model_dump(mode="json") | {"max_attempts": 1})
    )
    with WorkLedger(path, clock=lambda: 1000.0) as ledger:
        ledger.submit(atom)
        ledger.claim(atom.atom_id, "worker", lease_seconds=1)
    with WorkLedger(path, clock=lambda: 1001.0) as ledger:
        assert ledger.reconcile() == [atom.atom_id]
        assert ledger.status(atom.atom_id)["status"] == "quarantined"
        with pytest.raises(Conflict):
            ledger.claim(atom.atom_id, "worker")


def test_repeated_strategy_evidence_pair_is_rejected(ledger, atom):
    ledger.artifacts.publish(b"evidence")
    ledger.submit(atom)
    initial = ledger.claim(atom.atom_id, "controller")
    failure = ledger.fail(initial, "first failure")
    retried = ledger.claim(
        atom.atom_id,
        "controller",
        retry=RetryPlan(failure_event=failure, strategy="initial", new_evidence=EVIDENCE),
    )
    next_failure = ledger.fail(retried, "same failure")
    with pytest.raises(Conflict):
        ledger.claim(
            atom.atom_id,
            "controller",
            retry=RetryPlan(failure_event=next_failure, strategy="initial", new_evidence=EVIDENCE),
        )
    assert len(ledger.status(atom.atom_id)["attempts"]) == 2


def test_worker_cannot_skip_running_or_validation(ledger, atom):
    ledger.artifacts.publish(b"candidate")
    ledger.artifacts.publish(b"evidence")
    ledger.submit(atom)
    lease = ledger.claim(atom.atom_id, "controller")
    with pytest.raises(Conflict):
        ledger.candidate(lease, CANDIDATE)
    with pytest.raises(Conflict):
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
    ledger.start(lease)
    with pytest.raises(Conflict):
        ledger.record_gate(lease, receipt(atom, lease, atom.required_gates[0]))
    assert ledger.status(atom.atom_id)["status"] == "running"


def test_durable_settings_and_foreign_keys(ledger):
    assert ledger._db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert ledger._db.execute("PRAGMA synchronous").fetchone()[0] == 2
    assert ledger._db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        ledger._db.execute(
            "INSERT INTO events(attempt_id,kind,details,recorded_at) "
            "VALUES ('missing','failed','{}',1000)"
        )


def test_gate_receipts_survive_reopen_before_acceptance(tmp_path, atom):
    path = tmp_path / "gates.db"
    with WorkLedger(path) as ledger:
        lease = validating(ledger, atom)
        pass_gates(ledger, atom, lease)
    with WorkLedger(path) as ledger:
        receipts = ledger.status(atom.atom_id)["attempts"][0]["gate_receipts"]
        assert len(receipts) == len(atom.required_gates)
        assert all(r["runner_id"] == "trusted-runner-v1" for r in receipts)
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)


@pytest.mark.parametrize("target", ["candidate", "evidence"])
@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_accept_reverifies_bytes_and_preserves_history(tmp_path, atom, target, damage):
    from gflo.artifacts import ArtifactError

    path = tmp_path / "integrity.db"
    with WorkLedger(path) as ledger:
        lease = validating(ledger, atom)
        pass_gates(ledger, atom, lease)
        obj = ledger.artifacts.root / (CANDIDATE if target == "candidate" else EVIDENCE)
        if damage == "missing":
            obj.unlink()
        else:
            obj.chmod(0o600)
            obj.write_bytes(b"damaged")
    with WorkLedger(path) as ledger:
        with pytest.raises(ArtifactError):
            ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
        assert ledger.status(atom.atom_id)["status"] == "validating"
        report = ledger.audit_artifacts()
        assert getattr(report, damage) == (obj.name,)
        assert report.unreferenced == ()


def test_absent_content_cannot_enter_ledger(ledger, atom):
    from gflo.artifacts import ArtifactError

    ledger.submit(atom)
    lease = ledger.claim(atom.atom_id, "controller")
    ledger.start(lease)
    with pytest.raises(ArtifactError):
        ledger.candidate(lease, CANDIDATE)
    assert ledger.status(atom.atom_id)["status"] == "running"
    ledger.artifacts.publish(b"candidate")
    ledger.candidate(lease, CANDIDATE)
    with pytest.raises(ArtifactError):
        ledger.record_gate(lease, receipt(atom, lease, atom.required_gates[0]))
    assert ledger.status(atom.atom_id)["attempts"][0]["gate_receipts"] == []
    failure = ledger.fail(lease, "missing evidence")
    with pytest.raises(ArtifactError):
        ledger.claim(
            atom.atom_id,
            "controller",
            retry=RetryPlan(failure_event=failure, strategy="repair", new_evidence=EVIDENCE),
        )


def test_failed_attempt_content_retained_and_orphan_discovered(ledger, atom):
    lease = validating(ledger, atom)
    pass_gates(ledger, atom, lease)
    ledger.fail(lease, "failure after evidence")
    uncommitted = ledger.artifacts.publish(b"published before ledger commit")
    report = ledger.audit_artifacts()
    assert report.unreferenced == (uncommitted,)
    assert report.missing == report.corrupt == ()
    assert ledger.artifacts.read(CANDIDATE) == b"candidate"
    assert ledger.artifacts.read(EVIDENCE) == b"evidence"


def test_dependency_artifacts_must_exist_and_remain_referenced(ledger, atom):
    from gflo.artifacts import ArtifactError

    atom = WorkAtom.model_validate_json(
        json.dumps(atom.model_dump(mode="json") | {"dependency_artifacts": [CANDIDATE]})
    )
    with pytest.raises(ArtifactError):
        ledger.submit(atom)
    ledger.artifacts.publish(b"candidate")
    ledger.submit(atom)
    assert ledger.audit_artifacts().unreferenced == ()


def test_crash_between_publication_and_ledger_commit_leaves_orphan(tmp_path, atom):
    path = tmp_path / "publication-crash.db"
    with WorkLedger(path) as ledger:
        ledger.submit(atom)
        lease = ledger.claim(atom.atom_id, "controller")
        ledger.start(lease)
    code = """
import os, sys
from gflo.ledger import WorkLedger
from gflo.records import Lease
with WorkLedger(sys.argv[1]) as ledger:
    digest = ledger.artifacts.publish(b"candidate")
    ledger._event = lambda *args: os._exit(24)
    ledger.candidate(Lease.model_validate_json(sys.argv[2]), digest)
"""
    result = subprocess.run([sys.executable, "-c", code, str(path), lease.model_dump_json()])
    assert result.returncode == 24
    with WorkLedger(path) as ledger:
        assert ledger.status(atom.atom_id)["status"] == "running"
        assert ledger.audit_artifacts().unreferenced == (CANDIDATE,)
        ledger.candidate(lease, CANDIDATE)
        assert ledger.audit_artifacts().unreferenced == ()
    result = subprocess.run(
        [sys.executable, "-m", "gflo", "--db", str(path), "audit-artifacts"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == {
        "missing": [],
        "corrupt": [],
        "unreferenced": [],
        "staging": [],
    }


def test_lost_accepted_bytes_do_not_rewrite_acceptance(ledger, atom):
    from gflo.artifacts import ArtifactError

    lease = validating(ledger, atom)
    pass_gates(ledger, atom, lease)
    ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
    (ledger.artifacts.root / CANDIDATE).unlink()
    with pytest.raises(ArtifactError):
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
    assert ledger.status(atom.atom_id)["status"] == "accepted"
    assert ledger.audit_artifacts().missing == (CANDIDATE,)
