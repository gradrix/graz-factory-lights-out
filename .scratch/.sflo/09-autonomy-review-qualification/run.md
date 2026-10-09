# Review consistency, blind qualification and integration

Executor: markdown
Unit: .scratch/autonomy/delivery/09-executable-review.md
Contract: contract.md
Predecessor: ../09-autonomy-review-ensemble/run.md

## Execution

Status: active — gate 1 PASSED (trial 3); gate 2 FAILED: blind run 1 24/24 (trial 4), blind run 2 23/24 with b06 incomplete (trial 5); loop-escape repair under way
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

## Gate 2 blind run 1 — candidate 3 (6920218), trial 4: 24/24, all grounded

Evidence: `trial-4-*.json`, `trial-4-stage-inventory.sha256`; rig `~/gflo-review-ensemble-6920218-trial-4/`. Blind run 2 (trial 5, same frozen candidate) was launched before this run's score was read, so nothing seen here could influence it.

Verdicts: 24/24 correct and complete; 12/12 controls pass with no blocking finding; 12/12 seeded cases repair.

Grounding (cohort-3 `private/expectations.json` first read at this scoring step): every repair unit cites the seeded defect at its source line with reproducing evidence.

| Case | Class | Required defect | Repair units (statement → source) |
|---|---|---|---|
| b01 | ordering-tie-rule | FIFO queue lets later eligible nodes outrank newly eligible earlier ones | u2 (5) `domain.py:15` |
| b03 | cli-exit-code | `sys.exit(message)` exits 1 not 2 | u3 (11) `cli.py:8` |
| b04 | input-mutation | shallow copy, nested defaults mutated | u4 (14) `domain.py:15` |
| b06 | off-by-one-bound | `>=` rejects total == max_total | u2 (8) `domain.py:16` |
| b11 | rejects-valid-input | conflict check before old-event filter | u2 (3), u6 (17, framed as invented validation) `domain.py:11` |
| c03 | error-type-contract | OverflowError instead of ValueError | u1 (3) `domain.py:9` |
| c04 | numeric-exactness | `x**(i-1)` at i=0: floats, ZeroDivisionError at x=0 | u1 (4) `domain.py:7` |
| c05 | whitespace-handling | `split(' ')` ignores tabs | u1 (3), u2 (6) `domain.py:7` |
| c06 | readme-example-broken | README sends `value` not `number` | u5 (13) `README.md:8` |
| c09 | tests-miss-required-category | no rejected-input test though rejections specified | u4 (13) `test_behavior.py:11` |
| c10 | dedup-rule | repeated names counted per occurrence | u1 (1) `domain.py:7`; u4 (12) `domain.py:7`, `test_behavior.py:5` |
| c12 | strict-decoding | `unquote_plus` replaces invalid UTF-8 | u1 (4) `domain.py:9` |

The c09 result matters for candidate 3's reading rule: the rule excuses a missing rejection test only when no rejection is specified for the added behavior, and here it correctly did not.
- 2026-10-09: after blind run 2 (trial 5) was admitted, `contract.md` changed only in its first paragraph to record the user's later push authorisation (commit 67cce2a); trial 5's admission keeps the prior hash, and gates, cases and acceptance are unchanged.

## Gate 2 blind run 2 — candidate 3 (6920218), trial 5: 23/24, FAILED (b06 incomplete)

Evidence: `trial-5-*.json`, `trial-5-stage-inventory.sha256`; rig `~/gflo-review-ensemble-6920218-trial-5/`. 12/12 controls pass with no blocking finding; 11/12 seeded cases repair; b06 (off-by-one-bound) is incomplete although its unit 5 repaired on the seeded defect at `domain.py:16`. Every repair unit in this run is grounded at its seeded defect line (c04 u2 and c12 u4 add a second unit on the same defect line). Gate 2 requires both runs complete, so gate 2 fails and the integration vertical (chained to start after this run) was stopped before it launched.

Run-to-run agreement with trial 4: case decisions 23/24 (b06 repair → incomplete); identical repair-unit sets 21/24 (b06, c04 [1] → [1,2], c12 [1] → [1,4]); no cited defect differs.

Cause of b06 u2: the first audit chunk exhausted 8192, 24576 and 65536 reasoning tokens. The deep attempt's reasoning (188 KB) is a degenerate repetition loop: seven probe lines repeated about 250 times each until the budget ended (1304 s for that request alone). Every request runs at temperature 0 with an identical prompt, so escalation replays the same greedy path with more room and cannot escape a loop. Across trials 3–5 (about 1780 role calls), 11 first attempts exhausted; 10 were rescued by escalation, this loop was not, and exhausted attempts cost 776 s, 582 s and 2393 s per trial. At roughly 25–30 role calls per factory review this is a few percent of reviews interrupted, each after a long stall.
