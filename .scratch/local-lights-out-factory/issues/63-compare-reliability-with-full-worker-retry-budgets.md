# Compare reliability with full per-worker retry budgets

Type: task
Status: ready-for-agent
Blocked by: 61

## Owner preference

Reliability is the primary objective on the local GPU; additional tokens/electricity
are acceptable when they buy better completion or coverage. The equal-aggregate-budget
experiment in issue 59 does not answer whether additional specialist capacity is worth it:
each split worker had only one attempt, while the solo worker had two.

## Scope

After fixing new-file draft repair, compare one worker with behavior-scoped workers
that each retain the same full retry allowance. Permit the larger aggregate budget
explicitly and freeze finite per-run limits. Measure independently checked completion,
assigned and combined coverage, held-out faults, intervention and failure modes first.
Token use and latency are secondary observations, not reasons to reject a more reliable
configuration. Keep the pinned model, source and checks unchanged across conditions.

Include the default-value coverage gap in preflighted per-task checks. Retain failed
runs and post-acceptance findings; do not report only successful campaigns. Treat a
small sample as provisional and avoid claiming a general ranking from it.
