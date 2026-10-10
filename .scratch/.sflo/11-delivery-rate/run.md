# Phase 1 — delivery rate on real tasks: run note

Unit: [11-delivery-rate](../../autonomy/delivery/11-delivery-rate.md). Decisions: 011, 012.
Privacy: the source repositories are private; this public note records only aggregates and short commit ids. Tasks,
objectives, hidden tests and transcripts stay on the rig (`~/gflo-pp/`) and in the ignored `.gflo/delivery/`.

## Built so far (2026-10-10)

- `python-project` profile (d37216c, QA repair 80400b0 accepted by independent QA+security review).
- Optional task `test_command` (aeb3b05); reviewers handle real repositories through changed files (5f64c85).
- Tooling in `ops/delivery/`: `mine.py` (fail-to-pass / pass-to-pass validation from history, JUnit outcomes),
  `tasks.py` (build tasks, score runs against hidden tests), `drive.py` (cohort driver), `env_exec.py`.

## Findings on the way

- The fixed profiles could not run any of the user's Python projects (pytest, pandas, SQLAlchemy, sdists).
- Both reviewers loaded the whole workspace, capped at 200 KB / 1,000 text files: every review of a real
  repository (running-coach ≈ 9.6 MB) would have failed as "input too large". The ensemble battery ran
  `unittest discover`, not the project's tests. Both were qualified only on ~95-line fixtures.
- Sandbox output is bounded, so per-test outcomes must come from JUnit reports, not console summaries
  (first pilot recorded 110 instead of ~3,100 pass-to-pass tests).

## Pilot (task cde2e00, single reviewer)

1. Run 446ed362407c: worker fixed the bug by turn 16 and added a regression test, then spent the remaining turns
   trying to fit the ~110 s suite into the 60 s worker command limit; 3 attempts exhausted. Scoring: hidden fail-to-pass
   and all 3,951 pass-to-pass tests **pass** — a correct patch the factory rejected. Root cause was the task, not the
   model: the whole-suite acceptance check already fails on the base (63 database tests the project does not mark).
   Repairs: no-new-failures acceptance for mined tasks (5b5991c), 300 s worker commands for real projects (54cb497).
2. Run ceeabac8ee21: died on "Another environment preparation owns this store" while a concurrent preparation held
   the store. Repair: bounded waiting instead of instant refusal (75d32ee).
3. Third run: pending.

Also found while mining: older commits pin with a uv.lock (one version per Python range, one pin stale against
pyproject); the resolver now reads it the way uv does (44ae332).

## Cohort

Source 1: home-lab `services/running-coach`, 36 bounded candidate commits (2–137 changed source lines), non-database
tests only. Mining started on the rig 2026-10-10.

### Exploratory pass (default reviewer), code changing between tasks

| Task | Factory | Hidden tests | Cause when not delivered | Repair |
|---|---|---|---|---|
| cde2e00 (pilot 4) | accepted, 1 attempt, 640 s | pass | — | — |
| 8331398 | accepted, 618 s | pass | — | — |
| 3e6e4bd | interrupted | pass | 120 s review request limit on a 77K-token review | 73f8fed |
| 06ba3e9 | exhausted (3) | pass | attempt 1 broke an existing test (correct rejection, repaired); attempts 2–3 review refused: changed files > 200 KB | 8cf9671 |
| dcd2e78 | exhausted (3) | pass | review refused, changed files > 200 KB (ran before 8cf9671) | 8cf9671 |
| 366e6ca | accepted, 374 s | pass | — | — |
| f20a4e2 | accepted, 971 s | pass | — | — |
| 0937b55 | accepted, 807 s | pass | — | — |
| 3612b5f | exhausted (3) | pass | worker kept two visible tests that assert the behaviour the objective removes; the check named them each attempt (worker miss) | — |
| 156422b | accepted, 2 attempts, 1,032 s | pass | — | — |
| cde2e00 (rerun) | interrupted, 206 s | fail (unfinished) | model emitted a self-repeating tool call; llama.cpp HTTP 500 stopped the run | 7cedc3c |

Source 2: gflo itself (public), 5 tasks.

| Task | Factory | Hidden tests | Cause when not delivered | Repair |
|---|---|---|---|---|
| 89d66ea | accepted, 2 attempts, 1,044 s | pass | — | — |
| 0c9c7c8 | accepted, 279 s | pass | — | — |

After 13 exploratory runs (12 tasks): 8 delivered, 0 false accepts, and all 12 runs that produced a patch pass the hidden tests. Of the 5 losses, 4 were factory gaps, now repaired: three review limits sized for ~95-line fixtures and one model-error path that stopped the run. The fifth was a worker miss (3612b5f).
The headline rate will come from a rerun of all tasks at one frozen revision after this pass.

Results: pending.

Task selection rule (SWE-bench Verified practice): a mined task is kept only when an operator-style objective can
state everything its hidden tests check without dictating the patch. Excluded so far: two copy-rewrite commits
whose many hidden assertions pin exact new wording, and commits whose tests need PostgreSQL only.
