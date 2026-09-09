"""Independent acceptance checks for the supervised local-worker CLI trial."""

import json
import sys

import pytest
from test_controller import plan as plan_fixture
from test_controller import setup

from gflo.cli import main
from gflo.history import change_history, render_history
from gflo.ledger import WorkLedger
from gflo.records import AcceptanceFinding
from gflo.worker import CandidateResult


@pytest.fixture
def history_db(tmp_path):
    plan = plan_fixture.__wrapped__()
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        controller, _, _ = setup(
            ledger,
            plan,
            [
                CandidateResult(kind="candidate", changes={"main.py": "print(1)"}),
                CandidateResult(kind="candidate", changes={"main.py": "print(42)"}),
            ],
        )
        state = controller.run(plan.atom.atom_id)
        evidence = ledger.artifacts.publish(b"independent review found a defect")
        ledger.record_finding(
            AcceptanceFinding(
                atom_id=plan.atom.atom_id,
                contract_digest=plan.atom.digest(),
                candidate_digest=state["candidate_digest"],
                evidence_digest=evidence,
                reason="Review required before reuse",
            )
        )
    return path, plan.atom.atom_id


def invoke(monkeypatch, capsys, path, identity, *args):
    monkeypatch.setattr(sys, "argv", ["gflo", "--db", str(path), "history", identity, *args])
    try:
        code = main()
    except SystemExit as exc:
        code = exc.code
    out = capsys.readouterr()
    return code, out.out, out.err


@pytest.mark.parametrize("ordinal", [1, 2])
def test_selected_json_preserves_task_metadata(history_db, monkeypatch, capsys, ordinal):
    path, identity = history_db
    with WorkLedger(path) as ledger:
        before = ledger.status(identity)
        expected = change_history(ledger, identity)
    expected["attempts"] = [a for a in expected["attempts"] if a["ordinal"] == ordinal]
    code, out, err = invoke(
        monkeypatch, capsys, path, identity, "--attempt", str(ordinal), "--format", "json"
    )
    assert code == 0 and not err
    assert json.loads(out) == expected
    with WorkLedger(path) as ledger:
        assert ledger.status(identity) == before


@pytest.mark.parametrize("ordinal", [1, 2])
def test_selected_text_preserves_warning_and_baseline(history_db, monkeypatch, capsys, ordinal):
    path, identity = history_db
    with WorkLedger(path) as ledger:
        expected = change_history(ledger, identity)
    expected["attempts"] = [a for a in expected["attempts"] if a["ordinal"] == ordinal]
    code, out, err = invoke(monkeypatch, capsys, path, identity, "--attempt", str(ordinal))
    assert code == 0 and not err
    assert out == render_history(expected)
    assert "Reuse blocked by later evidence" in out
    assert "-print(0)" in out


@pytest.mark.parametrize("ordinal", ["0", "-1", "3", "nonsense", "1.0"])
def test_invalid_or_missing_ordinal_fails(history_db, monkeypatch, capsys, ordinal):
    code, out, err = invoke(monkeypatch, capsys, *history_db, "--attempt", ordinal)
    assert code != 0 and err
    assert not out


def test_default_output_unchanged(history_db, monkeypatch, capsys):
    path, identity = history_db
    with WorkLedger(path) as ledger:
        expected = change_history(ledger, identity)
    code, out, err = invoke(monkeypatch, capsys, path, identity, "--format", "json")
    assert code == 0 and json.loads(out) == expected
    code, out, err = invoke(monkeypatch, capsys, path, identity)
    assert code == 0 and out == render_history(expected)


def test_unselected_corruption_still_fails(history_db, monkeypatch, capsys):
    path, identity = history_db
    with WorkLedger(path) as ledger:
        history = change_history(ledger, identity)
        digest = history["attempts"][0]["candidates"][0]["digest"]
        artifact = ledger.artifacts.root / digest
        artifact.chmod(0o600)
        artifact.write_bytes(b"corrupted")
    code, out, err = invoke(monkeypatch, capsys, path, identity, "--attempt", "2")
    assert code != 0 and not out
    assert "Corrupt" in err
