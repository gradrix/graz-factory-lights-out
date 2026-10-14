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

## Results

Pending.
