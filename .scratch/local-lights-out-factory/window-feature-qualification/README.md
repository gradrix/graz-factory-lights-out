# Window-based planning and complete feature qualification

The same pinned local model planned and implemented a feature in the recorded
10,002-line / 207,814-byte source file, then wrote tests and passed combined checks.
Codex selected the task, wrote the independent gates and implemented the generic
protocol. The model supplied the plan, source edits and tests; no manual candidate or
plan correction was supplied. This is a supervised qualification, not an autonomous
product discovery benchmark.

## Complete-feature trials

- v1 halted: the implementation eventually passed, but the test worker repeated test
  functions until it exhausted 4,096 output tokens. The incomplete response was not
  accepted. Its ledger and response remain recorded.
- v2 accepted: one planning response, three implementation responses and two test
  responses. Maximum prompt 3,513 tokens, maximum visible source 2,821 bytes. The
  implementation needed development feedback about exact input types. Eight generated
  tests passed the real implementation and rejected three injected faults. Integration
  reran behavior and test checks against the combined candidate. Replay added no events.

- v3 halted: the updated planner read the function at line 5001 and produced its plan
  in two turns. The implementation passed after two attempts, but the test response
  again hit its output limit. Compact guidance alone did not prevent recurrence.

- v4 halted in planning: after a repeated read, its next proposal omitted a requirement.
  Structural validation rejected it, and no worker was started. This run used the final
  implementation including retryable worker-output truncation; it did not exercise that
  retry on the GPU. That change is covered by protocol and controller tests.

Overall, one of four fresh complete-feature trials accepted. They span the documented
protocol changes and are not a fixed-configuration statistical benchmark. The final
configuration has not yet repeated the full-feature success; keep it experimental.

After v3, window-profile output truncation became a retryable worker-output failure,
with compact-output diagnostic, within the existing attempt limit. Partial output is
never applied; malformed accounting and other infrastructure failures still halt.
Legacy profiles retain their original behavior. CPU tests cover retry exhaustion and
legacy failure classification.

Between v1 and v2, the generic window-worker instructions gained compact new-file/test
advice and single JSON encoding guidance. The task, independent gates, model deployment
and per-attempt budgets remained fixed. Fresh trials use distinct feature identities and
ledgers; earlier attempts were not reset.

## Planner navigation probes

A separate draft-only probe required the planner to inspect the current function body
and quote its return statement in the rationale. Its target was outside all initial
headers. These probes did not execute plans or accept code.

- v1 asked the human for available source instead of reading it. Source-free question
  review correctly declined to invent the answer, leaving needs-info.
- v2 used read_window after an explicit JSON read example was added, but repeated reads
  and exhausted both attempts.
- v3 received explicit completed-read metadata alongside the supplied excerpts. It still
  repeated reads, then produced a valid plan within its second attempt (five responses),
  correctly quoting `return 41` at lines 5001–5002. Maximum prompt 4,737 tokens.

These failures show that navigation efficiency remains a weakness. Exact read examples
and completion metadata are generic protocol changes, with no fixture-specific symbols,
paths, line numbers, expected return values or algorithms embedded in factory code.

## Reproduction and retained evidence

Run the checked-in harness from the repository root using its virtualenv, a fresh output
directory and the pinned provisioned local model and offline Docker image:

```sh
.venv/bin/python .scratch/local-lights-out-factory/window-feature-qualification/reproduce.py \
  --fixture .scratch/local-lights-out-factory/window-feature-qualification/window-feature-v2-fixture.json \
  --output .gflo/evidence/window-feature-fresh
```

Navigation fixture files use the same command. Source is reconstructed from the exact
recipe and checked against its retained identity. Fixture files contain requests,
policy, gates and model/deployment identities; results retain responses, token counts,
window ranges, ledger outcomes and evidence digests. New inference can differ from
historical responses. Raw `.gflo/evidence/window-feature-v*/` and
`window-planner-navigation-v*/` artifact stores require separate transfer for exact replay.
The initial source is synthetic and the product policy is precise. Execution still uses
a complete SourceBundle capped at 256 KiB; no million-line build capability is claimed.

The next comparison is one test worker versus behavior-scoped test tasks under the same
aggregate budget. Separate test files avoid concurrent ownership of a shared mutable
file. See issue 59; no multi-worker advantage has yet been measured.
