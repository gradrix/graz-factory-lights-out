# Planner recovery qualification — 2026-09-10

The final protocol produced valid plans in all six fixed fresh planner runs: three
navigation probes and three full-feature requests. Each used its first attempt and
two turns (one source read, one plan). All navigation rationales correctly quoted
`return 41` from the function at lines 5001–5002. Two of the three full features then
passed workers, generated tests and independent integration; one failed in its worker.
This is progress in a supervised small sample, not unattended reliability proof.

## Changes and authority

- Read-only planning excerpts are labeled directly by file and visible line range.
  File/source identities and omission records remain bound to the immutable input.
- Up to four requested windows persist across attempts. A smaller repeated request
  cannot discard a wider retained request. Redundant reads receive validation feedback.
- Invalid plans and truncated planning output use remaining turns before giving up.
  Missing requirement IDs are named explicitly. Grounded requirement citations survive
  later errors. No tasks or product policy are supplied by the controller.
- Window planner schemas omit request_digest. The controller fills an omitted identity
  from the exact bound request, and records that action. An explicitly supplied wrong
  identity still fails validation. This removes hash-copying work from the LLM without
  weakening source/scope/requirement checks or changing canonical proposal records.
- Discriminated schema feedback reports field/message details without truncated input
  previews that a model might copy as valid data.

Legacy profiles keep their old planning/retry semantics. Source-free question grounding
keeps its existing identity and quotation checks; source windows are not shown during
that review. Attempts remain limited to two, each with three turns. The output/context
budgets, model/deployment and worker protocol were not expanded for this comparison.

## Frozen runs and failures

Each campaign froze three navigation/feature pairs before inference. Requests, source,
model and gates came unchanged from the prior window-feature qualification fixtures.
No plan, generated candidate, or missing requirement was manually corrected.

| Campaign | Navigation plans | Feature plans | Complete features |
| --- | ---: | ---: | ---: |
| Intermediate v1 | 0/3 | 3/3 | 0/3 |
| Final v2 | 3/3 | 3/3 | 2/3 |

V1 retained reads and used remaining turns, but navigation plans repeatedly copied an
invalid/abbreviated request hash; feedback echoed invalid input previews. All three
navigation attempts exhausted six responses. The three feature planners succeeded
in two turns, but their workers halted. These outcomes remain recorded.

V2 adds controller-bound omitted identities and cleaner schema handling. All six plans
succeeded in two turns, within their first attempts. Largest planning prompts were
4,580 tokens for navigation and 4,807 for full features. Both accepted features replayed
without new events/inference. The remaining feature exhausted its first worker attempt,
then failed its pinned source-preservation check after retry. It was not accepted.
Worker failures remain a separate reliability boundary.

The complete Docker regression suite passed 497 tests and 25 subtests, followed by the
added narrower-read retention test passing with the targeted planner suite. Lint, typing
and four historical replay checks pass. New tests cover retained reads across retries,
finite exhaustion, exact missing-requirement feedback, omitted/wrong identity handling,
sanitized schema feedback, source labels and range preservation. Existing tests retain
source-free question review and legacy behavior.

## Reproduction and evidence

```sh
.venv/bin/python .scratch/local-lights-out-factory/planner-recovery/campaign.py \
  --output .gflo/evidence/planner-recovery-fresh
```

The directory must be fresh. The harness reconstructs and verifies the exact source
recipe from sibling window-feature-qualification, and uses its pinned fixtures. It
performs no model planning corrections or candidate edits. Current code reproduces
v2 behavior; inference outcomes can vary. For intermediate v1, apply the retained
v1-implementation.patch to an isolated baseline 6ce54d9 checkout and supply this harness.

v1-results.json and v2-results.json retain planner outputs, source-label/byte metadata,
validation feedback, controller identity bindings, worker outcomes and evidence
identities. report.py exports results without resuming halted work; accepted replay is
checked. Raw `.gflo/evidence/planner-recovery-v1` and `-v2` stores require separate
transfer for byte-exact historical replay. Execution remains limited to 256 KiB.

Owner preference: reliable completion and verified coverage take priority over local
inference token cost. Issue 63 will compare specialists with full per-worker retry
budgets, allowing greater total expenditure. Issue 59's equal-budget result does not
rule out a reliability benefit from that additional capacity. Next implementation is
issue 61, the observed new-file draft repair problem.
