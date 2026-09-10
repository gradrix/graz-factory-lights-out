# Add reusable behavior-sensitive pytest gates

Type: task
Status: resolved

## Scope

Compile operator-owned faulty module variants into one pinned ProcessGate that checks
candidate tests first, then requires genuine assertion failures on each variant.
Reject collection/runtime errors, skips, missing tests and surviving variants. Run
isolated interpreter processes; retain ordinary process-gate receipts and bounded
worker development feedback. No new acceptance authority or model change.

Qualify on retained weak leds-service tests and repaired tests, then run a fresh local
repair with the generic gate frozen before execution. Explicitly record seen-task
assistance and limits: trusted variants still require preparation.

## Answer

Implemented gflo.test_adequacy.pytest_adequacy_gate and documented policy integration.
The ordinary pinned ProcessGate runs candidate tests and trusted variants in fresh
interpreters. Fourteen targeted tests cover behavioral rejection, vacuous assertions,
errors, skipped/expected-failure tests, collection-time skips, source identity and
path validation. No model or scheduler changes.

Retained weak leds tests are rejected; repaired tests pass. Two fresh same-instruction
local trials passed first response, the second after tightening collection-skip
handling (2569 prompt/467 output tokens, 8.19s). Both replay without model calls.
Independent parser oracle passes. No further product edits were published.

[Results](../generic-test-adequacy-results.json) retain both trials. Full suite before
final collection-skip addition: 428 passed, 8 optional Docker skips, 25 subtests;
Docker broker checks separately: 49 passed. Final targeted suite: 14 passed; ruff and
mypy pass. Trusted fault selection remains necessary; no automatic discovery claim.
