# Review consistency, blind qualification and integration

Executor: markdown
Unit: .scratch/autonomy/delivery/09-executable-review.md
Contract: contract.md
Predecessor: ../09-autonomy-review-ensemble/run.md

## Execution

Status: active — gate 1 rerun (consistency, dev) on candidate 2
Owner: Claude Code coordinator; independent seeding agent for cohort 3 (no pipeline access, private expectations unread by coordinator until scoring)
Candidate: prototype ee8f2a4 (candidate 2: panel kept, interpreter removed, reading rules, audit citation pruning); candidate 1 5bf552c failed gate 1
Controls: candidate 2 review suites 49/49 (Docker); candidate 1 had 111 collected, 110 pass, 1 skipped
Driver: ops/rig_ensemble.sh ee8f2a4 <this dir> <all 16 cohort-2 ids>

## Gate 1 binding

All 16 review-cohort-2 cases (dev). Gate: 16/16 correct and complete; no blocking finding outside each case's seeded defect.

## Cohort 3 (blind)

Built by an independent agent without pipeline access; committed as prototype 7436607, manifest ed15c759117e2aefb5563d8bde180ccc7b3707cd4450d1af38bc8cb13340d15d. 24 cases (b01–b12 from coding-b, c01–c12 from coding-c), 12 seeded across 12 reported defect classes (ordering-tie-rule, cli-exit-code, input-mutation, off-by-one-bound, rejects-valid-input, error-type-contract, numeric-exactness, whitespace-handling, readme-example-broken, tests-miss-required-category, dedup-rule, strict-decoding), 12 controls; agent reports every case verified (`OVERALL: ALL CASES VERIFIED`). Coordinator has not read `private/`. Agent notes: coding-b references lack tests/README for the new action, so all twelve b cases (seeded or not) receive the same added test file and README section; the agent once started a stray host `python3 -` that read empty stdin and was stopped without running code (a breach of the Docker-only rule, reported by the agent).

Driver/scoring generalised at 35d6ab0 (judging logic byte-identical to 5bf552c apart from split summary).

## Gate 1 trial 1 — candidate 1 (5bf552c): FAILED 3/16

Evidence: `trial-1-results.json`, `trial-1-score.json`, `trial-1-artifact-hashes.json`, `trial-1-stage-inventory.sha256`; rig `~/gflo-review-ensemble-5bf552c-trial-1/`. Correct: d03, d06, d12. Twelve cases incomplete, one control (d02) false repair.

Causes, from the unit records:

- 14 of 15 incomplete units: the requirement interpreter returned criteria of roughly 600–650 bytes on all three attempts and the controller rejected each (`Each criterion must be nonempty text of at most 600 bytes`); the correction feedback never shortened them. Pure controller/role friction, no judgement involved.
- 1 incomplete unit (k03 u1): one audit chunk cited segments owned by other commands on all three attempts.
- False control repairs, all panel-agreed and all traceable to interpreter criteria that every role then applied:
  - d02 u4 and d11 u5: criterion named the preserved unknown-action `ValueError` as the "specified rejection", so tests covering normal/boundary/boundary were ruled insufficient. The objectives specify no rejection for the added action ("input shapes and types follow the contract except explicitly described errors"), so the "another boundary" alternative applies.
  - d08 u1: criterion required rejecting markdown longer than 10000 code points; the objective states that as an input bound ("Do not invent validation").
- Grounded real findings on originals (k01 u10 hardcoded `/workspace` cwd makes a discovered test fail; k04 u10 README example uses 62/60-character sha256 values that the CLI rejects; d09 u6 seeded README action name) were correct.

Conclusion: the interpreter made judges consistent by making them consistently wrong; it is removed. Judge disagreement is handled by the panel alone.

## Candidate 2 (ee8f2a4)

Changes from 5bf552c, tuned on cohort 2 only (cohort 3 still unread):

- Interpreter role, its policy and criteria plumbing removed; units run audit chunks → prosecutor → three-judge panel (repair needs ≥2 judges on a common statement).
- Shared policy gains two generic reading rules: stated input bounds and shapes are caller preconditions unless the objective requires an error; a conditional alternative ("X, or Y when no Z is specified") is satisfied by Y unless Z is specified for the added work, and behavior only to be preserved is not newly specified.
- Audit answers have foreign-command segment citations dropped (count recorded as `pruned_segments`) when an owned citation remains; rows left with none still go through correction.
- Controls: review suites 49/49 in Docker (python:3.12-slim). The full discover run shows 10 errors only in planning-pilot git suites because the slim image has no git; unrelated to this change.

Gate 1 rerun launched 2026-10-08 18:04 as trial 2 on all 16 cases. Scoring note: originals (k01, k04, d-seeded) may carry additional grounded real defects; for controls any blocking finding fails the gate.
