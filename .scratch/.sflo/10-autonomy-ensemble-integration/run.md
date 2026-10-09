# Maintained executable ensemble review — run record

Executor: markdown
Contract: contract.md
Predecessor: ../09-autonomy-review-qualification/run.md
Branch: integration/ensemble-review (not merged to main until promotion)

## Execution

Status: active — offline controls and replay equivalence done; rig suite and independent QA running on 0c91359 while blind run 2 occupies the model; vertical after blind run 2
Owner: Claude Code coordinator
Candidate: integration/ensemble-review 0c91359 (gflo/ensemble.py, Sandbox.execute readonly flag, config "review" opt-in)

## Evidence so far

1. Offline controls (Docker python:3.12, network none): `tests/test_ensemble.py` 12/12 — statements/units, catalog head/tail bounds and segment size, audit validation and foreign-citation pruning, two-judge panel rule, clean pass with read-only commands and no judge, panel-backed repair mapped onto the runner schema (duplicate judge findings collapsed), 8192→24576→65536 ladder then fail-closed `EnsembleIncomplete`, quoted correction, candidate change during review fails, explorer commands join the catalog read-only, node-ts refused, runner repair loop receives the findings, invalid `review` config rejected. Full maintained discover: 175 tests; the only failures (10 failures, 11 errors) are Docker-dependent sandbox/prepare/qualification/CLI-doctor tests that cannot reach a daemon inside the test container; the same set fails with this change stashed (11 failures there, the extra one being the new config test without its wiring). The full suite runs on the rig after blind run 2 frees it.
2. Replay equivalence (`replay.py`, output `replay-trials-3-4.txt`): stored role answers from qualified gate 1 trial 3 (16 cohort-2 cases) and gate 2 blind run 1 (24 cohort-3 cases) re-validated and re-decided by the maintained `gflo.ensemble` functions with no model calls: 40/40 cases and every unit decision and panel statement agree with the recorded prototype decisions; every mapped review passes `gflo.review.validate`.
3. 2026-10-09 16:30 EEST (route rechecked under sflo-waydriver; still the shortest evidence route to maintained integration): the full maintained suite for 0c91359 runs on the rig in `~/gflo-suite-0c91359` (git archive, own git init; `~/gflo-runtime` untouched; no model calls, so it overlaps blind run 2 safely, and Docker cleanup filters use per-instance labels). A fresh independent QA reviewer (s-qa with security/slop lenses on the read-only boundary and docs) is assessing the same frozen candidate. Next owner: coordinator; next action: consume both reports, repair through dev if needed, then run the vertical after blind run 2 finishes.
