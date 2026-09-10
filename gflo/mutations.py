"""Bounded Python fault proposals and sandboxed reference-test qualification."""

from __future__ import annotations

import ast
import copy
import hashlib
import re
from typing import Any, cast

from gflo.broker import DockerBroker
from gflo.test_adequacy import FaultyVariant, pytest_adequacy_gate


def propose_faults(
    module: str, source: str, function: str, *, limit: int = 8
) -> tuple[FaultyVariant, ...]:
    """Propose deterministic single-site mutations, never execute source.

    Function is a top-level name or Class.method. Operators negate conditions,
    invert comparisons, and remove zero-argument method calls. Proposals may be
    equivalent or invalid at runtime; reference qualification is mandatory.
    """
    if not re.fullmatch(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*", module):
        raise ValueError("Require a Python module name")
    if not 1 <= limit <= 8 or len(source.encode()) > 32768:
        raise ValueError("Mutation input exceeds bounds")
    tree = ast.parse(source)
    nodes = tree.body
    target: ast.AST = tree
    for name in function.split("."):
        matches = [
            n
            for n in nodes
            if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == name
        ]
        if len(matches) != 1:
            raise ValueError("Function selection is missing or ambiguous")
        target = matches[0]
        nodes = target.body
    if not isinstance(target, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise ValueError("Select a function, not a class")
    inverse = {
        ast.Eq: ast.NotEq,
        ast.NotEq: ast.Eq,
        ast.Lt: ast.GtE,
        ast.LtE: ast.Gt,
        ast.Gt: ast.LtE,
        ast.GtE: ast.Lt,
        ast.Is: ast.IsNot,
        ast.IsNot: ast.Is,
        ast.In: ast.NotIn,
        ast.NotIn: ast.In,
    }
    proposals = []
    # Source order makes a bounded prefix stable across runs on the same Python version.
    sites = sorted(
        ast.walk(target),
        key=lambda n: (getattr(n, "lineno", 0), getattr(n, "col_offset", 0), type(n).__name__),
    )
    for site in sites:
        replacement: ast.AST
        operator: str
        if (
            isinstance(site, ast.Call)
            and isinstance(site.func, ast.Attribute)
            and (not site.args and not site.keywords)
        ):
            replacement = copy.deepcopy(site.func.value)
            operator = "remove-call"
        elif isinstance(site, ast.Compare) and len(site.ops) == 1 and type(site.ops[0]) in inverse:
            replacement = copy.deepcopy(site)
            replacement.ops = [inverse[type(site.ops[0])]()]
            operator = "invert-comparison"
        elif isinstance(site, ast.If):
            replacement = copy.deepcopy(site)
            replacement.test = ast.UnaryOp(op=ast.Not(), operand=replacement.test)
            operator = "negate-condition"
        else:
            continue

        cloned = copy.deepcopy(tree)
        index = next(i for i, node in enumerate(ast.walk(tree)) if node is site)
        selected_site = list(ast.walk(cloned))[index]

        class Replace(ast.NodeTransformer):
            def visit(self, node: ast.AST) -> ast.AST:
                if node is selected_site:
                    return replacement
                return cast(ast.AST, super().visit(node))

        mutated = Replace().visit(cloned)
        ast.fix_missing_locations(mutated)
        content = ast.unparse(mutated) + "\n"
        compile(content, "<mutation>", "exec")
        digest = hashlib.sha256(content.encode()).hexdigest()
        proposals.append(
            FaultyVariant(
                name=f"{operator}-{site.lineno}-{site.col_offset}-{digest[:12]}",
                modules={module: content},
            )
        )
        if len(proposals) == limit:
            break
    return tuple(proposals)


def qualify_faults(
    broker: DockerBroker,
    reference_bundle_digest: str,
    tests: tuple[str, ...],
    variants: tuple[FaultyVariant, ...],
    *,
    minimum_tests: int = 1,
) -> dict[str, Any]:
    """Caller owns reference tests and source; preserve every sandbox outcome.

    Selected variants are faults relative to those tests only. A failed check is
    unqualified, not proof of equivalence. This creates no work acceptance receipt.
    """
    if not variants or len(variants) > 8 or len({v.name for v in variants}) != len(variants):
        raise ValueError("Require one to eight uniquely named variants")
    # Validate all plans before executing anything.
    plans = [pytest_adequacy_gate(tests, (v,), minimum_tests=minimum_tests) for v in variants]
    if broker.qualification_digest is None or not broker.image_id:
        raise ValueError("Qualify the broker before fault validation")
    broker.artifacts.verify(broker.qualification_digest)
    outcomes = []
    containers: set[str] = set()
    for variant, plan in zip(variants, plans, strict=True):
        case = plan.cases[0]
        execution = broker.execute(
            reference_bundle_digest,
            case.command,
            stdin=case.stdin,
            seconds=case.seconds,
            purpose="validation",
        )
        if (
            execution.candidate_digest != reference_bundle_digest
            or execution.command != case.command
            or execution.stdin != case.stdin
            or execution.purpose != "validation"
            or execution.image_id != broker.image_id
            or execution.container_id in containers
        ):
            raise ValueError("Fault qualification execution does not bind its inputs")
        containers.add(execution.container_id)
        selected = (
            execution.outcome == "completed"
            and execution.exit_code == 0
            and not execution.oom_killed
            and execution.stdout == case.expected_stdout.encode()
        )
        outcomes.append(
            dict(
                variant=variant.model_dump(mode="json"),
                selected=selected,
                gate=plan.model_dump(mode="json"),
                gate_digest=plan.digest(),
                execution=execution.model_dump(mode="json"),
            )
        )
    report = dict(
        schema_version=1,
        kind="fault-qualification-v1",
        reference_bundle_digest=reference_bundle_digest,
        qualification_digest=broker.qualification_digest,
        outcomes=outcomes,
    )
    import json

    digest = broker.artifacts.publish(json.dumps(report, sort_keys=True).encode())
    return {**report, "evidence_digest": digest}
