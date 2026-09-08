# Serving comparison — synthetic-serving-v1

Status: conservative baseline complete; optimized engine comparison deferred. vLLM remains the working default, not an established performance winner.

## Predeclared comparison

Run the same Inferact/Qwen3.8-27B-NVFP4 snapshot (`6128240ebaf4eaa7bad2b3d1c72c37d677c5f462`) on vLLM and, if supported, SGLang. If SGLang requires another export, record that as a comparison of complete configurations, not an isolated engine comparison. Exact cached file hashes and runtime identities are retained in `.gflo/evidence/serving-comparison/`.

Use one GPU, one inference request at a time, 8,192 and 16,384 total context tiers, BF16 KV cache, no speculative decoding, no prefix caching, temperature zero, seed 42 and thinking disabled for the baseline. The initial unscored vLLM FP8 launch warned of missing calibration scales; its logs are retained and BF16 is the conservative comparison configuration.

At each tier, run one unscored plain-response warm-up and three repetitions of four synthetic cases: exact plain response, strict JSON-schema response, parsed tool call with exact arguments, and JSON after approximately tier-minus-2K input tokens. Require every scored response to pass shape/value/finish/token-accounting checks. Tool calls are parsed but never executed. Record raw requests/responses, elapsed times and one-second total-device VRAM samples; desktop GPU usage is included.

Record startup and stopped-container restart behavior with the immutable checkpoint mounted read-only and runtime cache preserved. Test over-budget request rejection followed by a valid request. Thinking-enabled probes are supplementary compatibility evidence. Do not claim deliberate OOM fault qualification unless exercised.

Prefer a configuration that passes both context tiers and recovery checks. If both pass, use measured latency and setup reliability to choose the provisional default; three repetitions are diagnostic, not a statistically strong performance ranking. The twelve-task real-model worker pilot remains authoritative for coding usefulness.

Sources checked: [vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B), [SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B).

## Configuration adjustments retained as evidence

SGLang's `--language-model-only` switch rejects this Qwen architecture; the supported general VLM switch is `--language-only`. The failed invocation is retained. At static memory fraction 0.85, its memory guard rejected the post-weight cache budget. Retrying at 0.90 allocated 23,036 BF16 KV tokens and reached readiness. This is a documented no-speculation setting, but the actual observed fit is specific to the pinned Inferact checkpoint and desktop memory use. vLLM remains at 0.85.

The initial successful SGLang startup took approximately 47 seconds; vLLM's corresponding cold 8K startup took approximately 97 seconds, with a further 57-second first plain request. Initial JIT cache states differ, so these are operational observations rather than a clean engine startup-speed ranking.

## Decision and measured results — 2026-09-08

**Retain vLLM as the working default for the Stage 1 worker pilot.** Both engines passed the synthetic probes. The original preference based on approximately 1.5 GiB additional free VRAM is withdrawn: memory fractions and reserved cache capacities differ, so free VRAM does not establish engine efficiency. vLLM has additional managed-lifecycle and engine-crash recovery evidence, which supports keeping the existing service during implementation. Neither engine was tested with its best configuration. The [bounded tuning review](serving-tuning-review.md) found no obvious quick correction; meaningful optimization is deferred until representative Worker turns exist, as the user prefers product progress over a long tuning exercise.

| Engine | Total context tier | Scored passes | Median JSON | Median tool call | Median long JSON | Sampled peak GPU use |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| vllm | 8192 | 12/12 | 1.16 s | 2.66 s | 1.74 s | 29,969 MiB |
| vllm | 16384 | 12/12 | 1.53 s | 2.62 s | 3.21 s | 30,119 MiB |
| sglang | 8192 | 12/12 | 0.96 s | 2.67 s | 1.44 s | 31,631 MiB |
| sglang | 16384 | 12/12 | 1.19 s | 2.68 s | 2.41 s | 31,639 MiB |

Long requests contained 6,181 input tokens at the 8K tier and 14,373 at 16K. Both engines emitted the expected values, valid completion reasons and coherent token usage. Tool-prompt accounting differed (289 versus 300 input tokens), despite the same submitted payload and checkpoint/tokenizer files; the runtime's tool rendering is part of this configuration comparison. VRAM figures include the desktop and are sampled peaks, not guaranteed transient maxima. At 16K, the observed free remainder was about 2.43 GiB for vLLM and 0.95 GiB for SGLang.

