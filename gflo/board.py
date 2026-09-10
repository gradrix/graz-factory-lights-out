"""Four bounded independent advisers and one accountable coordinator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gflo.artifacts import ArtifactError, ArtifactStore
from gflo.board_records import ROLES, SpecialistReport
from gflo.model import ModelError, ModelProfile
from gflo.planning import PlanQuestions, RepositoryFeatureRequest, draft_feature
from gflo.repository import Repository


def draft_board(
    request: RepositoryFeatureRequest,
    profile: ModelProfile,
    output: Path,
    *,
    deployment: str,
    repository: Repository,
    context_paths: tuple[str, ...],
) -> dict[str, Any]:
    request = RepositoryFeatureRequest.model_validate(request)
    if repository.source.ref != request.source:
        raise ValueError("Board repository differs from the request")
    # Fail before opening a run if the shared source selection is incomplete.
    repository.select(context_paths, purpose="execution")
    output.mkdir(parents=True, exist_ok=False)
    artifacts = ArtifactStore(output / "artifacts")
    artifacts.publish(request.canonical().encode())
    result: dict[str, Any] = dict(
        status="interrupted",
        profile="specialist-board-v3",
        execution_authorized=False,
        request_digest=request.digest(),
        stages=[],
        max_model_turns=30,
        max_reserved_tokens=30 * 12288,
    )
    reports = []
    try:
        for role in ROLES:
            stage = draft_feature(
                request,
                profile,
                output / role,
                deployment=deployment,
                repository=repository,
                context_paths=context_paths,
                specialist=role,
            )
            result["stages"].append(dict(role=role, result=stage))
            if stage["status"] != "advisory":
                result["status"] = "specialist-halt"
                return result
            reports.append(
                SpecialistReport.model_validate_json((output / role / "report.json").read_bytes())
            )
            report = reports[-1]
            artifacts.publish(report.canonical().encode())
            blockers = [f for f in report.findings if f.severity == "blocker"]
            if report.questions or blockers:
                questions = PlanQuestions(
                    request_digest=request.digest(),
                    questions=tuple(report.questions)
                    + tuple(f"Resolve {role}:{f.finding_id}: {f.observation}" for f in blockers),
                    rationale=f"Unresolved {role} blockers stop synthesis.",
                )
                (output / "questions.json").write_text(questions.canonical() + "\n")
                result.update(
                    status="needs-info",
                    questions=list(questions.questions),
                    report_digests=[r.digest() for r in reports],
                    stopped_at=role,
                    questions_digest=artifacts.publish(questions.canonical().encode()),
                )
                return result
        if sum(len(r.canonical().encode()) for r in reports) > 12000:
            result["status"] = "advice-budget-halt"
            return result
        stage = draft_feature(
            request,
            profile,
            output / "coordinator",
            deployment=deployment,
            repository=repository,
            context_paths=context_paths,
            reports=tuple(reports),
        )
        result["stages"].append(dict(role="coordinator", result=stage))
        result["status"] = "needs-info" if stage.get("questions") else stage["status"]
        result["report_digests"] = [r.digest() for r in reports]
        for name in ("proposal.json", "questions.json", "synthesis.json"):
            path = output / "coordinator" / name
            if path.exists():
                (output / name).write_bytes(path.read_bytes())
        return result
    except (ModelError, ArtifactError):
        result["status"] = "infrastructure-halt"
        raise
    finally:
        # Full per-stage observations remain durable even if a service call raises.
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
