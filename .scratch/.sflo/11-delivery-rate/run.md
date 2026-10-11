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

### Ensemble arm (frozen 7cedc3c), 16 tasks

| Task | Ensemble | Hidden tests | Ensemble stop cause | Default reviewer, exploratory pass |
|---|---|---|---|---|
| 8331398 | accepted, 1 attempt, 2,646 s | pass | — | accepted, 618 s |
| 3e6e4bd | accepted, 2 attempts, 3,234 s | pass (rescored) | — | interrupted (review timeout, since repaired) |
| 06ba3e9 | interrupted, 1,828 s | pass | audit request 120K tokens > 98K context | exhausted (review size, since repaired) |
| dcd2e78 | interrupted, 2,069 s | pass | audit request timed out | exhausted (review size, since repaired) |
| 366e6ca | accepted, 1,865 s | pass | — | accepted, 374 s |
| f20a4e2 | interrupted, 1,398 s | pass | audit request timed out | accepted, 971 s |
| 0937b55 | accepted, 2 attempts, 2,119 s | pass | — | accepted, 807 s |
| 3612b5f | interrupted, 3 attempts, 3,197 s | fail | audit request timed out (stale tests as before) | exhausted (worker miss) |
| 156422b | interrupted, 1,303 s | pass | audit request timed out | accepted, 2 attempts |
| cde2e00 | interrupted, 1,996 s | pass | audit output invalid (command segment mismatch) | interrupted (model HTTP 500, since repaired) |
| 57271fe | interrupted, 1,769 s | fail | prosecutor output invalid (source reference) | exhausted (worker miss) |
| 89d66ea | interrupted, 5,603 s | fail | after one repair round, audit output invalid (segment mismatch) | accepted, 2 attempts |
| 0c9c7c8 | interrupted, 1,410 s | pass | audit output invalid (segment mismatch) | accepted, 279 s |
| 6dd3556 | accepted, 1,142 s | pass | — | accepted, 315 s |
| edc7d71 | accepted, 1,307 s | pass | — | accepted, 157 s |
| 6ea52be | accepted, 1,749 s | pass | — | accepted, 2 attempts |

Ensemble: 7 of 16 delivered. All 9 losses are the ensemble itself failing to reach a decision (4 audit timeouts,
1 context overflow, 4 invalid role outputs); in 6 of them the patch passes the hidden
tests. Runs take 2–5× the default reviewer's time. It caught nothing the hidden tests or the default reviewer missed.

3e6e4bd was first scored as a false accept: two pass-to-pass tests "failed" because the worker renamed the test
function in `tests/test_recorded_plan_display.py`, a file the reference commit did not touch, so the original test
ids no longer existed. Its code keeps those cases' behaviour. Scorer repaired in e5fbb82 (every reference test file
is restored before scoring, as SWE-bench does). Rescoring all 32 cohort runs with it changed only this one: 0 false accepts in either arm.

Decision (agent, per the 2-round qualification cap): the ensemble stays opt-in and is not recommended for real
repositories on this rig; it is not repaired further. The default single reviewer is the factory's reviewer.

### Headline: default reviewer, all 16 tasks at frozen 7cedc3c (2026-10-11)

| Task | Factory | Time | Hidden tests (rescored, e5fbb82) |
|---|---|---|---|
| 8331398 | accepted, 1 attempt | 494 s | pass |
| 3e6e4bd | accepted, 3 attempts | 2,528 s | pass |
| 06ba3e9 | accepted, 2 attempts | 1,450 s | pass |
| dcd2e78 | accepted, 1 attempt | 947 s | pass |
| 366e6ca | accepted, 1 attempt | 463 s | pass |
| f20a4e2 | accepted, 1 attempt | 764 s | pass |
| 0937b55 | accepted, 1 attempt | 720 s | pass |
| 3612b5f | exhausted, 3 attempts | 1,838 s | fail: stale visible tests again (worker miss) |
| 156422b | accepted, 1 attempt | 501 s | pass (the old scorer reported a false accept: a renamed existing test) |
| cde2e00 | accepted, 1 attempt | 517 s | pass |
| 57271fe | accepted, 3 attempts | 1,836 s | **fail: false accept** (below) |
| 89d66ea | accepted, 1 attempt | 791 s | pass |
| 0c9c7c8 | accepted, 1 attempt | 269 s | pass |
| 6dd3556 | accepted, 1 attempt | 282 s | pass |
| edc7d71 | accepted, 1 attempt | 182 s | pass |
| 6ea52be | accepted, 1 attempt | 452 s | pass |

