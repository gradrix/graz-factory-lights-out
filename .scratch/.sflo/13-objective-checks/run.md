# Objective-derived checks prototype (2026-10-14)

Question (route option 3 after phase 4, user go-ahead 2026-10-14): can checks written from the objective alone,
before any implementation, catch the false accepts that "no new failures" lets through, without rejecting correct work?

Method:
- Generator: a `gflo run` per objective on the task's base repository and environment (`ops/delivery/objcheck.py build`).
  The worker sees only the objective and the base code, and writes `tests/objective_checks/test_*.py`. Acceptance
  (`ops/delivery/objective_check.py`): no other file changes, at least 3 test functions, they collect, and every one
  fails on the base. Two attempts, 40 turns, default reviewer.
- Evaluation (`objcheck.py evaluate`): each objective's checks run on the base, the reference commit and every
  accepted delivered tree. Rule under test: reject a delivery if any generated check fails.
- Cohort: 15 accepted phase 1 runs (14 delivered, 1 false accept) and 5 phase 4 chains with accepted runs
  (4 correct deliveries, 6 false accepts over both arms). Rig: `~/gflo-pp/oc/`, chain `chain-oc.sh`, code in `~/gflo-oc`.

Measures: catch rate on the 7 false accepts; false-reject rate on the 18 correct deliveries; checks that fail on the
reference (wrong checks); generator acceptance rate and time.

Smoke (phase 1 8331398): accepted, 7 checks; base 0/7, reference 7/7, delivered 7/7.

## Results (2026-10-14, code ec432b8 plus the evaluate filter)

Generator: **11 of 20 objectives produced an accepted check set** (phase 1 9/15, phase 4 2/5), about 1,030 s per run
(20,519 s for 20). Losses: 6 ran out of 40 turns in both attempts; 1 overflowed the 98K context (p4 44ae332);
1 edited the repository's own run notes (p1 0c9c7c8, correctly rejected); 1 passed acceptance but the reviewer asked
for repair over top-level imports of modules that already exist (p1 3e6e4bd; the prompt's rule covers only names the
change adds). The first evaluation pass crashed on a set with no checks directory; `evaluate` now skips cases whose
generator was not accepted.

134 checks in the 11 sets; every one failed on its base (acceptance requires it).

| tree (11 accepted check sets) | all checks pass | notes |
|---|---|---|
| reference commit | 8/11 | 7 of 134 checks (5%) fail on the reference: 57271fe 2/10, p4 8331398 1/11, p4 80400b0 4/26 |
| correct deliveries (hidden tests pass) | 8/9 | the one rejected, p4 80400b0 direct, fails 2 checks beyond the reference's 4; both pin error messages the objective states verbatim (items 4 and 5) and the hidden tests do not cover |
| false accepts with a check set | caught 3/4 | 57271fe (1 check beyond the reference), p4 8331398 queued (4), p4 80400b0 queued (6). Missed: p4 8331398 direct; no check covered the step-2 lap labels it left out |
| false accepts without a check set | 0/3 | generators for p4 e7d7f18 (both arms) and 44ae332 failed |

Rule "reject if any generated check fails":
- Catches 3 of 7 false accepts overall (3 of 4 where a set exists).
- Rejects 3 of 11 reference implementations, because the checks themselves are wrong there; a worker cannot pass such a check.
- Rejects 1 of 9 hidden-test-correct deliveries, for stated requirements it really missed.
- Phase 1 alone (9 sets): no wrong checks on 8 of 9 references; all 8 correct deliveries pass; the 1 false accept is caught.

Reading: where the generator succeeds, its checks discriminate well. Three gaps stop it from being a hard gate:
wrong checks (3 of 11 sets) would block correct work, coverage is thinnest on feature-sized objectives where false
accepts concentrate (2 of 5), and each set costs about as much model time as a delivery attempt. Caveat: objectives
were written from the reference commits and are unusually precise. Decision: [015](../../../docs/decisions/architecture/015-objective-checks.md).
