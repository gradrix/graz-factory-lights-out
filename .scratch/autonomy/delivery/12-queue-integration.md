# 12 — Queue and integration (phase 4, first unit)

Owner: Claude Code coordinator. Decision: [014](../../../docs/decisions/architecture/014-phase-4-start.md).

## Acceptance

- `ops/delivery` mines commit chains (2–4 consecutive commits, one feature, final commit adds tests that fail at the chain base) from running-coach and gflo; at least 6 chains.
- A controller-owned queue runs a chain's tasks in order on an integration branch in its own clone; each step's base is the previous accepted state; full suite (no new failures) after each merge; resumable; never touches the source repository.
- Both arms (direct, queued) run once per chain on the rig; chain delivery and false accepts recorded in the run note `.scratch/.sflo/12-queue-integration/run.md`.

## State

Opened 2026-10-12. Rig queue busy until the phase 2 hard-task repeat and the overnight rerun finish (~12 h); build and unit-test the queue meanwhile.
