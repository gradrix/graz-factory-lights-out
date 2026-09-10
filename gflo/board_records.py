"""Bounded advisory records; specialist agreement grants no execution authority."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from gflo.records import Digest, Identifier, Record

Role = Literal["product", "architecture", "validation", "operations"]
ROLES: tuple[Role, ...] = ("product", "architecture", "validation", "operations")
ShortText = Annotated[str, Field(min_length=1, max_length=1200)]


class BoardFinding(Record):
    finding_id: Identifier
    requirement_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=16)]
    severity: Literal["blocker", "concern", "suggestion"]
    observation: ShortText
    recommendation: ShortText
    source_paths: Annotated[tuple[str, ...], Field(max_length=4)]


class SpecialistReport(Record):
    kind: Literal["specialist-report-v1"] = "specialist-report-v1"
    request_digest: Digest
    role: Role
    findings: Annotated[tuple[BoardFinding, ...], Field(max_length=6)]
    questions: Annotated[tuple[ShortText, ...], Field(max_length=4)]
    summary: ShortText
