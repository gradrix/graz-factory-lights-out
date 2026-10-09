# Maintained executable ensemble review — run record

Executor: markdown
Contract: contract.md
Predecessor: ../09-autonomy-review-qualification/run.md
Branch: integration/ensemble-review (not merged to main until promotion)

## Execution

Status: active — offline controls and replay equivalence done; awaiting blind run 2, rig suite and rig vertical
Owner: Claude Code coordinator
Candidate: integration/ensemble-review 85eb553 (gflo/ensemble.py, Sandbox.execute readonly flag, config "review" opt-in)

## Evidence so far

1. Offline controls (Docker python:3.12, network none): `tests/test_ensemble.py` 12/12 — statements/units, catalog head/tail bounds and segment size, audit validation and foreign-citation pruning, two-judge panel rule, clean pass with read-only commands and no judge, panel-backed repair mapped onto the runner schema (duplicate judge findings collapsed), 8192→24576→65536 ladder then fail-closed `EnsembleIncomplete`, quoted correction, candidate change during review fails, explorer commands join the catalog read-only, node-ts refused, runner repair loop receives the findings, invalid `review` config rejected. Full maintained discover: 175 tests; the only failures (10 failures, 11 errors) are Docker-dependent sandbox/prepare/qualification/CLI-doctor tests that cannot reach a daemon inside the test container; the same set fails with this change stashed (11 failures there, the extra one being the new config test without its wiring). The full suite runs on the rig after blind run 2 frees it.
2. Replay equivalence (`replay.py`, output `replay-trials-3-4.txt`): stored role answers from qualified gate 1 trial 3 (16 cohort-2 cases) and gate 2 blind run 1 (24 cohort-3 cases) re-validated and re-decided by the maintained `gflo.ensemble` functions with no model calls: 40/40 cases and every unit decision and panel statement agree with the recorded prototype decisions; every mapped review passes `gflo.review.validate`.
