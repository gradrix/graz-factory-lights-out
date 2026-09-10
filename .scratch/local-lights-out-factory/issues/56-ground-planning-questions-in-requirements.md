# Ground planning questions in original requirements

Type: task
Status: resolved

## Evidence

After issue 55's complete modes acceptance, a fresh same-model repeat stopped with
8 questions already answered by the original selection/tests requirements. See
contracts-qualification-results.json run leds-modes-contracts-v5 and raw
.gflo/evidence/leds-modes-contracts-v5. No worker executed or target edit shipped.
This does not require new human product policy.

## Scope

Design a bounded, evidence-retaining way to check whether proposed questions are
already answered in the immutable request. Preserve genuine missing-policy stops,
finite planning budgets, legacy identities and independent gates. Do not manually
answer the known task, silently remove questions, or invent product policy. Qualify
against both this seen redundant-question case and actual ambiguous requests, then
repeat complete features. No model/deployment change is authorized.


## Answer

Implemented one bounded question-grounding review for structured planning. It uses
only original requirements, with source reads disabled, and checks request/question
bindings, exact quote provenance and complete disposition coverage. Any unresolved,
invalid or repeated question set retains needs-info. A covered set can replan within
the same two-attempt/three-turn limits; quotes and subsequent schema diagnostics both
remain available. Quote provenance is deterministic; semantic coverage is still model
judgment and never acceptance authority.

Live qualification: fresh modes build accepted; seeded replay of the exact earlier
8-question failure grounded all questions and accepted the complete feature after a
planning coverage retry. No answers, target code or plan corrections supplied by Codex.
Two genuinely missing-policy fixtures (retention and rounding) stayed needs-info in
both reviewer iterations. Initial replay failures (source-read request, then planning
schema failure with dropped feedback) remain retained and motivated the final fixes.
480 factory tests/25 subtests with Docker pass; all 28 target tests pass together;
ruff/mypy and historical replay pass. No model/deployment/gate changes or target PR.

Portable evidence: question-grounding-feature-results.json,
question-grounding-ambiguity-results.json, question-grounding-combined-results.json.
Raw campaigns: .gflo/evidence/question-grounding-v1 through v3; fresh build:
.gflo/evidence/leds-modes-grounding-v1. Seeded campaigns deliberately replay the prior
question record as their first observation without a GPU call, then use real LocalModel
for all review/planning/coding. This is targeted regression evidence, not a fully fresh
unattended success-rate estimate.

Issue 57 follows the user's large-file concern: indexing found a two-line function in
10,002 lines, but whole-file worker context was 128,684 tokens and correctly refused.
Bounded source-window editing is not implemented yet.
