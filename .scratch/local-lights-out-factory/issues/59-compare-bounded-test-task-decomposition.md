# Compare bounded test-task decomposition

Type: task
Status: ready-for-agent

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
