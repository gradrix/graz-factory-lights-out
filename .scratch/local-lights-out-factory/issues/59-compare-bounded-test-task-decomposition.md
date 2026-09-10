# Compare bounded test-task decomposition

Type: task
Status: resolved

## Motivation

The user suggested multiple small agents writing groups of test functions. The first
large-file feature exhausted 4,096 output tokens while generating repetitive tests.
Generic compact-file guidance enabled a fresh complete build with eight tests and
three rejected mutants. This is evidence to compare decomposition, not proof that
parallel test writers improve reliability.

## Scope

Compare one test worker with behavior-scoped test tasks using the same requirements,
pinned model, aggregate token budget and independent fault checks. Prefer separate
pytest files with disjoint ownership; the existing dependency scheduler may execute
these sequentially on the single GPU. Measure total cost, retries, coverage, duplication
and review effort. Preserve negative runs. Do not weaken gates or require simultaneous
GPU execution to call this task decomposition.

Concurrent workers must not write the same file. If same-file fragments are necessary,
propose revision-bound patches and have the controller integrate them sequentially with
stale-base rejection and combined validation. Do not introduce shared mutable editing.

## Answer

Completed three frozen pairs using the existing factory: one worker (2 attempts × 3
turns) versus two disjoint behavior-scoped workers (1 × 3 each), with equal aggregate
ceiling, pinned source/model and combined fault checks. Both initially accepted 2/3.
Splitting used 30,807 tokens versus 20,128 (53% more); no reliability advantage was shown.

A held-out default-value mutant exposed an assigned-coverage gap in split-1's values
contribution. The types contribution incidentally covered it at integration. A finding
now blocks reuse; original receipts remain historical evidence. No candidate edits or
reruns were used to improve the measured outcomes. See [results and reproduction](../test-decomposition/README.md).

Keep one bounded test worker by default for this workload. Split selectively with
separate file ownership and meaningful per-task gates. Shared-file concurrent mutation
was neither needed nor introduced. Follow-ups 60–62 cover planner recovery, new-file
draft repair and integration requirement provenance. No factory runtime code changed.
