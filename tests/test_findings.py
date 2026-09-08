"""Later contradictory evidence blocks reuse without erasing historical acceptance."""

import json
import sqlite3

import pytest
from test_integration import Broker, make_fixture

from gflo.artifacts import ArtifactError
from gflo.controller import Controller, RunPlan
from gflo.history import change_history, render_history
from gflo.integration import integrate
from gflo.ledger import Conflict, WorkLedger
from gflo.records import AcceptanceFinding


def finding_for(ledger, atom_id="provider"):
    state = ledger.status(atom_id)
    evidence = ledger.artifacts.publish(b"Independent regression demonstrates wrong output")
    from gflo.records import WorkAtom

    return AcceptanceFinding(
        atom_id=atom_id,
        contract_digest=WorkAtom.model_validate_json(json.dumps(state["contract"])).digest(),
        candidate_digest=state["candidate_digest"],
        evidence_digest=evidence,
        reason="Wrong output for repeated IDs",
    )


def test_finding_preserves_acceptance_blocks_replay_and_survives_reopen(tmp_path):
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        make_fixture(ledger)
        before = ledger.status("provider")
        acceptance = ledger._db.execute(
            "SELECT receipt FROM acceptances WHERE atom_id='provider'"
        ).fetchone()[0]
        finding = finding_for(ledger)
        event = ledger.record_finding(finding)
        assert ledger.record_finding(finding) == event
        after = ledger.status("provider")
        assert after["status"] == "accepted" and after["acceptance_challenged"]
        assert after["attempts"][0]["events"][:-1] == before["attempts"][0]["events"]
        assert after["acceptance_findings"] == [finding.model_dump(mode="json")]
        assert ledger._db.execute("PRAGMA user_version").fetchone()[0] == 3
        assert (
            ledger._db.execute(
                "SELECT receipt FROM acceptances WHERE atom_id='provider'"
            ).fetchone()[0]
            == acceptance
        )
        with pytest.raises(sqlite3.IntegrityError):
            ledger._db.execute("DELETE FROM events WHERE event_id=?", (event,))
    with WorkLedger(path) as ledger:
        with pytest.raises(Conflict, match="contradictory"):
            ledger.accept(
                ledger.active_lease("provider"),
                current_inputs_digest=before["contract"]["inputs_digest"],
            )
        text = render_history(change_history(ledger, "provider"))
        assert "Reuse blocked by later evidence" in text
        assert ledger.audit_artifacts().missing == ()
        evidence = ledger.artifacts.root / finding.evidence_digest
        evidence.unlink()
        assert finding.evidence_digest in ledger.audit_artifacts().missing
        with pytest.raises(Conflict, match="contradictory"):
            ledger.accept(
                ledger.active_lease("provider"),
                current_inputs_digest=before["contract"]["inputs_digest"],
            )


@pytest.mark.parametrize("field", ["contract_digest", "candidate_digest", "evidence_digest"])
def test_wrong_or_missing_finding_bindings_cannot_change_state(tmp_path, field):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        make_fixture(ledger)
        before = ledger.status("provider")
        fields = finding_for(ledger).model_dump(mode="json") | {field: "0" * 64}
        with pytest.raises((Conflict, ArtifactError)):
            ledger.record_finding(AcceptanceFinding.model_validate_json(json.dumps(fields)))
        assert ledger.status("provider") == before
        assert ledger._db.execute("PRAGMA user_version").fetchone()[0] == 2


def test_findings_block_prepared_integration_before_claim(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger)
        ledger.record_finding(finding_for(ledger))
        with pytest.raises(Conflict, match="contradictory"):
            integrate(ledger, plan, Broker(ledger), lambda: plan.inputs.state)
        with pytest.raises(KeyError):
            ledger.status("integration")


def test_findings_block_controller_replay_without_model_or_broker_work(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        make_fixture(ledger)
        ledger.record_finding(finding_for(ledger))
        plan = RunPlan.model_validate_json(ledger.run_plan("provider"))

        class Model:
            artifacts = ledger.artifacts
            profile = plan.model_profile

            def turn(self, *args, **kwargs):
                raise AssertionError("No inference allowed")

        broker = Broker(ledger)
        with pytest.raises(Conflict, match="contradictory"):
            Controller(ledger, Model(), broker).run("provider")
        assert broker.calls == 0


def test_later_child_finding_blocks_reuse_of_existing_integration(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger)
        broker = Broker(ledger)
        original = integrate(ledger, plan, broker, lambda: plan.inputs.state)
        ledger.record_finding(finding_for(ledger))
        with pytest.raises(Conflict, match="contradictory"):
            integrate(ledger, plan, broker, lambda: plan.inputs.state)
        assert ledger.status("integration") == original
        assert broker.calls == 1


def test_finding_committed_after_snapshot_still_blocks_acceptance_replay(tmp_path):
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger, WorkLedger(path) as other:
        make_fixture(ledger)
        finding = finding_for(ledger)
        original = ledger.artifacts.verify
        armed = True

        def between_snapshot_and_transaction(digest):
            nonlocal armed
            original(digest)
            if armed and digest == finding.candidate_digest:
                armed = False
                other.record_finding(finding)

        ledger.artifacts.verify = between_snapshot_and_transaction
        with pytest.raises(Conflict, match="contradictory"):
            ledger.accept(
                ledger.active_lease("provider"),
                current_inputs_digest=ledger.status("provider")["contract"]["inputs_digest"],
            )
        assert not armed
        assert ledger.status("provider")["acceptance_challenged"]


def test_failed_finding_transaction_rolls_back_reader_version_and_event(tmp_path, monkeypatch):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        make_fixture(ledger)
        finding = finding_for(ledger)
        before = ledger.status("provider")

        def failed_event(*args, **kwargs):
            raise OSError("Injected event failure")

        monkeypatch.setattr(ledger, "_event", failed_event)
        with pytest.raises(OSError, match="Injected"):
            ledger.record_finding(finding)
        assert ledger._db.execute("PRAGMA user_version").fetchone()[0] == 2
        assert ledger.status("provider") == before


def test_finding_cannot_challenge_unaccepted_work(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger)
        ledger.artifacts.publish(plan.inputs.canonical().encode())
        ledger.submit(plan.atom)
        fields = finding_for(ledger).model_dump(mode="json") | {
            "atom_id": plan.atom.atom_id,
            "contract_digest": plan.atom.digest(),
        }
        before = ledger.status(plan.atom.atom_id)
        with pytest.raises(Conflict, match="accepted atom"):
            ledger.record_finding(AcceptanceFinding.model_validate_json(json.dumps(fields)))
        assert ledger.status(plan.atom.atom_id) == before
