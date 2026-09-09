# Qualify the stateful inventory workload

Type: task
Status: resolved
Blocked by: 27

## Scope

The provider/CLI/report API-migration slice passed with three first-attempt local
repairs, independent combined gates, stale-input rejection, restart idempotence,
and a synthetic finding probe in a separate ledger copy.

Prepare ten bounded changes over a small standard-library SQLite application:
quantity validation, persistent storage, reservation transitions, request replay,
cancellation, CLI, reporting, audit export, provider API revision, and migration of
both consumers. A trusted harness advances immutable source bases only after
checking the previous acceptance; this is not autonomous product planning.

Freeze specifications, reference controls, independent workflow oracles, and gates
before inference. Run three fresh builds. Use the qualified two-attempt profile:
2K non-thinking followed by at most one 4K low-effort reasoning attempt. This
replaces the earlier proposed three-attempt routine budget prospectively: at most
60 model turns across 30 atoms, with no automatic infrastructure retry.

Whole-build success requires every step and all final process-workflow gates.
Require all three complete builds and zero discovered false acceptances. Partial
builds remain failed builds. Stop progression on a failing build and retain its
partial artifacts rather than filling gaps manually.

## Progress

The first frozen build stopped at reservation (a dependency helper was scheduled
too late). A separately frozen dependency-ordered build passed reservation, then
stopped at audit export (the public output schema omitted an explicit field list).
An explicit-schema build passed audit and stopped at CLI: legitimate source reads
consumed the one-turn-per-attempt policy without a chance to submit an edit.

A separate tool-capable profile now permits three turns per attempt, still only
two attempts and the same per-turn 8K context / 2K initial / 4K low-reasoning caps.
Unit and protocol checks cover read-then-edit, six-turn exhaustion, and idempotent
resume. The next frozen campaign prospectively caps the three builds at 180 model
turns; earlier failed scores and budgets remain unchanged.

## Comments

2026-09-09: Tool-capable campaign stopped at build 2, step 10. Build 1 passed
all ten steps, six supplemental workflows, and three later boundary workflows.
Build 2 passed nine steps; migration changed the report call to pass a connection
instead of the required path. Gate rejected it; retry generated 4,096 reasoning
tokens with no final edit. Build 3 unscored. Qualification failed; keep claimed.
See [portable results](../stateful-inventory-results.json). Next investigation:
make bounded failure diagnostics expose the specific mismatch before long output
truncation, then qualify prospectively. Preserve all failed campaign records.

2026-09-09 follow-up: reproduced the hidden late error with a failing feedback
regression. Feedback now surfaces bounded JSON `error` fields from observed stdout
before truncated logs, explicitly noting that some are expected rejections. It
never reads gate expectations. Migration instructions restate the path-based
reporting interface. Fresh campaign: `.gflo/evidence/stateful-inventory-feedback-v1`.
An infrastructure halt after eight accepted steps retained a memory-probe exit 137
without Docker's OOM flag; explicitly resumed without relaxing qualification.

Task decomposition decision: keep this two-consumer migration together for now.
Both signatures already fit in the selected view and the combined gate catches
cross-file mistakes. Separate workers are useful when each task has a stable
provider contract and independent validation, followed by combined gates. Do not
add voting or unbounded worker retries as a substitute for actionable diagnostics.

## Answer

New frozen campaign passed all three builds: 30 accepted atoms, 32 attempts,
33 model turns; six supplemental plus three boundary workflows passed per build.
Retained rejected migration repaired 3/3 first attempt, each with six review passes.
Feedback now surfaces bounded observed errors and objective restates the interface.
Changes were tested together; individual causal contribution is not established.
Earlier failed campaigns remain failed. One infrastructure halt was explicitly
resumed under unchanged controls. See [portable evidence](../stateful-inventory-feedback-results.json).
Next owner decision: representative repository and concrete feature to qualify.
