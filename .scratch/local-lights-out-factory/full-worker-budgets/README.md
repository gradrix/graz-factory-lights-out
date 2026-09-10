# Full per-worker retry budget comparison

Reliability and independently checked coverage are primary. Local token use and
latency are secondary. This is a six-trial qualification, not a statistical ranking.

## Frozen design

The schedule is solo-1, split-1, split-2, solo-2, solo-3, split-3. All plans and gates
were persisted before inference. Solo gets one worker with two attempts and three
turns per attempt (six responses; 73,728 reserved tokens). Split gets two workers,
each with the same allowance (twelve responses; 147,456 reserved tokens). Specialists
own separate files for value/caller behavior and type rejection; execution remains
sequential. Both use the same accepted 10,002-line source, pinned deployment, context
and output limits, requirement text, and faults from the earlier decomposition trial.

The value worker and solo worker must now independently detect the wrong-default
mutant in addition to the original assigned faults. Combined validation also checks
it. The trusted reference suite passed every per-task and integration case before
inference. The later audit checks default and integer-subclass rejection for each
assigned contribution in accepted features and combined acceptance; subclass remains outside the worker's
pinned fault gates. Failed trials and later findings must remain visible.

The controller includes issue 61 draft repair and issue 62 version-2 integration
provenance. No model switch, manual candidate correction or budget extension.

Run `PYTHONPATH=. .venv/bin/python` with this directory's `campaign.py` from the repo
root. It refuses an existing `.gflo/evidence/full-worker-budgets-v1` directory. Then
run `../test-decomposition/audit.py` with `--campaign` pointing there, `--results`
pointing at this directory's `results.json`, and a new `--output` path. Historical
campaigns and their findings are never reset by this experiment.

## Observed results

| Condition | Accepted and audited | Model responses | Actual total tokens | Model seconds |
| --- | ---: | ---: | ---: | ---: |
| Solo | 3/3 | 5 | 14,348 | 45.2 |
| Two specialists | 2/3 | 16 | 50,844 | 123.2 |

All five accepted features passed the post-run default/subclass audit for assigned
contributions and combined results, with no findings and no replay events. Version-2
integration contracts name both requirement groups and grant no worker tools.
`results.json` contains every trial, response, failed attempt and contract; `audit.json`
contains the checks for accepted features. `preflight.json` retains reference checks.
The accepted type contribution in halted split-2 was not separately post-audited.

Split-2's value worker used all six responses across two attempts. It had read the
real function window, but generated an invalid `render()` call and later introduced
assertions that booleans should be accepted. Baseline checks rejected these errors;
the full retry allowance did not recover. Its type worker had already accepted.
No candidate was manually corrected and no halted trial was restarted.

Keep one worker as the default for this tested workload. The larger specialist budget
did not demonstrate a reliability gain here; its higher cost is secondary to that
outcome. Six trials on one fixture cannot establish a general ranking. The next
useful qualification is broader real-repository work, retaining this failure as a
repair-regression case rather than adding fixture-specific prompt instructions.
