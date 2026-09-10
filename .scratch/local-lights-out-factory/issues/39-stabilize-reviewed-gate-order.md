# Stabilize reviewed gate order across policy serialization

Type: task
Status: resolved

## Observed failure

Issue 38's builds passed, but canonical policy reload changed final validation gate
order while preserving the policy/plan digest. Replay rejected the resulting WorkAtom
as a different contract under the same ID. Two minimal regression cases reproduce
this for task gates and integration gates.

## Requirement

Make new reviewed materialization deterministic across equivalent JSON mapping order.
Preserve existing historical gate order for exact replay without permitting any gate,
input, source, budget or contract changes. Retain the observed failure and verify all
three existing live ledgers after the fix; do not reset or silently rerun accepted work.

## Answer

Sorted new derived required-gate lists in preparation and final validation. Replay
uses the retained historical order only after verifying the exact gate specifications
and equality of every other WorkAtom field. No historical contract or acceptance is
rewritten. Four regression cases passed, including migration and rejected policy/budget
changes. All three settings ledgers replayed without additional calls, as did both
older board-comparison ledgers. Full Docker-enabled suite: 406 passed, 25 subtests.
See [retained results](../navigation-feature-results.json).
