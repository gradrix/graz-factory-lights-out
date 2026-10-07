# Role ensemble review

Executor: markdown
Unit: .scratch/autonomy/delivery/09-executable-review.md
Contract: contract.md
Predecessor: ../09-autonomy-review-units/run.md

## Execution

Status: active
Owner: Claude Code coordinator
Fixtures: prototype 2f5eae7, review cohort 2 manifest 06b6fc2a2ef036f5e59fae8e721ff2e2d85a1d5dad224658ab6d1cdfdd64a972 (16 cases; dev k01–k04, d01, d02, d03, d05; holdout d04, d06–d12)
Candidate: prototype 3f32bfb, ops/review_ensemble.py; earlier modules unchanged except UnitClient caps parameterised (defaults identical)
Controls: 105 collected, 104 pass, 1 skipped predecessor local Docker vertical. Doc runner and test runner checked by hand on k01, k04, d02, d09 in the approved image (k04: documented compare example exits 2; d09: unknown action; `echo $?` preserves prior status).
Driver: ops/rig_ensemble.sh <commit> <this dir> <cases>
Plan: trial-1 smoke on k04 (dev); then full dev; holdout scored once after dev without tuning on holdout.

## Staging attempt (no trial)

3f32bfb staging refused before admission: `git archive` default `tar.umask=002` produced 664 files against frozen 644; cohort integrity check stopped it. Driver fixed at d44193b (`-c tar.umask=022`); failed staging directories removed (no inference, no admission).

## Trial 1 — k04 smoke (dev)

d44193b, 2026-10-07 09:04–09:43Z. Battery 2 + tester 12 + adversary 10 + docs 10 = 34 attested commands (65 KB catalog), all cleanup confirmed. 11 units: 9 accepted pass/repair, unit 1 (statements 1–2, A1 validation) incomplete — prosecutor exhausted 8192. Units 9 and 10 repaired via judge on the real defect: README.md:51 example with 62/60-character digests; doc-runner segment 2 shows the documented compare exits 2 with `invalid input`, segment 13 the lengths, segment 32 the corrected success. No false findings. Case incomplete only by exhaustion. Judging 27 min, case 39 min. [Score](trial-1-score.json), [results](trial-1-results.json).

Repair: one fresh, separately charged escalation to a 24576 thinking cap for an exhausted role (062d682). 106 controls, 105 pass, 1 skipped.

## Trial 2 binding — dev split

062d682 on k01,k02,k03,k04,d01,d02,d03,d05.
