# Qualify bounded specialist-board planning

Type: task
Status: resolved

## Requirement

Implement four independent specialist reports (product, architecture, validation,
operations) and one coordinator against the same immutable request/source selection.
Bound reports, calls, and synthesis. Preserve every finding and disagreement;
unresolved specialist questions/blockers cannot become an executable plan.
Keep model advice separate from trusted review/gates. Compare single planning and
board planning on identical unfamiliar compatibility-sensitive features, with an
unresolved-policy variant. Retain cost, failures, and downstream execution results.
Do not introduce recursive delegation until the comparison justifies it.

## Comparison contract

Before scoring: use the same new checkout-quote feature, snapshot, four context
files, model profile, and per-call budgets. Preserve legacy.total without editing
legacy.py; verify exact integer rounding, validation, API and CLI integration.
Specified requests must produce usable plans with no invented blocking decisions.
The ambiguity variant explicitly withholds the rounding policy; both modes must
request clarification and authorize no execution. Supply identical controller-owned
gates for both resulting specified plans, then run complete feature validation.
Report all model calls/tokens/time, including failed stages. A tied result does not
justify promoting the board to default. One feature is an exploratory comparison,
not a statistical generalization or proof of independent model opinions.

The owner asked whether this drifts from SFLO/Gas City. The existing foundation
research explicitly selected an independent small core borrowing their contracts.
The board stays optional planning policy above that core; execution and acceptance
remain unchanged. Do not add a recursive organization based on this metaphor alone.

## Answer

Implemented optional bounded specialist planning with deterministic early escalation,
complete finding dispositions for synthesis, retained per-stage evidence, and no
execution authority. Single remains default: both compact specified plans passed
three tasks in three attempts, while board planning consumed 29,628 versus 8,294
tokens. Initial failures and failed ambiguous synthesis remain separate observations;
early escalation subsequently returned questions in one live call. This does not
justify recursive delegation or a default board. See [results](../board-comparison-results.json),
[portable fixture](../board-comparison-fixture.json), and
[evaluation](../../../docs/evaluation.md). Full suite: 360 passed, eight optional
Docker skips, 25 subtests; ruff/mypy passed.
