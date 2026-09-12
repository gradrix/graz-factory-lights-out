"""Explicit operator-prepared plans for repeatable, supervised qualification.

This supplies a proposal to the normal policy compiler. It grants no execution
scope, accepts no results, and does not claim autonomous model planning.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from gflo.artifacts import ArtifactStore
from gflo.model import ModelProfile
from gflo.planning import PlanProposal, RepositoryFeatureRequest


def prepared_planner(proposal: PlanProposal) -> Callable[..., dict[str, Any]]:
    """Freeze a proposal and return a build_feature planner with explicit provenance."""
    frozen = PlanProposal.model_validate_json(proposal.canonical())

    def draft(
        request: RepositoryFeatureRequest,
        profile: ModelProfile,
        output: Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if request.digest() != frozen.request_digest:
            raise ValueError("Prepared proposal belongs to a different request")
        output.mkdir(parents=True, exist_ok=False)
        artifacts = ArtifactStore(output / "artifacts")
        digest = artifacts.publish(frozen.canonical().encode())
        (output / "proposal.json").write_text(frozen.canonical() + "\n")
        state: dict[str, Any] = {
            "status": "needs-review",
            "questions": list(frozen.questions),
            "proposal_digest": digest,
            "planner_origin": "operator-prepared-v1",
            "observations": [],
        }
        (output / "result.json").write_text(json.dumps(state, sort_keys=True) + "\n")
        return state

    return draft
