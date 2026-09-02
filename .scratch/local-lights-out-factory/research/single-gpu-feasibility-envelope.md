# Single-GPU feasibility envelope for Qwen3.8-27B

Research date: 2026-09-02  
Target: Linux, one GeForce RTX 5090 (32 GB VRAM), 64 GB system RAM  
Decision supported: what model-serving envelope the local Factory may safely assume

## Verdict

Qwen3.8-27B is feasible as the **serial inference worker** of this Factory on the target machine, but only with an aggressive 4-bit checkpoint and deliberately bounded requests. It is not evidence-backed to treat the model's advertised 262,144-token context, concurrent serving, or vendor agent benchmark scores as a reliable lights-out operating envelope.

The best currently documented baseline is SGLang plus `RadixArk/Qwen3.8-27B-NVFP4`, FP8 KV cache, one request in flight, and an 8K–16K normal Work-atom context budget. A 32K total-context ceiling is a defensible first implementation target. Contexts around 64K–96K are an experimental tier; the native 262K window is a model capability, not a demonstrated one-card service capacity. Multiple logical agents should queue work and share one model server rather than require simultaneous decoding.

This is enough for an atomic factory because model calls can be cheap, repeated, and serialized while durable state, source code, graphs, and deterministic validators remain outside the model. It is not enough to make a monolithic product request reliable by itself. The orchestration must assume individual calls can choose the wrong tool, produce semantically wrong schema-valid data, loop, or fail a coding task.

## What is documented versus inferred

### Hardware and architecture facts

