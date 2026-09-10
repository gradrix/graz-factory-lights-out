# Plan with bounded source windows

Type: task
Status: resolved

## Scope

Use the windows-v1 opt-in profile for direct structured planning as well as prepared
workers. Reuse revision-bound source windows and definition navigation, retain finite
read/attempt budgets, preserve no-source question grounding and legacy replay semantics.
Qualify a complete large-file feature from a fresh request through independent gates.
Retain failed trials and assistance. Do not change model, context limits, or the separate
256 KiB execution bundle limit. Missing context must never imply absent repository files.

## Answer

Implemented bounded direct planning with explicit read JSON, retained range/completion
metadata and source-free question review. build-feature uses it for windows-v1 policies.
Window output truncation is rejected and may use the remaining finite worker attempt;
legacy profiles retain their behavior. 492 tests / 25 Docker subtests pass.

One fresh complete feature accepted (model plan, implementation, eight tests, three
rejected mutants and integration); three other fresh runs halted, including the final
configuration's repeated read and incomplete plan. A focused navigation probe eventually
quoted return 41 from line 5001. This completes the protocol implementation and initial
qualification, not repeatability qualification. See [all evidence](../window-feature-qualification/README.md).

Follow-ups: issue 59 compares behavior-scoped test workers; issue 60 addresses navigation
and plan-coverage recovery. The complete execution bundle remains capped at 256 KiB.
