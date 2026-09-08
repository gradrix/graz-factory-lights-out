"""Versioned, strict ledger contracts; no product-language assumptions."""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
Identifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,199}$")]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
Version = Annotated[int, Field(ge=1, le=1)]


class Record(BaseModel):
    model_config = ConfigDict(
        strict=True, frozen=True, extra="forbid", revalidate_instances="always"
    )
    schema_version: Version = 1

    def canonical(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return hashlib.sha256(self.canonical().encode()).hexdigest()


class GateSpec(Record):
    gate_id: Identifier
    validator_digest: Digest


class OutputSpec(Record):
    name: Identifier
    schema_digest: Digest


class ContextBudget(Record):
    total_tokens: Annotated[int, Field(gt=0)]
    output_tokens: Annotated[int, Field(gt=0)]

    @model_validator(mode="after")
    def reserve_input(self) -> Self:
        if self.output_tokens >= self.total_tokens:
            raise ValueError("Context budget must leave room for input")
        return self


class WorkAtom(Record):
    atom_id: Identifier
    graph_revision: Identifier
    objective: Text
    non_goals: tuple[Text, ...]
    requirement_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    product_modules: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    source_revision: Text
    # Digest of the controller's complete precondition manifest, not model prose.
    inputs_digest: Digest
    writable_paths: Annotated[tuple[Text, ...], Field(min_length=1)]
    prohibited_paths: tuple[Text, ...]
    dependency_artifacts: tuple[Digest, ...]
    upstream_contracts: tuple[Digest, ...]
    capability_profile: Identifier
    network_profile: Identifier
    credential_profile: Identifier
    sandbox_profile: Identifier
    allowed_tools: tuple[Identifier, ...]
    required_gates: Annotated[tuple[GateSpec, ...], Field(min_length=1)]
    context_budget: ContextBudget
    max_attempts: Annotated[int, Field(ge=1, le=10)]
    expected_outputs: Annotated[tuple[OutputSpec, ...], Field(min_length=1)]
    idempotency_key: Identifier
    integration_key: Identifier

    @model_validator(mode="after")
    def unambiguous_contract(self) -> Self:
        for paths in (self.writable_paths, self.prohibited_paths):
            for path in paths:
                if (
                    path.startswith("/")
                    or "\\" in path
                    or any(part in ("", ".", "..") for part in path.split("/"))
                ):
                    raise ValueError("Scope paths must be normalized relative paths")
        for values in (
            self.requirement_ids,
            self.product_modules,
            self.writable_paths,
            self.prohibited_paths,
            self.allowed_tools,
            tuple(g.gate_id for g in self.required_gates),
            tuple(o.name for o in self.expected_outputs),
        ):
            if len(set(values)) != len(values):
                raise ValueError("Duplicate contract entries are ambiguous")
        return self


class Lease(Record):
    atom_id: Identifier
    attempt_id: Identifier
    token: Identifier
    owner: Identifier
    expires_at: Annotated[float, Field(allow_inf_nan=False, gt=0)]


class RetryPlan(Record):
    failure_event: Annotated[int, Field(gt=0)]
    strategy: Text
    new_evidence: Digest | None = None


class GateEvidence(Record):
    """Normalized receipt supplied only by a trusted runner, never a WorkerResult.

    The ledger verifies stored evidence bytes and receipt bindings. Validator
    execution and interpretation remain the trusted runner's responsibility.
    """

    attempt_id: Identifier
    contract_digest: Digest
    inputs_digest: Digest
    candidate_digest: Digest
    gate_id: Identifier
    validator_digest: Digest
    outcome: Literal["pass", "fail", "inconclusive"]
    evidence_digest: Digest
    runner_id: Identifier


class Acceptance(Record):
    atom_id: Identifier
    attempt_id: Identifier
    contract_digest: Digest
    inputs_digest: Digest
    candidate_digest: Digest
    gate_receipts: Annotated[tuple[Digest, ...], Field(min_length=1)]


class AcceptanceFinding(Record):
    """Trusted contradictory evidence; historical acceptance remains immutable."""

    atom_id: Identifier
    contract_digest: Digest
    candidate_digest: Digest
    evidence_digest: Digest
    reason: Annotated[Text, Field(max_length=8192)]
