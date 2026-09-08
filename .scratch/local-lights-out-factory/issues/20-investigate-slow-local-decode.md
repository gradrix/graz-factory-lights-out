# Investigate slow local decode

Type: task
Status: resolved
Blocked by: 18

## Scope

Investigate the measured approximately 10 output tokens/second on the current RTX 5090 / vLLM / Inferact Qwen3.8-27B-NVFP4 profile. Preserve the working service and coding-correctness baseline. Use bounded, one-variable experiments before a broader engine comparison.

## Evidence

The user questioned the earlier 7.15-second, 75-output-token turn. New instrumentation in the durable loop measured 11.96 seconds in generation HTTP for 112 output tokens, with about 0.05 seconds total for model listing and tokenization. A direct replay measured 11.33 seconds HTTP, 11.11 seconds server decode, 0.21 seconds prefill and approximately 0.000015 seconds queueing. Thus client overhead and queueing do not explain this fixture's latency. This is a reproducible decode-speed observation, not proof of the underlying configuration/hardware cause.

Reproducer (local retained debug harness):

```sh
.venv/bin/python .gflo/debug/serving_latency_probe.py
```

It replays the captured synthetic request and records vLLM metric deltas. Exit 1 flags the observed symptom: at least five seconds for at most 128 completion tokens. That threshold is a diagnostic trigger, not a product SLO or general hardware benchmark. Raw result/request identity: `.gflo/evidence/durable-loop-smoke-v1/latency-probe.json`; raw response is beside it. Ensure no concurrent serving requests when comparing global metric deltas.

## Acceptance

- Separate queue/prefill/decode and client time on a fixed workload; retain raw requests, output correctness, runtime/checkpoint/settings and host/GPU conditions.
- Diagnose actual decode bottlenecks before claiming a cause: inspect CPU throttling/kernel-launch behavior, GPU utilization/clocks and relevant engine kernels/configuration.
- Compare any supported change against the fixed workload and trusted cases; preserve failures, working profile and recovery behavior.
- A speedup must retain correct results. If tuning needs substantial time, retain findings and continue the diagnostic pilot with the measured limitation, following the user's earlier preference for product progress.

## Comments

2026-09-08: The official recipe describes this as a dense 27B model and recommends eager mode for its single-5090 configuration; it also documents MTP as an available experiment. Neither fact establishes the expected speed of this exact host/profile. See [vLLM's recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B) and [the prior bounded tuning review](../serving-tuning-review.md). No serving settings were changed during loop implementation or the timing replay. Diagnosis remains open; no performance fix is claimed.

2026-09-08 bounded experiment: enabling compilation/CUDA graphs fit this exact single-sequence profile and reduced twelve-task median generation HTTP from 9.71s to 1.94s, preserving 12/12 accepted outcomes. CPU quota throttling was negligible. Graphs are selected for further development; graph-specific recovery qualification and precise bottleneck attribution remain open. Cold first request incurred 20.71s prefill. See [pilot results](../pilot-results.md); this does not establish globally optimal settings or an engine winner.

## Answer

Resolved the bounded performance investigation: compilation/CUDA graphs improve the fixed coding workload while retaining 12/12 acceptance. Qualified stopped restart (35.14s including structured smoke), automatic internal engine-crash recovery (33.45s including smoke), same container/image/volume mounts, and a subsequent real paging migration accepted in one Attempt. [Recovery evidence](../graph-recovery-verification.json) retains the failed order-sensitive harness run too. This establishes a practical serving-mode improvement, not an exact kernel-level cause or globally optimal backend. Broader in-flight fault campaigns remain Stage 2 work.
