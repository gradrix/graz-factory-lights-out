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

## Cohort 3 (blind)

Built by an independent agent without pipeline access; committed as prototype 7436607, manifest ed15c759117e2aefb5563d8bde180ccc7b3707cd4450d1af38bc8cb13340d15d. 24 cases (b01–b12 from coding-b, c01–c12 from coding-c), 12 seeded across 12 reported defect classes (ordering-tie-rule, cli-exit-code, input-mutation, off-by-one-bound, rejects-valid-input, error-type-contract, numeric-exactness, whitespace-handling, readme-example-broken, tests-miss-required-category, dedup-rule, strict-decoding), 12 controls; agent reports every case verified (`OVERALL: ALL CASES VERIFIED`). Coordinator has not read `private/`. Agent notes: coding-b references lack tests/README for the new action, so all twelve b cases (seeded or not) receive the same added test file and README section; the agent once started a stray host `python3 -` that read empty stdin and was stopped without running code (a breach of the Docker-only rule, reported by the agent).

Driver/scoring generalised at 35d6ab0 (judging logic byte-identical to 5bf552c apart from split summary).