- NVIDIA specifies the RTX 5090 as a Blackwell card with 32 GB GDDR7 and a 512-bit memory interface ([NVIDIA specification](https://www.nvidia.com/en-eu/geforce/graphics-cards/50-series/rtx-5090/)).
- Qwen describes Qwen3.8-27B as a dense 27B hybrid model with 64 language layers: 48 Gated DeltaNet linear-attention layers and 16 full-attention layers. It has four KV heads of dimension 256 and a native maximum position length of 262,144 tokens ([Qwen model card](https://huggingface.co/Qwen/Qwen3.8-27B-FP8), [checkpoint configuration](https://huggingface.co/Qwen/Qwen3.8-27B-FP8/blob/017b9c7af6b5689d5dd426a76e0bc077eb5ca20a/config.json)).
- The official FP8 repository contains about 30.87 GB decimal / 28.75 GiB of safetensor files. Its tensor inventory is 24.70B FP8 and 3.08B BF16 parameters, so weight storage alone nearly fills a 32 GiB card. Qwen calls its block-size-128 FP8 metrics “nearly identical” to the original model, but that is a vendor claim and does not cover the third-party NVFP4 checkpoint ([Qwen FP8 repository](https://huggingface.co/Qwen/Qwen3.8-27B-FP8/tree/017b9c7af6b5689d5dd426a76e0bc077eb5ca20a)).
- SGLang's model-specific cookbook says BF16 does not fit and its FP8 checkpoint does not produce a serviceable 32 GB configuration. It recommends NVFP4, whose runtime weights it reports at about 16.5 GB. Unlike a paper estimate, its RTX 5090 cells were actually exercised at 8,192 input + 1,024 output tokens, concurrency one ([SGLang cookbook at tested revision](https://github.com/sgl-project/sglang/blob/1cf2b8c54d81802abc15dcf23a29b9cc687bc01e/docs/cookbook/autoregressive/Qwen/Qwen3.8-27B.mdx), [current recipe configuration and validation notes](https://github.com/sgl-project/sglang/blob/f8cbf000f4a5bfd86d3fb7c1e2d6c8fb12339d0e/docs/src/snippets/configs/Qwen/qwen3.8-27b.jsx)).
- RadixArk states that its NVFP4 derivative uses dynamic NVFP4 W4A4 for MLP and output-head tensors, FP8 for attention weights, and BF16 for MTP and vision tensors. The repository's safetensors occupy about 21.92 GB decimal / 20.41 GiB on disk; disk size must not be confused with SGLang's reported loaded-weight footprint ([NVFP4 model card](https://huggingface.co/RadixArk/Qwen3.8-27B-NVFP4/blob/319f741cce68d7914884900c138a1fbb70a42f30/README.md)).

### Memory and context envelope

For the 16 full-attention layers, a conventional KV-cache estimate follows directly from the published geometry:

```text
KV bytes/token = 16 layers × 4 KV heads × 256 dimensions × K-and-V × bytes/value
               = 65,536 bytes/token with BF16
               = 32,768 bytes/token with FP8
```

At FP8, attention KV alone is about 1 GiB per 32K tokens, 2 GiB per 64K, 3 GiB per 96K, and 8 GiB at 262,144 tokens. That is not the complete serving cost. Each live request also needs Gated DeltaNet state, runtime workspaces, CUDA graphs, activations during prefill, and memory for the server.

SGLang quantifies the hybrid-state cost more usefully than the simple KV estimate. One GDN state slot is 153.9 MB with FP32 state or 78.4 MB with BF16 state. Depending on its radix-cache strategy, a running request reserves several slots. On an RTX 5090 with no speculative decoding, SGLang measured pools of 68,588 KV tokens with FP32 GDN state and 97,280 with BF16 state. These are pool capacities, not proof that useful recall and coding quality remain intact at those lengths ([SGLang cookbook](https://github.com/sgl-project/sglang/blob/1cf2b8c54d81802abc15dcf23a29b9cc687bc01e/docs/cookbook/autoregressive/Qwen/Qwen3.8-27B.mdx#L275-L290)).

Consequently the Factory should begin with these policy tiers:

| Tier | Total input + output budget | Status | Intended use |
|---|---:|---|---|
| Routine | 8K tokens | documented boot/serve neighborhood | Default Work atom; leaves generous output and runtime margin |
| Large atom | 16K tokens | conservative inference from measured pool | Only when retrieval cannot form a smaller sufficient packet |
| Hard initial cap | 32K tokens | must be locally acceptance-tested | Exceptional synthesis/review, never a default |
| Experimental | 64K–96K tokens | near the measured one-stream KV envelope | Benchmark only; no unattended dependency until quality and OOM behavior pass |
| Advertised native | 262,144 tokens | does not fit the documented one-card serving pool | Not an implementation assumption |

The context budget is total input plus generated reasoning/output. The scheduler must reserve output explicitly and reject or re-summarize oversized packets before dispatch. Qwen enables thinking by default and can preserve earlier thinking; the Factory should not blindly replay preserved reasoning because it inflates context and makes stale hidden assumptions authoritative ([Qwen model card](https://huggingface.co/Qwen/Qwen3.8-27B-FP8#best-practices)).

The 64 GB host RAM is useful for the OS, checkpoint download/staging, indexes, build processes, and durable orchestration. It does not enlarge VRAM. CPU weight/KV offload may make larger configurations boot in some engines, but no primary source found here validates acceptable Qwen3.8-27B agent throughput or long-context correctness with that offload on this exact machine. Offload is therefore a recovery/experiment, not the baseline.

### Quantization and serving-engine choice

| Option | One-card judgment | Evidence and caveat |
|---|---|---|
| BF16 | Reject | About 54 GB of weights according to SGLang; impossible wholly in 32 GB VRAM |
| Official Qwen FP8 | Reject for the Factory baseline | Weights nearly fill VRAM; SGLang's exact RTX 5090 recipe says it does not boot/service reliably |
| RadixArk NVFP4 W4A4 | Adopt provisionally | Exact SGLang/RTX 5090 path is validated; quantization quality still needs Factory-specific A/B tests |
| GGUF/llama.cpp Q4 variants | Experimental fallback | Smaller weight-only formats may fit, but recent upstream reports show active Qwen hybrid conversion, MTP, and CUDA regressions; pinning and correctness tests are mandatory ([conversion issue](https://github.com/ggml-org/llama.cpp/issues/27019), [Qwen3.8 CUDA field report](https://github.com/ggml-org/llama.cpp/discussions/27164)) |

Use **SGLang first** because it supplies an exact Qwen3.8-27B RTX 5090 recipe, understands the hybrid GDN state pool, supports the correct `qwen3_coder` tool parser, and has measured the target card. Pin the tested SGLang commit/image and checkpoint revision; this model and Blackwell support are moving quickly. vLLM is a valuable second-engine comparison because it supports Qwen FP8, constrained outputs, and strict/named tool calls, but this research found no equally specific vLLM measurement for NVFP4 Qwen3.8-27B on one RTX 5090 ([vLLM Qwen deployment documentation](https://qwen.readthedocs.io/en/stable/deployment/vllm.html), [vLLM structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/)).

A suitable first SGLang profile follows the documented shape, not a promise that these exact values are optimal:

```text
checkpoint: RadixArk/Qwen3.8-27B-NVFP4
GPU: one RTX 5090
KV cache: fp8_e4m3
attention backend: flashinfer
concurrent running requests: 1
CUDA graph max batch: 1
reasoning parser: qwen3
tool parser: qwen3_coder
memory fraction: 0.90 for the no-speculation baseline
```

Start without speculative decoding to minimize moving parts. Then A/B the in-checkpoint MTP/EAGLE path and DFlash2. SGLang reports roughly 145–153 generated tokens/s/user for NVFP4 + EAGLE depending on GDN state precision, and a best 4.92 ms median time per output token with DFlash2 at acceptance length 4.29. Those are maintainers' measurements at a pinned build, not portable throughput guarantees. DFlash2 also needs tighter memory and prefill settings on the 5090 ([SGLang cookbook configuration tips](https://github.com/sgl-project/sglang/blob/1cf2b8c54d81802abc15dcf23a29b9cc687bc01e/docs/cookbook/autoregressive/Qwen/Qwen3.8-27B.mdx#L249-L302)).

### Concurrency

The only safe initial claim is **one physical request in flight**. The SGLang recipe explicitly pins `--max-running-requests 1` and `--cuda-graph-max-bs 1`; maintainers warn that raising both requires re-deriving the hybrid-state/KV split. They state that GDN state, rather than attention KV, becomes the concurrency limit first on a 32 GB card ([SGLang RTX 5090 cell](https://github.com/sgl-project/sglang/blob/f8cbf000f4a5bfd86d3fb7c1e2d6c8fb12339d0e/docs/src/snippets/configs/Qwen/qwen3.8-27b.jsx#L588-L655)).

This does not prevent a multi-agent factory. Run many logical workers as durable jobs, but let a single GPU scheduler serialize inference. Builds, tests, repository indexing, retrieval, and deterministic validation can proceed concurrently on CPU as RAM and I/O permit. Physical inference concurrency two or four is an optimization experiment, not an architectural requirement.

### Structured output and tool use

SGLang's recipe uses `--reasoning-parser qwen3 --tool-call-parser qwen3_coder`. Its documentation says the model emits Qwen's XML-like `<tool_call><function=...><parameter=...>` protocol and that the `qwen3_coder` parser converts it to structured API tool calls; the Hermes parser expects a different representation and is wrong for this checkpoint ([SGLang agent-harness guidance](https://github.com/sgl-project/sglang/blob/1cf2b8c54d81802abc15dcf23a29b9cc687bc01e/docs/cookbook/autoregressive/Qwen/Qwen3.8-27B.mdx#L304-L337)).

Constrained decoding can guarantee syntactic JSON/schema conformance, but it cannot guarantee that the model selected the right tool, supplied the right file path, preserved an identifier, or made a sound decision. vLLM states this boundary explicitly: named/required calls can guarantee parsable schema-conforming arguments, “not a high-quality one” ([vLLM tool-calling contract](https://docs.vllm.ai/en/latest/features/tool_calling/)).

There are also recent upstream reports of Qwen-family tool-history template incompatibility and malformed/exact-string behavior. These are issue reports rather than confirmed universal defects, but they justify a local regression suite and a normalization boundary around chat history ([Qwen3.8 JSON-string history issue](https://github.com/QwenLM/Qwen3/issues/1894), [exact path argument issue in Qwen3.5](https://github.com/QwenLM/Qwen3/issues/1821)). Every tool call should therefore pass four non-model checks before execution: parser success, JSON Schema validation, allowlisted tool/action validation, and exact target/capability validation. Side-effecting calls additionally need policy authorization and idempotency keys.

### Coding ability and long-horizon reliability

Qwen reports strong but non-perfect results: 73.0 on Terminal-Bench 2.1, 61.7 on SWE-bench Pro, and 42.3 on NL2Repo-Bench. The model card says some coding runs used a Claude Code harness and a 256K window; it also includes in-house benchmarks and other model-reported or model-judged comparisons. These are useful evidence that the model can perform coding-agent work, not evidence that it can operate unattended for days ([Qwen benchmark table and notes](https://huggingface.co/Qwen/Qwen3.8-27B-FP8#benchmark-results)).

RadixArk reports 73.81% on an 84-task Terminal-Bench subset for its NVFP4 checkpoint, but that test used four B300/GB300 GPUs and says nothing about restart recovery or multi-day behavior. Even taken at face value, a pass rate near 74% means orchestration must expect ordinary task failure ([NVFP4 evaluation](https://huggingface.co/RadixArk/Qwen3.8-27B-NVFP4/blob/319f741cce68d7914884900c138a1fbb70a42f30/README.md#evaluation)).

No reviewed primary source demonstrates this checkpoint completing arbitrary products or surviving multi-day unattended operation on one RTX 5090. Long-horizon reliability must come from short transactions, external durable state, deterministic completion gates, bounded retries with changed evidence/context, process supervision, and quarantine—not from keeping one conversation alive.

## Reproducible local benchmark required before implementation lock

Documentary acceptance is enough to choose NVFP4 + SGLang as the first candidate. It is not enough to freeze the production profile. Run and archive the following on the actual machine, including driver, CUDA, engine commit/image digest, model revision/hash, command line, temperatures/power limit, and raw results.

1. **Boot and memory sweep.** Measure READY time, idle VRAM, post-graph VRAM, first-request peak, and OOM behavior for no speculation with FP32 and BF16 GDN state. Confirm that repeated cold starts recover without manual cleanup.
2. **Context acceptance and correctness.** Test 8K, 16K, 32K, 64K, and the maximum stable length with reserved outputs of 1K, 2K, and 4K. Include code-symbol retrieval and cross-file dependency questions at controlled token positions, not only synthetic token filling. A request merely completing is not a pass.
3. **Relevant throughput.** Record prefill tokens/s, decode tokens/s, TTFT, TPOT percentiles, peak VRAM, and energy for Work-atom shapes such as 2K/512, 8K/1K, 16K/2K, and 32K/4K. Run concurrency one first; test two and four only as optional optimizations.
4. **Quantization/state/speculation A/B.** Compare NVFP4 against a trusted BF16 or official FP8 reference on a larger machine or hosted endpoint using identical prompts and deterministic graders. Separately compare FP32/BF16 GDN state, no-speculation, MTP/EAGLE, and DFlash2. Do not accept speed without quality and stop-rate parity.
5. **Structured-output conformance.** Generate at least hundreds of responses per schema across nested objects, enums, optional/null fields, long strings, streaming/non-streaming, thinking on/off, and malformed prior messages. Record parser errors, schema errors, semantic errors, retries, and latency.
6. **Tool-use correctness.** Test auto, required, named, parallel, and no-tool decisions; exact file paths and identifiers; tool-result continuation; injected tool output; unavailable tools; and refusal/escalation. Judge tool choice and arguments independently of syntax.
7. **Atomic coding benchmark.** Use hidden tests on repeated small Work atoms: locate, plan, edit, repair, refactor, and integrate. Stratify by context size and number of relevant/distractor files. Record pass@1, pass within retry budget, regressions, wrong-file edits, intervention rate, and total tokens/time.
8. **Recovery and soak.** Run at least a 72-hour queued workload while injecting model-server death, orchestrator restart, build timeout, malformed output, OOM, full disk threshold, and stale lease. Require no lost/duplicated side effect, bounded retry counts, durable evidence, and automatic continuation or quarantine.

## Planning constraints this ticket establishes

- Design around **small, reconstructible 8K Work atoms**, not long chats. Permit 16K and exceptional 32K packets under explicit policy.
- Treat the model server as a **single-stream scarce resource** behind a durable queue. Logical agent concurrency must not depend on GPU concurrency.
- Make the inference backend replaceable, but implement and benchmark **SGLang + NVFP4 first**.
- Keep source, contracts, graph state, test evidence, and retry state outside the LLM. Never depend on preserved chain-of-thought as durable memory.
- Require constrained syntax plus deterministic semantic/tool authorization checks. The model may propose; parsers and policy decide whether an action is admissible.
- Do not claim the full 262K native window, >1 inference concurrency, published throughput, NVFP4 quality parity, or unattended reliability until the exact local benchmark produces archived evidence.

## Sources and evidence grading

Primary/high-trust sources used: NVIDIA hardware specification; pinned Qwen model card and configuration; pinned SGLang source, exact-card recipe, and validation notes; vLLM feature contracts; pinned NVFP4 checkpoint card. Qwen and RadixArk benchmark results are explicitly treated as publisher claims. SGLang results are maintainer measurements on the exact GPU but still require reproduction because software revisions, host configuration, and workload shape materially affect them. GitHub issues/discussions are used only as field reports identifying tests to run, never as proof of universal behavior.
