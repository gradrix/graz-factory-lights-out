# Keep policy planning non-thinking while allowing qualified worker profiles

Type: task
Status: resolved

## Observed gap

The first ai-gamer worker attempt corrected contiguous wins but omitted potential
checks; the second repeated a read and quarantined. Policy builds pass the worker
profile directly to planning, which only supports non-thinking. Existing reasoning
workers therefore cannot be used through this entry point.

## Requirement

Derive the planner's existing non-thinking profile from the same pinned model and
deployment, while retaining the explicitly selected worker profile in PlanReview.
Plain-worker policies and their identities remain unchanged. Do not loosen existing
escalation budget contracts. The ai-gamer input is too large for the fixed 8K/4K
escalation contract, so qualify the existing reasoning worker at its explicit 12K/4K
budget instead. Preserve the first failed run and compare follow-up separately.


## Follow-up evidence

The standalone default-reasoning trial exhausted all 4,096 output tokens in reasoning
without a candidate (`finish_reason=length`). Added an explicit standalone
`vllm-python-worker-reasoning-low-v1` profile using the backend's already-supported
low reasoning effort, independently of the legacy fixed-budget escalation profiles.
Its tokenizer and generation templates must match and reserve the explicit worker
contract output. The next trial keeps the 12K/4K budget and all trusted checks.

## Answer

Planning now derives the existing plain profile on the same pinned deployment;
compiled worker reviews retain the selected profile. The standalone low-reasoning
profile uses identical tokenizer/generation templates and explicit context budgets.
Existing escalation contracts and default policies are unchanged. Full factory
suite passed 410 tests and 25 subtests with Docker checks enabled; ruff/mypy passed.

The 12K/4K low-reasoning trial also truncated. At 12K/6K the implementation passed
the independent oracle on its second attempt, but both test attempts consumed all
6,144 output tokens reasoning. Reasoning is therefore not a globally qualified
replacement default. Test generation proceeds as a separate plain-worker follow-up.
