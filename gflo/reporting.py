"""Read-only cumulative measurements from retained model observations."""

from __future__ import annotations

import math
from typing import Any

from gflo.ledger import WorkLedger
from gflo.model import ModelTurn
from gflo.worker import strict_json


def cost_report(ledger: WorkLedger, atom_id: str) -> dict[str, Any]:
    state = ledger.status(atom_id)
    attempts = []
    for attempt in state["attempts"]:
        observations = []
        failures = []
        for event in attempt["events"]:
            if event["kind"] in ("failed", "expired"):
                failures.append(event["details"])
            if event["kind"] != "observation" or event["details"]["kind"] != "model":
                continue
            digest = event["details"]["digest"]
            evidence = strict_json(ledger.artifacts.read(digest).decode())
            if not isinstance(evidence, dict):
                raise ValueError("Model evidence must be an object")
            elapsed = evidence.get("elapsed_seconds")
            if elapsed is not None and (
                type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0
            ):
                raise ValueError("Invalid observed model duration")
            observation = {
                "event_id": event["event_id"],
                "evidence_digest": digest,
                "model_seconds": elapsed,
                "error": evidence.get("error"),
                "prompt_tokens": None,
                "completion_tokens": None,
            }
            if "turn_digest" in evidence:
                turn = ModelTurn.model_validate_json(ledger.artifacts.read(evidence["turn_digest"]))
                if turn.prompt_tokens <= 0 or turn.completion_tokens <= 0:
                    raise ValueError("Invalid validated token usage")
                observation.update(
                    prompt_tokens=turn.prompt_tokens,
                    completion_tokens=turn.completion_tokens,
                )
            observations.append(observation)
        attempts.append(
            {
                "attempt_id": attempt["attempt_id"],
                "ordinal": attempt["ordinal"],
                "failures": failures,
                "observations": observations,
            }
        )

    def aggregate(items: list[dict[str, Any]]) -> dict[str, Any]:
        observations = [o for a in items for o in a["observations"]]
        missing_usage = sum(o["prompt_tokens"] is None for o in observations)
        missing_time = sum(o["model_seconds"] is None for o in observations)
        return {
            "attempts": len(items),
            "model_observations": len(observations),
            "validated_prompt_tokens": sum(o["prompt_tokens"] or 0 for o in observations),
            "validated_completion_tokens": sum(o["completion_tokens"] or 0 for o in observations),
            "observed_model_seconds": sum(o["model_seconds"] or 0 for o in observations),
            "observations_without_validated_usage": missing_usage,
            "observations_without_timing": missing_time,
            "usage_complete_for_recorded_observations": missing_usage == 0,
            "timing_complete_for_recorded_observations": missing_time == 0,
        }

    return {
        "schema_version": 1,
        "atom_id": atom_id,
        "status": state["status"],
        "totals": aggregate(attempts),
        "retries": aggregate(attempts[1:]),
        "attempts": attempts,
        "measurement_scope": (
            "Recorded model observations only; validated token sums are lower bounds when usage "
            "is missing. Model duration includes client work and waiting, not broker time. "
            "Unrecorded work lost during process death, energy and replanning are not measured."
        ),
    }
