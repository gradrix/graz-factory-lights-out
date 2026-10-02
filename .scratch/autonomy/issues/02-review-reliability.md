# What makes local review reliable enough to gate the next stage?

Type: Prototype
Status: active
Blocked by: none

Flash without thinking caught the ten seeded causes but accepted the independently discovered Decimal precision defect twice, even after a general counterexample prompt improvement. It also invented invalid-input requirements for the corrected money control. Dense Qwen without thinking lost a critical case to malformed output in the first set. Preserve all results; stage 2 is not accepted.

Experiment next: enable bounded local reasoning for the same fresh read-only review on a small discriminating set (correct money, original defective money, another seeded defect), keeping the 120-second request budget. If reasoning still fails, test read-only executable counterexample probes before expanding autonomy. Any revised prompt/profile requires full repeated-set qualification plus held-out coding and semantic checks; it does not turn repeated cases into unseen evidence.

Evidence: .scratch/.sflo/03-autonomy-review/flash-first.json, dense-first.json, flash-v2.json, semantic-receipt.md. Fixture v2 corrects the control/oracle while preserving objective and supplemental original false acceptance.

Unbounded medium reasoning spent the 8192-token output allowance without a final JSON verdict on both money inputs (~92 seconds each); it did identify the simple transition defect. The installed llama.cpp help advertises a separate reasoning budget. Upstream maintainer guidance documents per-request `thinking_budget_tokens` when no CLI budget is fixed: https://github.com/ggml-org/llama.cpp/discussions/21445. Next discriminating run uses 1024 thinking tokens inside the original 4096 total output cap and 120-second request limit. No serving restart or context reduction.
