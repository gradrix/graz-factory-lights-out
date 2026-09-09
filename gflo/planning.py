"""Bounded feature-plan proposals; model prose never grants execution authority."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, model_validator

from gflo.artifacts import ArtifactError, ArtifactStore
from gflo.broker import SourceBundle
from gflo.model import LocalModel, ModelError, ModelProfile
from gflo.records import Digest, Identifier, Record, Text, WorkAtom
from gflo.worker import CandidateResult, Diagnostic, InputSnapshot, ReadFileRequest, within


def _paths(paths: tuple[str, ...]) -> None:
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate paths")
    for path in paths:
        if (
            path.startswith("/")
            or "\\" in path
            or any(p in ("", ".", "..") for p in path.split("/"))
        ):
            raise ValueError("Paths must be normalized and relative")


class PlanEnvironment(Record):
    image: Annotated[str, Field(pattern=r"^(?:[A-Za-z0-9_./:-]+@)?sha256:[a-f0-9]{64}$")]
    description: Annotated[str, Field(min_length=1, max_length=2048)]


class FeatureRequest(Record):
    feature_id: Identifier
    objective: Annotated[str, Field(min_length=1, max_length=4096)]
    requirements: Annotated[dict[Identifier, Text], Field(min_length=1, max_length=16)]
    source_revision: Text
    source: SourceBundle
    allowed_paths: Annotated[tuple[str, ...], Field(min_length=1, max_length=32)]
    selected_paths: Annotated[tuple[str, ...], Field(max_length=16)]
    environments: Annotated[dict[Identifier, PlanEnvironment], Field(min_length=1, max_length=8)]

    @model_validator(mode="after")
    def scopes(self) -> FeatureRequest:
        _paths(self.allowed_paths)
        _paths(self.selected_paths)
        if not set(self.selected_paths) <= self.source.files.keys():
            raise ValueError("Selected source is missing")
        if "factory-plan.json" in self.source.files:
            raise ValueError("Reserved planning output path already exists")
        return self


class PlannedTask(Record):
    task_id: Identifier
    objective: Annotated[str, Field(min_length=1, max_length=2048)]
    requirement_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=16)]
    depends_on: Annotated[tuple[Identifier, ...], Field(max_length=12)]
    writable_paths: Annotated[tuple[str, ...], Field(min_length=1, max_length=16)]
    read_paths: Annotated[tuple[str, ...], Field(max_length=32)]
    environment_id: Identifier
    interface_contracts: Annotated[tuple[Text, ...], Field(min_length=1, max_length=16)]
    acceptance_checks: Annotated[tuple[Text, ...], Field(min_length=1, max_length=16)]


class PlanProposal(Record):
    request_digest: Digest
    tasks: Annotated[tuple[PlannedTask, ...], Field(min_length=1, max_length=12)]
    questions: Annotated[tuple[Text, ...], Field(max_length=16)]
    rationale: Annotated[str, Field(min_length=1, max_length=4096)]


def validate_proposal(request: FeatureRequest, proposal: PlanProposal) -> tuple[str, ...]:
    """Return deterministic dependency order; validate structure, not semantic adequacy."""
    request = FeatureRequest.model_validate(request)
    proposal = PlanProposal.model_validate(proposal)
    if proposal.request_digest != request.digest():
        raise ValueError("Proposal is bound to another request/source snapshot")
    tasks = {t.task_id: t for t in proposal.tasks}
    if len(tasks) != len(proposal.tasks):
        raise ValueError("Duplicate task identities")
    covered: set[str] = set()
    for task in proposal.tasks:
        _paths(task.writable_paths)
        _paths(task.read_paths)
        if not all(within(p, request.allowed_paths) for p in task.writable_paths):
            raise ValueError("Task writes outside allowed scope")
        if not set(task.read_paths) <= request.source.files.keys():
            raise ValueError("Task references missing source")
        if task.environment_id not in request.environments:
            raise ValueError("Task requests an unknown environment")
        if not set(task.requirement_ids) <= request.requirements.keys():
            raise ValueError("Task references an unknown requirement")
        if len(set(task.depends_on)) != len(task.depends_on):
            raise ValueError("Duplicate dependencies")
        if task.task_id in task.depends_on or not set(task.depends_on) <= tasks.keys():
            raise ValueError("Task has a self or missing dependency")
        covered.update(task.requirement_ids)
    if covered != request.requirements.keys():
        raise ValueError("Some requirements have no planned task")
    order: list[str] = []
    ancestors: dict[str, set[str]] = {}
    while len(order) < len(tasks):
        ready = sorted(
            k for k, t in tasks.items() if k not in order and set(t.depends_on) <= set(order)
        )
        if not ready:
            raise ValueError("Cyclic task dependencies")
        for key in ready:
            ancestors[key] = set(tasks[key].depends_on)
            for dep in tasks[key].depends_on:
                ancestors[key].update(ancestors[dep])
            order.append(key)
    for i, left in enumerate(order):
        for right in order[i + 1 :]:
            overlap = any(
                within(a, (b,)) or within(b, (a,))
                for a in tasks[left].writable_paths
                for b in tasks[right].writable_paths
            )
            if overlap and left not in ancestors[right]:
                raise ValueError("Overlapping writable scopes need an explicit dependency")
    return tuple(order)


def _source_interfaces(request: FeatureRequest) -> dict[str, list[str]]:
    """Bounded navigation hints derived from this exact source, never instructions."""
    result: dict[str, list[str]] = {}
    remaining = 2048
    for path in sorted(request.source.files):
        if not path.endswith(".py") or not within(path, request.allowed_paths):
            continue
        try:
            tree = ast.parse(request.source.files[path])
        except (SyntaxError, RecursionError):
            continue
        signatures = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                signatures.append(node.name + "(" + ast.unparse(node.args)[:160] + ")")
            elif isinstance(node, ast.ClassDef):
                signatures.append("class " + node.name)
        entry = signatures[:12]
        size = len(path) + sum(map(len, entry))
        if size > remaining:
            continue
        result[path] = entry
        remaining -= size
    return result


def draft_feature(
    request: FeatureRequest, profile: ModelProfile, output: Path, *, deployment: str
) -> dict[str, Any]:
    """Create one non-resumable, bounded proposal run with immutable model evidence.

    Existing directories are refused. Interrupted runs retain observations but are
    not silently resumed or rescored. A draft is never a Work-atom acceptance.
    """
    request = FeatureRequest.model_validate(request)
    profile = ModelProfile.model_validate(profile)
    if profile.profile_id != "vllm-python-worker-v1":
        raise ValueError("Planning v1 uses the default non-thinking profile with fixed 4K output")
    if hashlib.sha256(deployment.encode()).hexdigest() != profile.deployment_digest:
        raise ValueError("Deployment does not match pinned model profile")
    output.mkdir(parents=True, exist_ok=False)
    artifacts = ArtifactStore(output / "artifacts")
    artifacts.publish(deployment.encode())
    artifacts.publish(request.canonical().encode())
    source_digest = artifacts.publish(request.source.canonical().encode())
    brief = {
        "request_digest": request.digest(),
        "source_interfaces": _source_interfaces(request),
        "objective": request.objective,
        "requirements": request.requirements,
        "allowed_paths": request.allowed_paths,
        "environments": {k: v.model_dump(mode="json") for k, v in request.environments.items()},
    }
    instruction = (
        "Inspect the supplied repository and propose a bounded implementation plan, not code. "
        "Only the two most recently selected source files are retained after reads. The source "
        "interface index is navigation data from the pinned source; inspect files as needed. "
        "There are only three turns per attempt, so submit the proposal after at most two reads. "
        "Return a candidate containing only factory-plan.json, whose contents follow this schema. "
        "Split tasks only when independently testable. Include tests and documentation work where "
        "needed. Cover every requirement with meaningful acceptance checks. State exact provider "
        "interfaces and order consumers after providers. Each interface_contract must state "
        "the proposed AFTER-change signature, with matching parameter names for consumers, "
        "not merely list existing functions. Environments are a trusted catalog; "
        "select an existing environment, never invent install commands. Questions must list "
        "blocking scope or correctness decisions only. Choose routine presentation details "
        "consistently with the repository and state those choices in rationale, rather than "
        "asking about every formatting detail. Do not invent product requirements. "
        "Check source before "
        "claiming an interface exists. Plans are drafts for review, not execution permission. "
        + json.dumps(brief, separators=(",", ":"))
        + "\nSchema: "
        + json.dumps(PlanProposal.model_json_schema(), separators=(",", ":"))
    )
    atom = WorkAtom.model_validate_json(
        json.dumps(
            dict(
                atom_id=request.feature_id,
                graph_revision="feature-planning-v2",
                objective=instruction,
                non_goals=[
                    "Execute proposed tasks",
                    "Change source",
                    "Approve own acceptance checks",
                ],
                requirement_ids=list(request.requirements),
                product_modules=["planning"],
                source_revision=request.source_revision,
                inputs_digest=InputSnapshot(
                    source_digest=source_digest, source_revision=request.source_revision
                ).digest(),
                writable_paths=["factory-plan.json"],
                prohibited_paths=[],
                dependency_artifacts=[],
                upstream_contracts=[],
                capability_profile="python-pilot-v1",
                network_profile="none-v1",
                credential_profile="none-v1",
                sandbox_profile="pilot-v1",
                allowed_tools=["read", "edit"],
                required_gates=[
                    {
                        "gate_id": "proposal-structure",
                        "validator_digest": artifacts.publish(Path(__file__).read_bytes()),
                    }
                ],
                context_budget={"total_tokens": 12288, "output_tokens": 4096},
                max_attempts=2,
                expected_outputs=[
                    {
                        "name": "proposal",
                        "schema_digest": artifacts.publish(
                            json.dumps(PlanProposal.model_json_schema(), sort_keys=True).encode()
                        ),
                    }
                ],
                idempotency_key=request.feature_id,
                integration_key="planning-draft-only",
            )
        )
    )
    artifacts.publish(atom.canonical().encode())
    manifest = {
        "request_digest": request.digest(),
        "atom_digest": atom.digest(),
        "profile": profile.model_dump(mode="json"),
        "max_attempts": 2,
        "max_turns_per_attempt": 3,
        "context_budget": {"total_tokens": 12288, "output_tokens": 4096},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    model = LocalModel(artifacts, profile)
    observations: list[dict[str, Any]] = []
    diagnostics: tuple[str, ...] = ()
    result: dict[str, Any] = {
        "status": "exhausted",
        "proposal_digest": None,
        "execution_authorized": False,
    }
    try:
        for attempt in range(1, 3):
            selected = set(request.selected_paths[-2:])
            reading_order = list(request.selected_paths[-2:])
            failure = "Planning turn budget exhausted before a proposal"
            for turn in range(1, 4):
                row: dict[str, Any] = {"attempt": attempt, "turn": turn}
                try:
                    response = model.turn(
                        atom,
                        source_digest,
                        current_inputs=lambda: atom.inputs_digest,
                        selected_paths=tuple(sorted(selected)),
                        diagnostic_digests=diagnostics,
                    )
                    answer = response.result
                    if isinstance(answer, ReadFileRequest):
                        if answer.path in selected or answer.path not in request.source.files:
                            raise ValueError("Read must select an existing omitted source file")
                        selected.add(answer.path)
                        reading_order.append(answer.path)
                        if len(reading_order) > 2:
                            evicted = reading_order.pop(0)
                            selected.remove(evicted)
                            row["evicted_path"] = evicted
                        row["read_path"] = answer.path
                        continue
                    if not isinstance(answer, CandidateResult) or set(answer.changes) != {
                        "factory-plan.json"
                    }:
                        raise ValueError("Only factory-plan.json may be proposed")
                    proposal = PlanProposal.model_validate_json(answer.changes["factory-plan.json"])
                    order = validate_proposal(request, proposal)
                    digest = artifacts.publish(proposal.canonical().encode())
                    result.update(
                        status="needs-review",
                        proposal_digest=digest,
                        task_order=list(order),
                        questions=list(proposal.questions),
                    )
                    (output / "proposal.json").write_text(proposal.canonical() + "\n")
                    return result
                except (ModelError, ArtifactError):
                    result["status"] = "infrastructure-halt"
                    raise
                except ValueError as error:
                    failure = str(error)[:2048]
                    row["error"] = failure
                    break
                finally:
                    row["model_evidence_digest"] = model.last_evidence_digest
                    digest = artifacts.publish(json.dumps(row, sort_keys=True).encode())
                    observations.append(row | {"observation_digest": digest})
                    (output / f"observation-{attempt}-{turn}.json").write_text(
                        json.dumps(row, indent=2) + "\n"
                    )
            raw = artifacts.publish(failure.encode())
            diagnostic = Diagnostic(source_digest=raw, text=failure)
            diagnostics = (artifacts.publish(diagnostic.canonical().encode()),)
        return result
    except BaseException:
        if result["status"] != "infrastructure-halt":
            result["status"] = "interrupted"
        raise
    finally:
        result["observations"] = observations
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
