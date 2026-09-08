"""Retried/failed model work remains visible in read-only cost reports."""

import json
from pathlib import Path

import pytest

from gflo.artifacts import ArtifactError
from gflo.ledger import WorkLedger
from gflo.model import ModelTurn
from gflo.records import RetryPlan, WorkAtom
from gflo.reporting import cost_report
from gflo.worker import CandidateResult


def setup_run(tmp_path):
    ledger = WorkLedger(tmp_path / "ledger.db")
    atom = WorkAtom.model_validate_json(Path("examples/work-atom.json").read_bytes())
    ledger.submit(atom)
    lease = ledger.claim(atom.atom_id, "controller")
    ledger.start(lease)
    return ledger, atom, lease


def publish_turn(ledger):
    raw = ledger.artifacts.publish(b"fixture")
    turn = ModelTurn(
        manifest_digest=raw,
        response_digest=raw,
        result=CandidateResult(kind="candidate", changes={"main.py": "print(42)"}),
        prompt_tokens=100,
        completion_tokens=20,
        elapsed_seconds=2.0,
    )
    digest = ledger.artifacts.publish(turn.canonical().encode())
    return ledger.artifacts.publish(
        json.dumps(
            {
                "turn_digest": digest,
                "elapsed_seconds": 2.5,
            }
        ).encode()
    )


def test_retry_and_missing_usage_are_counted_without_mutating_history(tmp_path):
    ledger, atom, lease = setup_run(tmp_path)
    with ledger:
        first = publish_turn(ledger)
        ledger.observe(lease, "model", first)
        failure = ledger.fail(lease, "Candidate failed behavior gate")
        retry = ledger.claim(
            atom.atom_id,
            "controller",
            retry=RetryPlan(
                failure_event=failure,
                strategy="Use failure evidence",
            ),
        )
        ledger.start(retry)
        missing = ledger.artifacts.publish(
            json.dumps(
                {
                    "elapsed_seconds": 3.0,
                    "error": {"type": "ModelError", "message": "Timeout"},
                }
            ).encode()
        )
        ledger.observe(retry, "model", missing)
        ledger.fail(retry, "Model unavailable")
        before = ledger.status(atom.atom_id)
        report = cost_report(ledger, atom.atom_id)
        assert report["totals"]["validated_prompt_tokens"] == 100
        assert report["totals"]["validated_completion_tokens"] == 20
        assert report["totals"]["observed_model_seconds"] == 5.5
        assert report["totals"]["observations_without_validated_usage"] == 1
        assert not report["totals"]["usage_complete_for_recorded_observations"]
        assert report["retries"]["observed_model_seconds"] == 3.0
        assert report["retries"]["validated_prompt_tokens"] == 0
        assert report["attempts"][0]["failures"][0]["reason"] == "Candidate failed behavior gate"
        assert cost_report(ledger, atom.atom_id) == report
        assert ledger.status(atom.atom_id) == before


def test_corrupt_referenced_turn_does_not_produce_a_cost_report(tmp_path):
    ledger, atom, lease = setup_run(tmp_path)
    with ledger:
        evidence = publish_turn(ledger)
        ledger.observe(lease, "model", evidence)
        turn = json.loads(ledger.artifacts.read(evidence))["turn_digest"]
        path = tmp_path / "ledger.db.artifacts" / turn
        path.chmod(0o600)
        path.write_text("{}")
        with pytest.raises(ArtifactError, match="Corrupt"):
            cost_report(ledger, atom.atom_id)


def test_legacy_observation_has_explicitly_unknown_cost(tmp_path):
    ledger, atom, lease = setup_run(tmp_path)
    with ledger:
        ledger.observe(lease, "model", ledger.artifacts.publish(b"{}"))
        report = cost_report(ledger, atom.atom_id)
        assert report["totals"]["observations_without_timing"] == 1
        assert report["totals"]["observations_without_validated_usage"] == 1
        assert not report["totals"]["timing_complete_for_recorded_observations"]
