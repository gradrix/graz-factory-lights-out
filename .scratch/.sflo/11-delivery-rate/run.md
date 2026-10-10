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
| 57271fe | exhausted (3), 1,608 s | fail (no patch) | all 3 attempts spent the 40-turn budget reading code across 4 modules without editing (worker miss; multi-file feature, cf. decision 008) | phase 2 |

Source 2: gflo itself (public), 5 tasks.

| Task | Factory | Hidden tests | Cause when not delivered | Repair |
|---|---|---|---|---|
| 89d66ea | accepted, 2 attempts, 1,044 s | pass | — | — |
| 0c9c7c8 | accepted, 279 s | pass | — | — |
| 6dd3556 | accepted, 315 s | pass | — | — |
| edc7d71 | accepted, 157 s | pass | — | — |
| 6ea52be | accepted, 2 attempts, 692 s | pass | — | — |

Exploratory default-reviewer pass, 17 runs over 16 tasks: 11 delivered, 0 false accepts; every run that produced a patch passes the hidden tests. Of the 6 losses, 4 were factory gaps, now repaired (three review limits sized for ~95-line fixtures, one model-error path that stopped the run) and 2 were worker misses (3612b5f stale visible tests, 57271fe never started editing).

The rig code is frozen at 7cedc3c from here: the ensemble arm and a full default-reviewer rerun (`chain-frozen.sh`, after the test-factory trials) both run on it.

### Ensemble arm (frozen 7cedc3c)

| Task | Factory | Hidden tests | Single reviewer, same task |
|---|---|---|---|
| 8331398 | accepted, 1 attempt, 2,646 s | pass | accepted, 618 s |
| 3e6e4bd | accepted, 2 attempts, 3,234 s | pass | interrupted (review timeout, since repaired) |
| 06ba3e9 | interrupted | pass | exhausted (review size, since repaired) |
| dcd2e78 | interrupted | pass | exhausted (review size, since repaired) |

Both ensemble interruptions: the unit audit request reached ~120K tokens against the 98K context ("could not reach a validated decision"). The ensemble sends audit roles the reviewed files plus the exploration catalog, which real repositories overflow. Not repaired during the frozen arm.

The headline rate will come from a rerun of all tasks at one frozen revision after this pass.

Results: pending.

Task selection rule (SWE-bench Verified practice): a mined task is kept only when an operator-style objective can
state everything its hidden tests check without dictating the patch. Excluded so far: two copy-rewrite commits
whose many hidden assertions pin exact new wording, and commits whose tests need PostgreSQL only.

## Worker observations for phase 2 (from the exploratory trajectories)

- 14 of 25 worker attempts used the full 40-turn budget, including two delivered tasks (f20a4e2, 0937b55) that
  finished on the last turn. Peak request size reached ~80K of the 98K-token context.
- 57271fe (no edit in 120 turns): the repository already ships a ~31 KB layout overview in its CLAUDE.md and the
  worker read it; most turns went to tests and to the fitparse library's FIT message definitions, which no repository
  map covers. Attempts 2 and 3 received only "review needs changed source files" and re-read everything from zero.
- 3612b5f: not navigation; the check named the two stale tests and the worker never edited them.
- User question (2026-10-10): should the worker see a system overview / module graph and work on parts instead of
  reading the whole system? Agent recommendation: yes to a map as a tool and to retained findings across attempts;
  no to a worker blind outside its module for now (roadmap phase 2 navigation arms).

## Phase 2 staged (2026-10-10)

Code 8123102 in `~/gflo-p2` on the rig; `chain-phase2.sh` starts after `FROZEN DONE`. Arms on all 16 tasks:
`mini` (mini-swe-agent 2.4.6 worker, same model and sandbox, SWE-bench observation template), `nav` (all
navigation aids), then `notes`, `plan`, `map` alone. Navigation aids passed independent QA (one repair round;
baseline worker byte-identical to the parent commit).
