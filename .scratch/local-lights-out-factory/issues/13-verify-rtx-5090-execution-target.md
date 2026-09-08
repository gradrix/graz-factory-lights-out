# Verify the RTX 5090 execution target

Type: task
Status: resolved
Assignee: codex

## Scope

Record host/container GPU identity and reproducible image/checkpoint/tokenizer pins. Verify execution controls, available storage and model startup at concurrency one. Compare focused SGLang and vLLM profiles at supported 8K and 16K tiers; preserve differences and raw evidence.

## Acceptance

- Container GPU access and worker resource/authority restrictions have recorded evidence, including bounded enforcement tests before worker execution.
- Serving startup/readiness/synthetic structured output, repeated startup, stopped restart, drift refusal and cache preservation are exercised on exact pinned profiles.
- Serving comparison reports latency, peak VRAM and recovery; coding scores remain pending the live pilot.

## Comments

2026-09-08: Begun on the actual RTX 5090 under WSL2. See [target verification](../target-verification.md). Initial container probes pass; no inference endpoint is ready. This task remains incomplete. The active turn has checkpointed; a subsequent session may resume this claim.

### Serving comparison and provisional selection — 2026-09-08

The user authorized benchmarking and deciding. [The comparison](../serving-comparison.md) selects vLLM for the first worker pilot. Both engines passed 24 scored synthetic requests each across 8K/16K, plus thinking, over-budget rejection/recovery and stopped restart probes. vLLM retains approximately 1.5 GiB additional free GPU memory at 16K; SGLang was faster on long JSON. Exact checkpoint files, images, options, failed calibration runs, raw responses and sampled VRAM are preserved.

The selected managed vLLM profile is running and passed end-to-end synthetic checks, repeated-up reuse, running drift refusal, same-container/cache stop/start and automatic recovery after killing its internal EngineCore process. Explicit `docker kill` is a separate manual lifecycle action and suppressed automatic restart; `serve.py up` resumed it. No deliberate OOM recovery or coding ability is claimed. The SGLang comparison used direct pinned snapshot containers; its managed profile is configuration-validated only.

This task stays claimed because its execution/isolation acceptance includes bounded memory/PID enforcement faults and the future worker/broker boundary, which these serving probes do not establish. Continue core development with [artifact publication/reconciliation](15-publish-and-reconcile-artifacts.md); engine choice is no longer a blocker.

### Tuning review — 2026-09-08

The [bounded review](../serving-tuning-review.md) corrects the prior selection rationale: free VRAM is confounded by unequal cache reservation. Keep vLLM as the existing working default; an optimized-engine decision remains open. No new inference run or configuration change was made. Defer tuning until representative worker requests exist, following the user’s preference to prioritize product implementation.

## Answer

The initial Stage 0 target is qualified for the fixed small Python broker profile and existing vLLM synthetic serving profile. [Broker qualification](../broker-verification-results.json) now adds real bounded OOM/PID enforcement, effective security controls, clean validation separation, host/credential/network exclusion and cleanup/reconciliation evidence to the earlier serving/GPU checks. Task 16 is resolved. This closes the target prerequisite for the forthcoming diagnostic pilot, not a blanket isolation, optimized-engine, coding-capability or unattended-operation claim. Engine optimization remains deferred by the user’s accepted priority; general capabilities and long-run operational controls require later qualification.
