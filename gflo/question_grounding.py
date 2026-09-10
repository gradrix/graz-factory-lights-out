"""Provenance checks for bounded reconsideration of planning questions."""

from __future__ import annotations

import json
from typing import Annotated, Literal

from pydantic import Field

from gflo.records import Digest, Identifier, Record


class RequirementQuote(Record):
    requirement_id: Identifier
    quote: Annotated[str, Field(min_length=12, max_length=2048)]


class QuestionDisposition(Record):
    question_index: Annotated[int, Field(ge=0, le=15)]
    quotes: Annotated[tuple[RequirementQuote, ...], Field(max_length=4)]


class QuestionGrounding(Record):
    kind: Literal["question-grounding-v1"] = "question-grounding-v1"
    request_digest: Digest
    questions_digest: Digest
    dispositions: Annotated[tuple[QuestionDisposition, ...], Field(min_length=1, max_length=16)]

    def covered(
        self,
        request_digest: str,
        questions_digest: str,
        questions: tuple[str, ...],
        requirements: dict[str, str],
    ) -> bool:
        if self.request_digest != request_digest or self.questions_digest != questions_digest:
            raise ValueError("Question grounding binds another request or question set")
        indices = [d.question_index for d in self.dispositions]
        if sorted(indices) != list(range(len(questions))):
            raise ValueError("Grounding must account for every question exactly once")
        for disposition in self.dispositions:
            for citation in disposition.quotes:
                requirement = requirements.get(citation.requirement_id)
                if requirement is None or citation.quote not in requirement:
                    raise ValueError("Grounding quote is not exact original requirement text")
        return all(d.quotes for d in self.dispositions)


def grounding_instruction(
    request_digest: str,
    questions_digest: str,
    questions: tuple[str, ...],
    requirements: dict[str, str],
) -> str:
    return (
        "Review proposed planning questions against ONLY the immutable original requirements. "
        "For each question, cite exact requirement text only if it fully answers that question. "
        "Use an empty quotes list if policy is missing, ambiguous or only partially answered. "
        "Do not infer missing business policy from implementation, conventions or related text. "
        "Do not invent an answer, rewrite a requirement or propose a plan. Preserve genuine "
        "uncertainty. Every question needs one disposition using its zero-based index. "
        "Return one direct question-grounding-v1 JSON document matching the schema. "
        + json.dumps(
            dict(
                request_digest=request_digest,
                questions_digest=questions_digest,
                questions=questions,
                requirements=requirements,
            ),
            separators=(",", ":"),
        )
        + "\nSchema: "
        + json.dumps(QuestionGrounding.model_json_schema(), separators=(",", ":"))
    )
