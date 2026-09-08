# Connect the durable task-to-evidence loop

Type: task
Status: resolved
Blocked by: 16, 17

## Scope

Connect submit/status/resume, candidate execution, trusted validation, bounded evidence-derived retry and reconciliation.

## Acceptance

Deterministic end-to-end fixtures demonstrate successful completion, preserved failure, exhausted-budget quarantine and interruption/resume without duplicate acceptance. All model/container/test operations occur outside ledger transactions. No arbitrary product-planning layer is introduced.

## Answer

Implemented immutable RunPlan submission, serialized controller execution, bounded source-file expansion/model turns, separate candidate smoke and trusted gates, observation-derived retries/quarantine and restart reconciliation. SQLite schema 2 migrates prior ledgers and preserves immutable run bindings. CLI `submit-run`, `run` and `resume ATOM_ID` now execute the prepared loop; bare resume retains ledger-only reconciliation.

Fifteen deterministic integration tests use real SQLite/artifacts, including actual process death during generation and after acceptance commits, retained failures, retry/quarantine, tool bounds, expiry, leased-retry diagnostics, plan immutability, migration and CLI behavior. Full default suite: 162 tests and 23 subtests pass; eight optional broker tests skip. Ruff/type checks pass. A live CLI run against the actual local model reached acceptance after three independent process cases; repeated resume preserved identical history. [Verification manifest](../loop-verification-results.json) and [controller documentation](../../../../docs/controller.md) record evidence and limitations.

## Comments

2026-09-08: The user authorized the next step and questioned local-model speed. Per-endpoint timing and one direct replay confirmed approximately 10 output tokens/second with decode dominating, not client overhead or queueing. [Investigate slow local decode](20-investigate-slow-local-decode.md) records the open performance issue. No engine setting changed. The twelve-task diagnostic pilot remains task 19; no general campaign/coding or unattended-operation claim is made.
