# What makes local review reliable enough to gate the next stage?

Type: Prototype
Status: active
Blocked by: none

Flash without thinking caught the ten seeded causes but accepted the independently discovered Decimal precision defect twice, even after a general counterexample prompt improvement. It also invented invalid-input requirements for the corrected money control. Dense Qwen without thinking lost a critical case to malformed output in the first set. Preserve all results; stage 2 is not accepted.

Experiment next: enable bounded local reasoning for the same fresh read-only review on a small discriminating set (correct money, original defective money, another seeded defect), keeping the 120-second request budget. If reasoning still fails, test read-only executable counterexample probes before expanding autonomy. Any revised prompt/profile requires full repeated-set qualification plus held-out coding and semantic checks; it does not turn repeated cases into unseen evidence.

Evidence: .scratch/.sflo/03-autonomy-review/flash-first.json, dense-first.json, flash-v2.json, semantic-receipt.md. Fixture v2 corrects the control/oracle while preserving objective and supplemental original false acceptance.

Unbounded medium reasoning spent the 8192-token output allowance without a final JSON verdict on both money inputs (~92 seconds each); it did identify the simple transition defect. The installed llama.cpp help advertises a separate reasoning budget. Upstream maintainer guidance documents per-request `thinking_budget_tokens` when no CLI budget is fixed: https://github.com/ggml-org/llama.cpp/discussions/21445. Next discriminating run uses 1024 thinking tokens inside the original 4096 total output cap and 120-second request limit. No serving restart or context reduction.

## Current outcome

Bounded 1024-token thinking within4096 total passed the repeated Flash defect/control gate: 10/10 seeded, all critical, 2 false blocks, no format failures, supplemental defect caught. Dense same-budget comparison failed (7/10, critical miss,4 format failures,supplemental miss). Keep Flash serving serialized coder/reviewer assignments. This qualifies the review experiment only; correlated misses remain possible.

Cohort A coding failed7/12. Runtime corrections for unnecessary questions and unreviewable generated artifacts passed independent controller QA. New unused three-module cohort B is running; semantic evidence and its full numeric gate still block stage graduation. See execution run and docs/evidence/autonomy-stages.md.

Further B evidence: generated-test execution was missing from controller verification; local revision c17821c now runs present Python unittest suites, with real frozen-defect and repair-loop probes. Task09 stopped safely when question triage did not return an exact grounding quote. Documentation omissions and computational-boundary misses remain semantic risks. Final independent QA is currently blocked by account usage limits; model batch collection continues.

Final current receipts: B numeric gate passes11/12 plus ambiguity; full-objective inspection identifies nine deliveries without a requirement gap. c17821c known-case real repair passed on attempt3,350.61s, after project-test and review failures; both check suites passed readback. This does not rewrite B or establish an unseen revised-candidate rate. Next: close fresh-agent QA, define validation/equality boundaries explicitly in new fixtures and qualify repaired behavior before environment preparation.
