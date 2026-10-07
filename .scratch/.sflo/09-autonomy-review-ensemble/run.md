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
