# Review consistency, blind qualification and integration

Executor: markdown
Unit: .scratch/autonomy/delivery/09-executable-review.md
Contract: contract.md
Predecessor: ../09-autonomy-review-ensemble/run.md

## Execution

Status: active — gate 1 (consistency, dev)
Owner: Claude Code coordinator; independent seeding agent for cohort 3 (no pipeline access, private expectations unread by coordinator until scoring)
Candidate: prototype 5bf552c (interpreter + strict/charitable/neutral judge panel on 80b4956)
Controls: 111 collected, 110 pass, 1 skipped
Driver: ops/rig_ensemble.sh 5bf552c <this dir> <all 16 cohort-2 ids>

## Gate 1 binding

All 16 review-cohort-2 cases (dev). Gate: 16/16 correct and complete; no blocking finding outside each case's seeded defect.