**Delivered 14/16 (87.5%)**: running-coach 9/11, gflo 5/5. 1 false accept (6%), 1 exhausted. 12 of 16 accepted on the first attempt,
median wall time ≈ 620 s, longest 42 minutes. Both earlier worker misses moved: 57271fe now produces a patch (on attempt
3), 3612b5f still does not edit the stale tests.

57271fe false accept: the objective said "duration_step = index of the first repeated step". The worker read it as a
list position; the hidden test uses FIT `message_index` numbering (5, 6, 7), which is the FIT convention. The worker's
own tests encoded its reading, so the factory's checks and review could not see the gap. The objective was ambiguous
on exactly the point the hidden test pins (a task-selection miss), and a domain-aware worker would have chosen the
FIT reading. It stays counted as a false accept.

Limits of this rate:
- 16 tasks, not the planned 20; two repositories, one of them gflo itself.
- Objectives were written by the agent from the reference commit, naming functions, fields and formulas (SWE-bench
  Verified "well specified" practice, but more detailed than a typical user brief). The rate measures delivery of
  precisely specified, bounded changes (2–137 changed source lines), not of terse feature requests.
- Each task ran once; temperature-0 serving keeps runs close to repeatable but not identical (3e6e4bd needed 3
  attempts here, 1 in the ensemble arm).

Roadmap consequence: above the ~50% phase 4 gate and far above the ~30% kill criterion. Whether phase 4 starts on
this evidence, or after a terse-objective arm tests how much the rate depends on objective detail, is the user's call.

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

## Test-factory trials (phase 3, frozen 7cedc3c, 2026-10-11)

| Target | Factory | Time | New tests | Mutants the existing tests miss, killed by the new tests |
|---|---|---|---|---|
| running-coach `plan_formatter.py` | accepted, 1 attempt | 740 s | 14 | 1/1 (existing tests already kill 8/9) |
| running-coach `performance_recovery_mode.py` | accepted, 1 attempt | 763 s | 21 | 17/18 |
| gflo `document_references.py`, `web.py` | not run: the trial script archived a missing `main` ref | — | — | queued again after phase 2 (`chain-tests2.sh`) |

The patches stay on the rig (`~/gflo-pp/tf/runs/*/change.patch`, private repository). Acceptance for phase 3 is the user's merge-unchanged judgement on them.

## Terse-objective arm (user choice 2026-10-11: option A before phase 4)

Same 16 tasks, frozen 7cedc3c, default reviewer; only the objective changes. Each terse objective (in
`~/gflo-pp/terse-*.json` on the rig, private) keeps the public interfaces and exact outputs the hidden tests pin and
drops implementation steps and enumerated cases, as SWE-bench Verified requires of issue text. Mean length: running-coach
984 → 427 characters, gflo 720 → 381. Task directories differ from the headline ones only in the objective (checked on
8331398). `chain-terse.sh` runs after the overnight trial and rescores with e5fbb82. Results: pending.

### Merge-unchanged judgement on the two running-coach test patches (2026-10-11)

The user delegated the judgement ("if it is good enough, we could merge them unchanged"); this verdict is the agent's.
The merge itself stays the user's (standing rule: generated changes are never applied to the user's other repositories).

| Patch | Verdict | Notes |
|---|---|---|
| `performance_recovery_mode.py`, 21 tests | merge unchanged | Boundary tests (cadence 140/139, coverage 90/89%, mode share 90%), exact caveat texts, reason routing; public interface only. Nit: one identity assertion (`returned is metrics`). |
| `plan_formatter.py`, 14 tests | merge unchanged, with a caveat | Exact-output snapshot tests of defaults and omitted sections. They also pin odd current output (`**S** () ` with a trailing space, `() --  -- 0km`), so a later formatting cleanup must update them. Some `not in` assertions repeat what exact equality already checks. |

Phase 3 share merged unchanged: 2/2 (n = 2).
