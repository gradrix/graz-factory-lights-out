"""Structured planner declarations; implementation advice cannot become worker authority."""

from __future__ import annotations

import ast
from typing import Annotated, Literal

from pydantic import Field, model_validator

from gflo.records import Digest, Identifier, Record, Text

CONTRACT_PROFILE = "vllm-python-worker-contracts-v1"
DEPENDENCY_CONTRACT_PROFILE = "vllm-python-worker-contracts-v2"
WINDOW_PROFILE = "vllm-python-worker-windows-v1"
CONTRACT_PROFILES = (CONTRACT_PROFILE, DEPENDENCY_CONTRACT_PROFILE, WINDOW_PROFILE)


class InterfaceDeclaration(Record):
    path: Text
    symbol: Identifier
    declaration: Annotated[str, Field(min_length=1, max_length=2048)]
    requirement_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=16)]

    @model_validator(mode="after")
    def signature_only(self) -> InterfaceDeclaration:
        try:
            tree = ast.parse(self.declaration)
        except SyntaxError as exc:
            raise ValueError("Invalid Python declaration") from exc
        if len(tree.body) != 1 or not isinstance(
            tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            raise ValueError(
                "Declaration must be one Python function signature with an ellipsis body"
            )
        fn = tree.body[0]
        if (
            fn.decorator_list
            or len(fn.body) != 1
            or not (
                isinstance(fn.body[0], ast.Pass)
                or isinstance(fn.body[0], ast.Expr)
                and isinstance(fn.body[0].value, ast.Constant)
                and fn.body[0].value.value is Ellipsis
            )
        ):
            raise ValueError("Interface declarations cannot contain implementation or decorators")
        if fn.name != self.symbol.rsplit(".", 1)[-1]:
            raise ValueError("Declaration name differs from symbol")
        # Defaults/annotations are syntax only: never execute planner declarations.
        if any(isinstance(n, (ast.Call, ast.Lambda, ast.NamedExpr)) for n in ast.walk(fn)):
            raise ValueError("Declarations cannot contain executable argument expressions")
        return self


class ContractTask(Record):
    task_id: Identifier
    objective: Annotated[str, Field(min_length=1, max_length=2048)]
    requirement_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=16)]
    depends_on: Annotated[tuple[Identifier, ...], Field(max_length=12)]
    writable_paths: Annotated[tuple[str, ...], Field(min_length=1, max_length=16)]
    read_paths: Annotated[tuple[str, ...], Field(max_length=32)]
    environment_id: Identifier
    interfaces: Annotated[tuple[InterfaceDeclaration, ...], Field(max_length=16)]
    implementation_suggestions: Annotated[tuple[Text, ...], Field(max_length=8)]
    acceptance_checks: Annotated[tuple[Text, ...], Field(min_length=1, max_length=16)]


class ContractProposal(Record):
    kind: Literal["contract-plan-v1"] = "contract-plan-v1"
    request_digest: Digest
    tasks: Annotated[tuple[ContractTask, ...], Field(min_length=1, max_length=12)]
    questions: Annotated[tuple[Text, ...], Field(max_length=16)]
    rationale: Annotated[str, Field(min_length=1, max_length=4096)]


class InterfaceBundle(Record):
    kind: Literal["interface-declarations-v1"] = "interface-declarations-v1"
    declarations: Annotated[tuple[InterfaceDeclaration, ...], Field(max_length=16)]


def task_interfaces(
    contracts: tuple[str, ...], paths: tuple[str, ...], requirements: tuple[str, ...]
) -> list[dict[str, object]]:
    """Validate the typed boundary again when preparing execution authority."""
    if len(contracts) != 1:
        raise ValueError("Structured contracts require one interface declaration bundle")
    bundle = InterfaceBundle.model_validate_json(contracts[0])
    seen = set()
    for declaration in bundle.declarations:
        key = (declaration.path, declaration.symbol)
        if key in seen:
            raise ValueError("Duplicate interface declaration")
        seen.add(key)
        if declaration.path not in paths:
            raise ValueError("Interface path is outside task inputs and outputs")
        if not set(declaration.requirement_ids) <= set(requirements):
            raise ValueError("Interface cites an unknown task requirement")
    return [d.model_dump(mode="json") for d in bundle.declarations]
