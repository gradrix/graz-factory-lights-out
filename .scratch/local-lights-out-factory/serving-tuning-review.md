# Serving tuning review — 2026-09-08

Recommendation: proceed with product implementation using the qualified vLLM configuration as a working default. Keep engine optimization open. The existing experiment establishes compatibility and some recovery behavior; it does not establish the best engine/configuration. A credible optimization comparison needs a representative worker workload and more than a quick flag adjustment.

This was a bounded documentation review. No new inference measurements, downloads, container changes, or service restarts were performed.

## What the baseline tells us

The [recorded comparison](serving-comparison.md) passed short synthetic requests at both context tiers on both engines. It used different memory fractions, different SSM settings, and very short output sequences. Its free-VRAM difference includes reserved cache capacity and desktop usage; it cannot support an intrinsic engine-efficiency ranking. SGLang was faster on several measured request types. The [vLLM profile](../../infra/serving/vllm-5090.example.json) has additional managed-lifecycle and internal-process-crash evidence, which is a practical reason to retain it while the product is built.

## Primary-source findings

The vLLM single-RTX-5090 recipe explicitly uses eager execution for Inferact NVFP4 because its tested graph capture ran out of memory. It also reports BF16 KV as a viable alternative to FP8. Thus those baseline choices are defensible, although they do not prove optimality for our smaller context/concurrency limits. The recipe supports the in-checkpoint MTP head using `--speculative-config '{"method":"mtp","num_speculative_tokens":3}'`; draft acceptance counters are needed to confirm useful speculation. Its separate DFlash2 option needs a draft checkpoint and vLLM 0.28 or later. These are candidates for measurement, not established improvements on this host. [vLLM Qwen3.8-27B recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)

SGLang's published recipes use RadixArk NVFP4 exports, including calibrated FP8 KV; our comparison used Inferact with BF16 KV. Its RTX 5090 validation uses 8,192 input and 1,024 output tokens at concurrency one. The explicit Mamba-cache size overrides the memory-ratio setting, so our one-slot pin with radix caching disabled is consistent with a single request. FlashInfer is the documented SM120 attention backend. Changing SSM state to BF16 requires workload accuracy validation. MTP and external draft configurations have distinct memory settings, and the documented SGLang source revision is not the inspected version identity of our image. A recipe-based SGLang comparison therefore needs checkpoint/runtime qualification, not just copying flags. [SGLang Qwen3.8-27B cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B)

## Effort and next experiment

The following are engineering judgments, not measured speedup predictions:

| Candidate | Expected scope | Recommendation |
| --- | --- | --- |
| Correct the engine-selection wording | Small documentation change | Do now; preserve baseline results. |
| Enable in-checkpoint MTP on vLLM | One candidate configuration, launcher support, realistic decode and correctness checks | First tuning experiment once worker requests exist. |
| Try graph capture with tighter allocations | Potential startup failures and retuning; our exact fit is unknown | Defer behind a useful baseline workload. |
| Change KV/SSM precision or checkpoint export | Memory/performance and correctness qualification | Do not treat as a free optimization. |
| Test SGLang with its recommended export and speculation | Download, immutable pins, runtime checks, equivalent workloads and recovery | Separate bounded evaluation after the worker loop. |
| Enable prefix caching | Needs repeated-prefix workload and cache/state budget measurement | Measure on actual Model turns. |

Resume artifact publication/reconciliation, then the broker and worker/model integration. During the planned pilot, capture real input/output lengths, time to first token, sustained decode speed, complete-turn latency, tool/structured-output validity, and task-level gate outcomes. Replay fixed requests at matching context and concurrency before comparing tuned candidates. Separate weight/state memory from reserved KV capacity, and retain a common desktop operating margin. Record every configuration and failed launch.

Reopen tuning earlier if model latency blocks the pilot, the service cannot fit required Worker views, or correctness/recovery fails. Otherwise a broad engine search now would delay implementation without yet measuring the work the Factory must perform.
