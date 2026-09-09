"""Supplemental cases separate from the worker's frozen acceptance gate."""

import json

from test_controller import plan as plan_fixture
from test_controller import setup
from test_history_filter import invoke

from gflo.ledger import WorkLedger
from gflo.model import ModelError


def test_attempt_without_candidate(tmp_path, monkeypatch, capsys):
    plan = plan_fixture.__wrapped__()
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        controller, _, _ = setup(ledger, plan, [ModelError("server unavailable")])
        controller.run(plan.atom.atom_id)
        before = ledger.status(plan.atom.atom_id)
    code, out, err = invoke(
        monkeypatch, capsys, path, plan.atom.atom_id, "--attempt", "1", "--format", "json"
    )
    assert code == 0 and not err
    assert json.loads(out)["attempts"][0]["candidates"] == []
    with WorkLedger(path) as ledger:
        assert ledger.status(plan.atom.atom_id) == before


def test_ready_history_has_no_selectable_attempt(tmp_path, monkeypatch, capsys):
    from gflo.controller import prepare_run

    plan = plan_fixture.__wrapped__()
    path = tmp_path / "ledger.db"
    with WorkLedger(path) as ledger:
        prepare_run(ledger, plan)
    code, out, err = invoke(monkeypatch, capsys, path, plan.atom.atom_id, "--attempt", "1")
    assert code != 0 and not out and err
    code, out, err = invoke(monkeypatch, capsys, path, plan.atom.atom_id, "--format", "json")
    assert code == 0 and json.loads(out)["attempts"] == []
