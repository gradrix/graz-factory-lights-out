# Execute features under pinned policy

Type: task
Status: resolved

## Requirement

Close the manual proposal-to-review handoff for bounded snapshot features. A trusted,
request-bound policy supplies exact writable-file checks, execution inputs, pinned
environment and model, integration gates, and finite budgets before planning.
Compile a generated task graph into the existing reviewed FeaturePlan without taking
commands or authority from model prose. Provide one build command with retained
planning, deterministic compilation, execution replay, and explicit halts.

## Qualification

Reject missing file checks, stale requests, scope expansion, unsupported inputs,
questions, and budgets before execution. Verify resumed builds do not replan or
repeat accepted work. Exercise actual local planning and workers with independent
behavior checks; preserve failed trials. This is bounded policy-driven autonomy,
not arbitrary product intake, generated test authority, environment provisioning,
or automatic Git promotion. Single planner remains the default.

## Answer

Implemented request-bound FeaturePolicy compilation and `build-feature`, retaining
existing execution/review contracts and independent gates. Local checkout build
passed three tasks in three attempts and final validation, without editing the
model's proposal; planning used its second allowed attempt. Replay added no model
calls. Ambiguity halted with questions before execution. Fifteen regression cases
cover authority rejection, policy halts, and replay/interruption; full suite 375
passed, eight optional skips, 25 subtests. See [results](../policy-build-results.json),
[fixture](../policy-build-fixture.json), and [guide](../../../docs/product-intake.md).

## Comments

Owner clarified that the next useful engineering step takes priority over autonomy
as a label. Finish this concrete handoff gap, then return to product/navigation
qualification and indexing rather than adding speculative orchestration.
