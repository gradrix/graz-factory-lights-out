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

## Trial 2 — dev split, 4/8, zero wrong verdicts

062d682 on k01–k04, d01, d02, d03, d05. [Score](trial-2-score.json), [results](trial-2-results.json), [hashes](trial-2-artifact-hashes.json).

- Correct: k01 repair (units 9–10, A6), k03/d02/d03 pass. No control produced a repair; no defect case produced a pass.
- Incomplete: k02 (units 3–4), k04 (unit 6; its seeded README defect again repaired in unit 9), d01 (units 3–4), d05 (units 1, 2, 5, 6). Every incomplete unit — 9 of 84 — is an auditor answer rejected for citing a segment owned by another command (or wrong segment count). No exhaustion; the escalation ladder never fired.
- Evidence covers the fresh defects: d01 tester captured `exit=1` with a Python traceback for an invalid action (requirement: exit 2, no traceback); d05's own test run shows `FAIL: test_case_1`.
- Docs explorer advisory verdicts sometimes fail their schema (k02); their attested commands still enter the catalog.

Repairs (dev-only tuning): 2d8db9e one quoted correction attempt with specific validator messages; 80fbfd2 nests each command's segments in the view (ownership visible) and allows two corrections. 108 controls, 107 pass, 1 skipped.

## Trial 3 binding — dev split rerun

80fbfd2 on the same eight dev cases. Holdout remains unrun.

## Trial 3 — dev rerun, 7/8, zero wrong verdicts

80fbfd2. [Score](trial-3-score.json), [results](trial-3-results.json), [hashes](trial-3-artifact-hashes.json). k01–k04, d01, d02, d05 correct and complete; d03 (control) incomplete on unit 1. The auditor-wire failures from trial 2 did not recur.

Grounding (coordinator check): d01 unit 4 cites `cli.py:6` (`raise`) with four captured runs showing `exit=1` plus traceback against statement 15 (exit 2, no traceback) — the seeded defect. d05 units 1/2/5 cite `domain.py:4` (`last.setdefault`) with captured output `## Added\n- Old\n- Y` where last-occurrence semantics require `- Y` only, and the shipped test failure — the seeded defect. k01/k04 as in earlier trials. Some judge outputs append minor "statement satisfied" findings: noise, not wrong.

d03 unit 1: the auditor exhausted both 8192 and 24576 classifying ~30 commands in one answer. Repair: auditing in chunks of 8 commands, merged and reverified per chunk (candidate below). 109 controls, 108 pass, 1 skipped.
