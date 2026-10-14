# Objective-derived checks: measured, not a hard acceptance gate

Status: accepted, 2026-10-14. Decision maker: the agent, under the user's delegation ("when it comes to other your recommendations and suggestions - sure, go ahead with it", 2026-10-11). The user approved the prototype experiment (2026-10-14). Originating unit: `.scratch/autonomy/delivery/13-objective-checks.md`; run note `.scratch/.sflo/13-objective-checks/run.md`.

## Question

Decision 014 found that on feature-sized work 6 of 10 accepted chains failed the reference tests. A triage showed that all 6 missed requirements the objective stated. Can a separate model run write checks from the objective alone, before any implementation, that catch these false accepts without rejecting correct work?

## Evidence

Each generator run sees only the objective and the base code. It writes `tests/objective_checks/test_*.py`, which must all fail on the base (`ops/delivery/objective_check.py`). The checks then ran on the reference commit and on every accepted delivery from phases 1 and 4 (`ops/delivery/objcheck.py`).

| measure | result |
|---|---|
| generator produced an accepted check set | 11/20 (phase 1 9/15, phase 4 2/5); ~1,030 s per run |
| reference passes all its checks | 8/11 (7 of 134 checks are wrong) |
| hidden-test-correct deliveries pass all checks | 8/9 (the rejected one misses two error messages the objective states verbatim) |
| false accepts caught | 3/4 with a check set; 3/7 overall |

## Choice

Generated checks **do not join acceptance as a hard gate**:

- Wrong checks would reject correct implementations (3 of 11 references), and a worker cannot make a wrong check pass.
- The generator fails most often on feature-sized objectives (2 of 5), which is where false accepts concentrate.
- Each check set costs about as much model time as a delivery attempt.

The tooling stays in `ops/delivery/` as an experiment, not a product feature.

Within the cap of two qualification rounds, a second round would test a weaker role. A delivery that fails generated checks gets one repair turn with the failures as feedback. If any still fail, the delivery is accepted but flagged for human review with the failing checks listed. That turns a wrong check into one wasted repair, not a rejection. The prompt would also say that existing modules may be imported at the top of the file (one generator was lost to that). Round 2 needs runner integration and a rig re-run, so it was put to the user. It is deferred by maintenance mode (decision 016, 2026-10-14) and reopens if a new model passes the features gate.

## Remaining assumptions

- The objectives were written from the reference commits and are unusually precise. Checks written from a user's own looser brief will likely be weaker.
- One generator run per objective, on one model and one rig. The phase 4 sample is small: 2 check sets and 4 false accepts covered.
