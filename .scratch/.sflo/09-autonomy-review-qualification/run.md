# Review consistency, blind qualification and integration

Executor: markdown
Unit: .scratch/autonomy/delivery/09-executable-review.md
Contract: contract.md
Predecessor: ../09-autonomy-review-ensemble/run.md

## Execution

Status: active — gate 1 PASSED (trial 3); gate 2 blind run 1 on candidate 3
Owner: Claude Code coordinator; independent seeding agent for cohort 3 (no pipeline access, private expectations unread by coordinator until scoring)
Candidate: prototype 6920218 (candidate 3, frozen for gate 2); candidate 1 5bf552c and candidate 2 ee8f2a4 failed gate 1
Controls: candidates 2 and 3 review suites 49/49 (Docker); candidate 1 had 111 collected, 110 pass, 1 skipped
Driver: ops/rig_ensemble.sh 6920218 <this dir> <all 16 cohort-2 ids>

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

## Gate 1 trial 2 — candidate 2 (ee8f2a4): FAILED 13/16

Evidence: `trial-2-*.json`, `trial-2-stage-inventory.sha256`; rig `~/gflo-review-ensemble-ee8f2a4-trial-2/`. No interpreter incompletes and no audit invalidity remained; every seeded and original defect case returned repair, and controls k02, k03, d03, d04, d07 passed.

- d02 u4 (strict + neutral repair, charitable pass) and d11 u5 (charitable + neutral repair, strict pass): still read the preserved unknown-action `ValueError` as "the specified rejection" despite the abstract reading rule. The judges in the minority each cited the right reason (the error belongs to existing routing; the added action specifies none). This one boilerplate sentence is the ambiguity in the factory's own objective template.
- d08 u3: the prosecutor exhausted both 8192 and 24576 reasoning tokens on the anchor-uniqueness statement (prompt 13335 tokens), so the unit stayed incomplete.

## Candidate 3 (6920218)

- The reading rule now names the factory boilerplate concretely: for tests that must cover "a specified rejection (or another boundary when no rejection is specified)", only an error specified for the newly added behavior counts; preserved routing errors and CLI exit handling do not. Cohort 3 contains a seeded `tests-miss-required-category` defect, so gate 2 checks that this rule does not excuse a real gap.
- A third escalation rung at 65536 reasoning / 69632 max tokens (HTTP 1500 s, role 1620 s); the case judging deadline includes it.
- Controls: review suites 49/49 in Docker. Gate 1 trial 3 launched 2026-10-09 on all 16 cases.

## Gate 1 trial 3 — candidate 3 (6920218): PASSED 16/16

Evidence: `trial-3-*.json`, `trial-3-stage-inventory.sha256`; rig `~/gflo-review-ensemble-6920218-trial-3/`. All 16 cases correct and complete (dev 8/8, holdout 8/8); all seven controls pass with no blocking finding.

Grounding check against `review-cohort-2/private/expectations.json` (dev cohort, readable): every one of the 19 repair units cites its case's required defect at the defect's source line; none raises anything else.

| Case | Required defect | Repair units (statement, source) |
|---|---|---|
| k01 | test hardcodes `/workspace` | u9 (20), u10 (24): `tests/test_manifest_tool.py:178` |
| k04 | README digests 62/60 chars | u9 (21), u10 (24): `README.md:51` |
| d01 | CLI ValueError traceback, exit 1 | u4 (15) `cli.py:6`; u7 (23, preserve CLI error contract) `cli.py:5` |
| d05 | dedup keeps first not last | u1 (2), u2 (5) `domain.py:4`; u5 (tests pass) `test_behavior.py:12` failing on it |
| d06 | tie keeps largest id | u2 (4), u5 (15) `domain.py:8`; u4 (tests pass) failing on it |
| d09 | README uses nonexistent action | u6 (15) `README.md:10` |
| d10 | blockers unsorted | u2 (5), u5 (15) `domain.py:9` |
| d12 | input list sorted in place | u2 (8), u3 (12) `domain.py:5` |

The d09 "tests miss rejection" extra from the ensemble holdout did not recur. Candidate 3 is frozen for gate 2; blind run 1 launched on all 24 cohort-3 cases with `GFLO_COHORT=review-cohort-3`.