The explicit plain-response warm-up took about 55–57 seconds on fresh vLLM containers and under a second on these SGLang runs. Both startup paths also do their own warm-up, and cache states differ; those times are not a clean engine speed ranking. Median request figures include only the three scored repetitions per case. Cold vLLM readiness plus first generation requires a larger deadline than routine warmed requests.

## Runtime and model provenance

The existing Inferact/Qwen3.8-27B-NVFP4 revision `6128240ebaf4eaa7bad2b3d1c72c37d677c5f462` was verified against the Hub revision identity and all cached blob names. All snapshot files matched their cache hashes; their SHA-256 digests were independently recorded. Total cached snapshot bytes verified: 26,404,387,417. Weights were reused through read-only mounts, not downloaded or converted.

- vLLM: `0.28.0`, PyTorch `2.13.0+cu129`, Transformers `5.15.1`; image digest `sha256:ac259a0111c6cf462a72e449962b84f7a624b5cbec24bd7d9ec3b67d40ffd1bf`.
- SGLang: `0.0.0.dev1+g5f55db35e`, PyTorch `2.13.0+cu130`, Transformers `5.12.1`; image digest `sha256:616a3e97f45191af975896cfa644279096cb31bd408a071c2e99ca7209c3cafe`. The recipe tag resolved to this actual build; do not substitute the documentation's source checkout commit for the inspected image identity.

This is the same checkpoint but different complete serving configurations. SGLang used explicit float32 SSM state, disabled graph backends, a one-entry Mamba cache and memory fraction 0.90. vLLM used its default SSM settings, eager text-only execution and memory fraction 0.85. Both used BF16 KV, 2K prefill chunks, one admitted request and no prefix cache/speculation. The profiles and raw launch arrays preserve these differences.

## Managed service and recovery

The selected [managed vLLM profile](../../infra/serving/vllm-5090.example.json) is live-validated with explicit image/model/tokenizer pins, read-only offline model cache, 36 GiB memory, no extra swap allowance, three CPUs, 1,024 PIDs and loopback binding. It also passed one complete four-case 16K check through the actual launcher.

Repeated `up` reused the same container in about 0.25 seconds. A changed running context limit was refused without replacement. Launcher `down`/`up` retained the container ID and cache mounts; API readiness returned in approximately 30.1 seconds, followed by a passing structured smoke test.

The initial explicit `docker kill` did **not** trigger automatic restart: it was a manual Docker lifecycle action, and the stopped service resumed successfully through `serve.py up`. This distinction is consistent with [Docker's restart-policy semantics](https://docs.docker.com/engine/containers/start-containers-automatically/). That observation is retained rather than being called an engine crash failure.

A separate SIGKILL delivered to the internal `VLLM::EngineCore` process caused the container to restart automatically under `unless-stopped`; readiness returned in approximately 36.1 seconds and the structured smoke test passed afterward. This qualifies this process-crash path, not GPU OOM recovery, arbitrary hangs, or an unattended factory run.

The [SGLang profile](../../infra/serving/sglang-5090.example.json) remains available. Its new managed configuration is validated by the loader, but the live SGLang comparison used direct containers mounting the exact snapshot. Do not report its managed launcher path as live-qualified.

## Evidence and remaining work

[Machine-readable results](serving-comparison-results.json) contain the measurements and identities. Raw startup logs, failed launches, requests/responses, GPU samples, lifecycle observations and helper commands remain in `.gflo/evidence/serving-comparison/` on this checkout. [The evidence manifest](serving-evidence-manifest.json) records their file hashes. Raw evidence is ignored by Git and must be copied separately for a host migration.

Seven stopped comparison containers were removed after their logs/configuration were archived. Both runtime images, cache volumes and the selected `gflo-vllm` service remain. No generated tool call or model-produced code was executed.

Continue with [immutable artifact publication/reconciliation](issues/15-publish-and-reconcile-artifacts.md), then worker/broker/model-client integration and the twelve-task real-model pilot. Actual artifact/output validation, worker isolation qualification, enforced-resource fault fixtures, long unattended recovery and coding-quality scoring are still pending.
