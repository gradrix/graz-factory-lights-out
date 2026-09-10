# Ground planning questions in original requirements

Type: task
Status: ready-for-agent

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
