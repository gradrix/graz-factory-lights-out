# Test-worker decomposition comparison — 2026-09-10

Decision: keep one bounded test worker as the default for this workload. The factory
can run separate behavior-scoped workers and integrate their files, but this small
comparison found no reliability advantage and higher cost from splitting. Use splitting
selectively when a larger suite has independently checkable responsibilities. This is
not evidence that one worker is always better.

## Frozen comparison

Both conditions start from the exact accepted clamp implementation in the 10,002-line
fixture. The same original behavior requirements, local model/deployment, 12,288-token
contract budget and 4,096-token output limit apply. No factory runtime code or prompts
were changed during this campaign (baseline 99dcfd9).

- Solo: one worker writes tests/test_all.py, with two attempts of three turns each.
- Split: a values/caller worker and a types worker write separate pytest files, each
  with one attempt of three turns. They run sequentially on the same GPU. Each task
  has independent acceptance; the combined suite is checked afterward.
- Both reserve six responses / 73,728 tokens per trial. Unused attempts cannot be
  borrowed across split workers. This allocation tradeoff is part of the comparison.
- Three trials per condition, with order frozen before inference: solo-1, split-1,
  split-2, solo-2, solo-3, split-3. No attempt was reset or replacement trial added.
- Codex supplied the reviewed task groups to isolate test writing from planner
  reliability. This does not evaluate autonomous task decomposition.

Reference tests preflighted all four original gate variants before any model calls.
They checked the real implementation and rejection of unclamped, constant-return,
incorrect caller-format and type-permissive mutants. Gates also reject source mutation.
An earlier preflight harness used a bytes property as a method and stopped before
inference; corrected preflight and all campaign records remain separate in raw evidence.

## Outcomes

| Condition | Original gate acceptances | Reusable after review | Total tokens, all 3 runs | Model-call seconds |
| --- | ---: | ---: | ---: | ---: |
| One worker | 2/3 | 2/3 | 20,128 | 62.8 |
| Two scoped workers | 2/3 | 1/3 | 30,807 | 116.5 |

Splitting used 53% more tokens in this sample. Model-call time includes client work;
it excludes Docker validation and is not a complete build-time benchmark. With only
three runs per condition, these are observations, not a statistical ranking.

Solo-2 created a test file with a missing colon, then repeatedly attempted whole-file
replacement instead of using window edits on the retained draft. Both attempts ended
without acceptance. Split-3 exhausted its types worker's output allowance and one
available attempt; its values worker never started. Splitting did not prevent long output.

The originally accepted solo suites had 10 and 18 test functions, with no exactly
duplicate function bodies. Split suites had 19 and 15 functions, with three and four
exact duplicate bodies respectively. This AST metric is narrow: it ignores names and
decorators, and cannot measure semantic redundancy or pytest parametrization quality.
Review also found the types workers generating value/default checks outside their
assigned behavioral focus. More workers did not automatically produce less duplication.

## Post-run coverage audit

Review noticed that split-1's values contribution omitted a no-argument/default test.
Two additional fault types—wrong default and accepted integer subclasses—were applied
uniformly to the applicable accepted task requirements. These were held out of the
original gates and were never fed back to model workers. The audit checked both
contributions and the integration requirement IDs available in the retained records.

The default mutant survived the values file alone, proving its assigned coverage gap.
The combined suite caught it only because the types worker also tested the default.
An AcceptanceFinding was recorded against the values contribution, and feature replay
correctly blocked reuse without new inference or ledger events. Historical acceptance
and the originally passing combined checks remain unchanged. Other audited accepted
contributions detected their applicable held-out faults. No generated test was manually
repaired. This demonstrates why per-task checks must enforce assigned coverage even
when combined tests happen to pass.

A separate provenance issue was noticed: split integration atoms inherit requirement
IDs from the last task, although their pinned combined gates check all four fault types.
This did not bypass the combined gates; it is recorded as issue 62. Draft repair is
issue 61. Planner navigation/coverage recovery remains issue 60.

## Reproduce and inspect

```sh
.venv/bin/python .scratch/local-lights-out-factory/test-decomposition/campaign.py \
  --output .gflo/evidence/test-decomposition-fresh
```

The output directory must be new. `--preflight-only` validates reference gates without
model calls. The source recipe, accepted function and file hashes reconstruct the exact
input without copying the 208 KiB file into every fixture. The campaign writes plans,
results and its frozen schedule. Production source remains read-only to workers.

`results.json` retains original trial outcomes, current ledger snapshots, model responses,
costs, generated accepted tests and replay status. `audit-results.json` retains findings
and held-out execution outcomes. `summary.json` contains aggregate metrics. `report.py`
can export/replay an existing campaign without restarting halted workers. `audit.py` is
a post-review tool for these checked-in results; it refuses an existing audit output to
avoid appending duplicate findings. Reference test text is used only for gate preflight,
never given to model workers. No manual plan/candidate correction, model change, shared
file mutation or new scheduler was used. Review time was not instrumented, so no numeric
claim about reduced human effort is made.

Raw .gflo/evidence/test-decomposition-v1 and -v2 stores need separate transfer for exact
historical replay. These are supervised tests on a synthetic source file, not proof of
large-product autonomy or arbitrary execution sizes; SourceBundle still caps at 256 KiB.
