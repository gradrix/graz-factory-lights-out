"""Portable example data verified by an explicitly supplied trusted oracle."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, Literal

from pydantic import Field

from gflo.records import Digest, Record


class Example(Record):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    inputs: dict[str, Any]
    expected: dict[str, Any]


class VerifiedExamples(Record):
    kind: Literal["verified-examples-v1"] = "verified-examples-v1"
    producer_digest: Digest
    examples: Annotated[tuple[Example, ...], Field(min_length=1, max_length=64)]


def verify_examples(
    examples: tuple[Example, ...],
    *,
    producer_digest: str,
    oracle: Callable[[dict[str, Any]], dict[str, Any]],
) -> VerifiedExamples:
    """The caller owns the oracle; model output cannot choose or execute one."""
    result = VerifiedExamples(producer_digest=producer_digest, examples=examples)
    if len(result.canonical().encode()) > 32768:
        raise ValueError("Verified examples exceed the bounded data allowance")
    if len({e.name for e in examples}) != len(examples):
        raise ValueError("Example names must be unique")
    for example in examples:
        # Canonical bytes avoid Python's True == 1 ambiguity and isolate input mutation.
        import json

        observed = oracle(json.loads(json.dumps(example.inputs)))
        if json.dumps(observed, sort_keys=True) != json.dumps(example.expected, sort_keys=True):
            raise ValueError("Oracle rejected example: " + example.name)
    return result
