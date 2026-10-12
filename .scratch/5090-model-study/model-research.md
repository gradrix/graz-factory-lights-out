# RTX 5090 model research — 2026-09-30

For measurements and the final local recommendation, see [RESULTS.md](RESULTS.md). This document preserves the source research and candidate hypotheses that guided the experiments; proposed commands below are not, by themselves, evidence of a successful local run.

## Recommendation before local measurements

Benchmark the running Qwen3.8-27B first, then **Ternary Bonsai 2 27B PQ2_0**. Bonsai is the strongest immediate hypothesis for improving both speed and available context on this machine. Keep Qwen3.8-27B as the quality reference. Treat **Swift 1.5 Qwen3.8-27B** as the next candidate for reducing task completion time through shorter reasoning. **Flash-Next** merits an experimental offload test, but is a poor first choice when the objective includes very long context on one 32 GB GPU. These are research recommendations, not measured winners.

“Best” needs separate answers for correctness, task completion latency, concurrent throughput, and usable context. A model producing more tokens per second can still take longer to solve a task. A server accepting 262K input does not establish useful reasoning at that length.

## Model identities and shortlist

| Candidate | Why it belongs | Main constraint | Priority |
|---|---|---|---|
| Existing Inferact/Qwen3.8-27B-NVFP4 | Quality and compatibility reference | Current weights occupy most VRAM | Baseline and context tuning |
| prism-ml/Ternary-Bonsai-2-27B-gguf, PQ2_0 | Very small Qwen3.8 derivative; promising Blackwell kernels | Requires Prism runtime; quality must be checked | First challenger |
| Qwen3.8-27B in a different NVFP4/GGUF packing | Potentially reclaim VRAM without changing base model | Same “4-bit” label can hide different tensor precision | Second configuration experiment |
| ukisai/Swift-1.5-Qwen3.8-27b | Shorter reasoning, same model family | Adapted weights and distinct license | Task latency challenger |
| Flash-Next GSQ-RCO Coder | Much larger parent model compressed toward 32 GB | Expert pruning, little KV room, extra disk shard | Experimental |
| Gemma 4 26B A4B / 31B QAT | Independent family, multimodal, useful general baseline | No direct evidence of superiority for this workload | Broader comparison |
| Nemotron 3 Nano 30B A3B NVFP4 | Long-context architecture and small active MoE | Different parser and quality profile | Context specialist |

### Qwen3.8-27B

The name is real; it is not a mistaken spelling of Qwen3-8B. Qwen publishes 27B dense language parameters, 64 layers, and a hybrid layout with 48 recurrent linear-attention layers and 16 full-attention layers. Its native context is 262,144 tokens, with extension advertised to 1,000,000. It supports images/video, thinking controls, and retained reasoning history. Publisher results include SWE-bench Pro 61.7 and LiveCodeBench v6 90.3, but those numbers depend on the documented harness and budgets. [Qwen model card](https://huggingface.co/Qwen/Qwen3.8-27B)

### Ternary Bonsai 2 27B

This is a Qwen3.8-27B derivative, distinct from earlier Bonsai releases. The language weights occupy 5.95 GB in PTQ1_0 or 7.21 GB in PQ2_0; optional vision adds a 0.63 GB projector. The card advertises 262K context. Vendor RTX 5090 measurements favor PQ2: 129.9 token/s generation and 3,893 token/s prompt processing, versus 120.5 and 1,805 for PTQ1. These are short `llama-bench` measurements, not long-context chat results. Its 14-task average is reported as 84.78 versus 86.32 for FP16; tool calling and knowledge still regress. Treat the “98.2% retained” number as a vendor aggregate, not universal parity. Stock llama.cpp cannot correctly execute these rotated ternary weights. [Prism model card](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf)

### Qwen3.8-Flash-Next

The official architecture is 125B parameters with 6B active per token, **plus** 51B n-gram embeddings and 4B MTP. Active parameter count controls part of compute, not total weight storage. It advertises the same 262,144 native / 1M extended context. Publisher SWE-bench Pro rises from 61.7 for 27B to 62.5; other agent tasks improve more substantially. This supports trying the larger model when memory permits, but does not demonstrate that an aggressively pruned version beats 27B locally. [Qwen Flash-Next card](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)

The unpruned GSQ-RCO Q2_0 build needs 37.6 GB of transformer weights plus a 28.8 GB n-gram shard. The latter can be memory mapped; the transformer alone exceeds the GPU before KV cache and runtime buffers. Higher precision increases the resident part to 39.2–54.8 GB. CPU offload is therefore required for these builds. [DASLab unpruned release](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF)

The experimental Coder variant removes half the routed experts and stores retained weights at 3.5 bits. Its two files total 58.4 GB: 29.6 GB transformer and 28.8 GB lookup table. The “1.89 bits” headline amortizes deleted experts over original parameters; it is not the precision of individual weights. Publisher SWE-bench Verified drops from 82.8 to 75.6; LiveCodeBench from 87.43 to 86.28. Even if weights fit, context and scratch buffers require additional memory. Its model card explicitly accepts degradation outside the selected capability mix. [DASLab Coder release](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF)

### Swift 1.5

UkisAI post-trains Qwen3.8-27B to reduce unnecessary reasoning. The publisher reports shorter traces with mixed accuracy changes: Terminal-Bench 2.1 improves from 69.21 to 72.13, while IFBench drops from 73.53 to 72.07. These are vendor comparisons, not directly comparable to Qwen's table. NVFP4, AWQ, AutoRound and GGUF versions are linked. This makes Swift an especially useful candidate when long thinking dominates latency. Its contribution uses Swift Open License v1.0, with separate enterprise terms above the stated revenue threshold. [Swift release and methodology](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b)

### Other families worth retaining in the comparison

Gemma 4 offers 31B dense and 26B A4B MoE, both with 256K context; the MoE has 25.2B total and 3.8B active parameters. The official card reports LiveCodeBench v6 of 80.0 and 77.1, respectively, and 128K MRCR scores of 66.4 and 44.1. These scores are useful for choosing tests, but differing evaluation setups prevent a strict cross-vendor ranking. Official QAT exports make quantized variants preferable starting points. [Google Gemma card](https://huggingface.co/google/gemma-4-26B-A4B-it), [Google QAT 31B export](https://huggingface.co/google/gemma-4-31B-it-qat-w4a16-ct)

NVIDIA's Nemotron 3 Nano 30B A3B NVFP4 advertises up to 1M context, while its default configuration is 256K because of memory requirements. Its documented serving path uses vLLM and a model-specific reasoning parser. It should be considered if maximum validated context outweighs the convenience of the existing Qwen stack. The claimed limit still requires a local capacity and retrieval test. [NVIDIA model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4)

GLM-4.7-Flash remains another 30B-class MoE comparison candidate, with an official deployment recipe. It is lower priority for this investigation because the Qwen-derived candidates directly address both current quality and memory constraints. This priority is a judgment, not a measured claim that GLM is inferior. [Z.ai model card](https://huggingface.co/zai-org/GLM-4.7-Flash)

## Serving choices and precision

The official vLLM Qwen recipe gives a single-5090 Inferact launch using eager execution, FP8 KV and 32K context. Its measured KV pool grows from roughly 91K to 153K tokens with text-only serving and reduced sequence capacity. It warns of CUDA graph allocation failures on that configuration and records large memory differences between NVFP4 exports. These are version- and checkpoint-specific results. The recipe also documents MTP, and DFlash2 support beginning at vLLM 0.28. [vLLM Qwen recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)

NVIDIA's own Qwen NVFP4 export uses mixed precision: MLP and output weights use NVFP4 while attention uses FP8. Its publisher evaluations show small differences versus BF16 across six tasks, with both gains and losses. It supplies vLLM and SGLang examples, but its sample vLLM deployment uses four-way tensor parallelism, so it is not a single-5090 capacity guarantee. [NVIDIA quantization card](https://huggingface.co/nvidia/Qwen3.8-27B-NVFP4)

FP8 KV reduces cache storage relative to FP16/BF16. Appropriate scale handling matters; unsupported or poorly calibrated scaling can degrade accuracy. A successful startup is insufficient validation. Test retrieval, structured outputs and ordinary reasoning using the actual cache dtype. [vLLM quantized KV documentation](https://docs.vllm.ai/en/latest/features/quantization/quantized_kvcache/)

For Bonsai, the demo repository is the runtime source of truth. It points to a pinned Prism llama.cpp release and provides platform binaries. Use its CUDA build instead of a generic llama.cpp image. [Prism demo](https://github.com/PrismML-Eng/Bonsai-demo)

## Context memory calculation

An approximate full-attention KV cost for Qwen3.8-27B is:

`16 full layers × 2 (K,V) × 4 KV heads × 256 head dimension × bytes per element`.

That is 32,768 bytes/token at FP8 and 65,536 at BF16, before scales, block padding, recurrent states and implementation overhead. This is a calculation from the published architecture, not a runtime measurement.

| Total sequence tokens | Approximate FP8 KV | Approximate BF16 KV |
|---:|---:|---:|
| 32,768 | 1 GiB | 2 GiB |
| 65,536 | 2 GiB | 4 GiB |
| 131,072 | 4 GiB | 8 GiB |
| 262,144 | 8 GiB | 16 GiB |
| 524,288 | 16 GiB | 32 GiB |
| 1,000,000 | 30.5 GiB | 61.0 GiB |

Consequently, 1M FP8 KV alone nearly fills a 32 GiB card. Bonsai's compact weights plausibly enable 262K and perhaps larger experimental windows with more cache compression; they do not automatically enable 1M. Context beyond native training also needs the correct extension configuration and a quality evaluation. Sequence capacity includes prompt, chat formatting, reasoning and final output. Concurrent requests share the cache pool.

## Proposed automated evaluation

1. Save exact model revision, engine commit, flags, GPU memory and baseline health.
2. Measure streaming time to first token, generation rate, total answer time and input/output counts independently. Report single request and modest concurrency separately.
3. Use deterministic checked tasks for JSON structure, tool arguments, code unit tests and multi-step constraints. Include tasks that produce a real answer, not only throughput filler. Keep generated code isolated from secrets and network.
4. Match reasoning mode, sampling, prompt and output budgets across models. Record truncation as failure; a short reasoning cap can otherwise make a good model look broken.
5. Probe 32K, 64K, 128K and 262K with exact token counts, randomized facts at several depths, distractors and multi-fact questions. Repeat several seeds. Reserve output headroom.
6. Stop increasing size at OOM, request rejection, unacceptable delay or correctness failure. Distinguish largest accepted request from largest reliable context.
7. Test speculative decoding only after the ordinary path is correct; record acceptance statistics and total task time. Added draft weights can reduce context capacity.
8. Restore the baseline after tests; choose a permanent configuration only from actual measurements.

## Pinned Bonsai artifacts for the experiment

Verified through GitHub and Hugging Face APIs on 2026-09-30:

- Runtime release: `prism-b10743-adfffbe`.
- [CUDA 12.8 Linux x64 archive](https://github.com/PrismML-Eng/llama.cpp/releases/download/prism-b10743-adfffbe/llama-prism-b10743-adfffbe-bin-linux-cuda-12.8-x64.tar.gz).
- Model commit: `b072e1d3b35a0a630cece372c2127528e0994386`.
- [PQ2_0 model file](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/resolve/b072e1d3b35a0a630cece372c2127528e0994386/Ternary-Bonsai-2-27B-PQ2_0.gguf).
- Start with GPU layers 99, flash attention enabled, 32,768 context and one sequence; increase only after health and correctness checks.

## Evidence boundaries

This document contains current primary-source research and explicit calculations. It contains no measurements from MONSTER-GAMING-PC. Local benchmark artifacts elsewhere in this study determine the final recommendation. Vendor benchmark claims, advertised context, and the existence of a quantized file are not proof that a configuration works on this rig.

## Follow-up: original Qwen GGUF versus the existing Inferact export

The next concrete same-base candidate is **Unsloth UD-Q4_K_M**. The producer identifies this repository as an imatrix-based Dynamic 3.0 quantization of Qwen3.8-27B. Its file is 16,464,440,224 bytes (15.33 GiB), while UD-Q4_K_XL is 17,559,178,144 bytes (16.35 GiB). These exact sizes came from the Hugging Face model API on September 30. Neither number includes KV or compute buffers. Q4_K_M is the stronger first experiment for context headroom; no claim of optimal quality is established. [Unsloth release](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF)

Pinned artifacts:

- Official base current revision: `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`. This identifies the current official base, not proof of the exact conversion ancestry of the Unsloth file.
- Unsloth revision: `4ca720788d1e01f1bff70c033e0d0028fd02e502`.
- [UD-Q4_K_M download](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/resolve/4ca720788d1e01f1bff70c033e0d0028fd02e502/Qwen3.8-27B-UD-Q4_K_M.gguf).
- SHA256: `322e194ff79741c7baa497c240f677f54b201b0efab44ca8e50f122b39123482`.
- NVIDIA NVFP4 revision: `482ca0f3832238542f8f5295dde86b5f22711d80`; three safetensors files total 21,921,697,280 bytes (20.42 GiB). This offers less weight-memory reduction than the GGUF, before runtime differences.

The pinned Prism runtime contains the Qwen35 implementation and standard GGUF quantization support. That supports trying the ordinary Qwen file with the same engine; actual compatibility must still be confirmed by a load and correctness test. [Pinned model implementation](https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/src/models/qwen35.cpp)

Example candidate command, using the previously downloaded Prism binary:

```bash
./llama-server \
  -m Qwen3.8-27B-UD-Q4_K_M.gguf \
  --host 127.0.0.1 --port 18080 \
  -ngl 99 -fa on -np 1 -c 131072 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --reasoning auto --chat-template-kwargs '{"reasoning_effort":"medium"}'
```

This is a proposed test command, not a measured successful launch. Q8_0 includes block scales and is somewhat larger than the FP8 approximation above. Start at 32K if loading or workspace allocation fails; try 262144 only after inspecting available memory and answering real requests.

## Follow-up: Bonsai controls and native context

The model's known-issues document clarifies several easily confused controls. Keep the server at `--reasoning auto`; use request `reasoning_effort: "none"` to disable thinking, or `medium` to ask for shorter reasoning. `high` is invalid; `low` is accepted but has little measured shortening. A thinking budget is a separate top-level `thinking_budget_tokens` field, not a template kwarg. Budget zero alone does not disable thinking. `--reasoning on` overrides a client's request to disable it. The document also lists malformed tool calls and growing tool-loop prompt caches as unresolved problems. [Bonsai known issues](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/main/KNOWN_ISSUES.md)

The pinned runtime supports `chat_template_kwargs.enable_thinking: false`, but its CLI marks that route deprecated in favor of `--reasoning off`. Per-request `reasoning_effort: "none"` has explicit server support. [Pinned server API documentation](https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/tools/server/README.md), [Pinned CLI implementation](https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/common/arg.cpp)

For native full context, use `-c 262144 -np 1 -fa on`. For the Bonsai wrapper, use `BONSAI_CTX=262144`; zero means a machine-dependent automatic choice, not full model context. The wrapper caps its supported range at 262144. The UI's “Medium” is a hard 2,048-token budget and differs from the model's `reasoning_effort: "medium"`. [Prism demo guidance](https://github.com/PrismML-Eng/Bonsai-demo)

If memory demands it, Prism documents experimental Q4 KV using `--cache-type-k q4_0 --cache-type-v q4_0`. Its estimate is about 18 KiB/token versus 64 KiB for FP16, with slightly slower decoding. A model-specific mean-centering calibration can improve quality; it must match the inference rotation state. Do not reuse another model's calibration. [Prism KV guidance](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/KV-CACHE.md)

## Follow-up: extending beyond native context

Qwen's official guidance uses static YaRN: factor 2 for 524,288 tokens, factor 4 for 1M. Its vLLM/SGLang examples override the nested `text_config.rope_parameters`, retaining the original interleaved multimodal RoPE fields and original context 262144. Static scaling can reduce short-context quality. [Official Qwen extension instructions](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/README.md)

For the original Qwen GGUF, the corresponding Prism CLI experiment is:

```bash
--ctx-size 524288 --rope-scaling yarn --rope-scale 2 --yarn-orig-ctx 262144 \
  --override-kv qwen35.context_length=int:524288
```

These flags exist in the pinned parser. The later Bonsai experiment completed one near-524K retrieval probe and short regression checks; see [the measured report](RESULTS.md) for its limits. Extension of the ordinary Qwen GGUF was not tested. Merely raising context without the correct positional scaling is not a supported extension. There is no publisher-supported >262144 Bonsai recipe in the sources inspected. The runtime metadata override is required to bypass the server's training-context cap and does not change the model's training history.

## Follow-up: minimal CUDA graph experiment on vLLM 0.28.0

A narrow graph test is justified before concluding that the existing weights are intrinsically slow. The exact v0.28.0 configuration supports `FULL_DECODE_ONLY`, which captures decoding while leaving mixed/prefill batches outside graphs. It also accepts an explicit capture-size list. This can reduce capture memory relative to the default configuration, but cannot guarantee startup. [v0.28.0 compilation configuration](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/compilation.py)

Use the existing pinned Inferact weights and parsers, remove `--enforce-eager`, and change only the following for an initial 32K, single-request comparison:

```bash
--max-model-len 32768 \
--max-num-seqs 1 \
--max-num-batched-tokens 2048 \
--gpu-memory-utilization 0.85 \
--kv-cache-dtype fp8 \
--language-model-only \
--compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1],"max_cudagraph_capture_size":1}'
```

Do not attach a speculative drafter during this experiment: its query length changes the relevant capture size. Retaining `--enforce-eager` would disable the graph experiment. Record startup capture memory, actual graph mode, kernel selection, and identical-request latency after warmup. If it fails, preserve the error and restore eager. A successful one-slot decode graph does not establish that larger batches or long contexts fit. [v0.28.0 graph-size and eager handling](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/vllm.py)

The same release exposes `--linear-backend flashinfer_cutlass` and `--linear-backend flashinfer_b12x`. The former checks CUTLASS FP4 support and capability >=100; the latter specifically requires SM120+ and the FlashInfer B12x kernel. Generic `flashinfer_cutedsl` checks family100 and is not the consumer-Blackwell option. Native `b12x` requires the optional package. Start with automatic selection and inspect `Using ... for NVFP4 GEMM`; an emulation fallback would be a distinct performance defect. MoE environment flags do not select dense Qwen's linear kernels. [Kernel options](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/kernel.py), [FlashInfer support checks](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/kernels/linear/nvfp4/flashinfer.py), [Kernel selection](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/kernels/linear/__init__.py)

These commands are source-verified proposals, not remotely executed measurements. The installed build may contain downstream differences despite its version label; its `--help` and logs are the final compatibility evidence.

## Follow-up: concrete Flash-Next Coder feasibility test

The pruned Coder's first shard is **27.57 GiB**, so a short-context test on this 5090 is plausible. This leaves roughly 3.8 GiB out of 31.4 GiB usable for context, recurrent states, indexer, workspaces and other GPU use. At 8K, ordinary full-attention FP16 KV is approximately 192 MiB from the published 12-layer/2-head/256-dimension layout; this omits sparse-indexer and runtime overhead. Therefore a load test is needed. The n-gram shard is 26.82 GiB and can be read lazily from SSD; the rig's 44 GiB host RAM can cache much of it. These are feasibility calculations, not a fit guarantee.

### Exact model files

Hugging Face API revision checked September 30: `5348543e0147355ac9cbcb031184a3546350988e`.

| File within repository | Bytes | SHA256 |
|---|---:|---|
| `IQ1_M/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf` | 29,608,446,496 | `e11083ba855e7666b48ea3f2db6a9c3a20c18751a012cc24f948de91b7087fad` |
| `IQ1_M/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00002-of-00002.gguf` | 28,800,138,432 | `316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113` |

[First pinned shard](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF/resolve/5348543e0147355ac9cbcb031184a3546350988e/IQ1_M/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf), [second pinned shard](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF/resolve/5348543e0147355ac9cbcb031184a3546350988e/IQ1_M/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00002-of-00002.gguf). Keep both alongside one another; start the server with the first. Skip the optional 907,543,008-byte vision projector for the text test.

### Runtime distinction

The previously pinned Prism `adfffbe` tree does **not** contain `qwen4exp.cpp`. Use a separate current upstream llama.cpp build for Flash; do not replace the working Bonsai binary.

Upstream release `b11284`, commit `25747b08e7a0f9a59a2089ce6b98d2229b76042a`, includes the architecture and lazy-loading flags. Its model loader marks the PLE table `TENSOR_READ_LAZY`; this is native support, not an extra offload patch. CLI `--lazy-mode on` reads selected tensor rows on demand and requires mmap. `auto` activates for tensors over 4 GiB. [Pinned model implementation](https://github.com/ggml-org/llama.cpp/blob/b11284/src/models/qwen4exp.cpp), [Pinned loader arguments](https://github.com/ggml-org/llama.cpp/blob/b11284/common/arg.cpp)

- [Ubuntu CUDA 12.8 binary](https://github.com/ggml-org/llama.cpp/releases/download/b11284/llama-b11284-bin-ubuntu-cuda-12.8-x64.tar.gz).
- [Matching CUDA runtime archive](https://github.com/ggml-org/llama.cpp/releases/download/b11284/cudart-llama-b11284-bin-ubuntu-cuda-12.8-x64.tar.gz), if needed by dynamic linking.
- Source-build fallback: checkout the commit above, configure `cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120`, then `cmake --build build -j4 --target llama-server llama-bench` in an environment containing the CUDA toolkit.

Proposed initial command:

```bash
./llama-server \
  -m IQ1_M/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf \
  --host 127.0.0.1 --port 18081 \
  -ngl 99 -np 1 -c 8192 -b 256 -ub 256 -fa on \
  -lm mmap --lazy-mode on
```

Start with default FP16 KV to avoid adding quantized-cache compatibility uncertainty. Verify the startup log identifies `qwen4exp`, all intended transformer layers are on GPU, and PLE is lazy rather than a GPU allocation. If workspace allocation fails, reduce offloaded layers (for example `-ngl 46`) and measure the speed impact. Preserve the sparse lookup table on Linux SSD storage; cold I/O can dominate first-request timing. Measure cold and warm requests separately.

### Optional alternative engine

The Coder publisher links Strata, which has dedicated expert caching and lazy PLE. Its current README documents a Coder configuration and says the expert working set fits on 5090. It also has a low-RAM mode using memory-mapped expert packs, but requires extra conversion storage. Its headline speed results are vendor measurements on another machine. This is a fallback if upstream performs poorly, not evidence of a measured advantage here. Pin the inspected Strata tree `d6708a4aae15b4860000d54c8af9e84d684bce09`; read its setup before executing because its convenience installer may install dependencies and start services. [Strata](https://github.com/Niko1221/Strata/tree/d6708a4aae15b4860000d54c8af9e84d684bce09), [Strata low-RAM details](https://github.com/Niko1221/Strata/blob/d6708a4aae15b4860000d54c8af9e84d684bce09/docs/DETAILS.md)

## Follow-up: reproducible HumanEval coding comparison

Fetched the canonical 164-task dataset from upstream commit `6d43fb980f9fee3c892a914eda09951f772ad10d`. Local artifacts are `humaneval.jsonl`, `humaneval-LICENSE.txt`, and `humaneval-subset32.json` beside this report. The repository uses the MIT license; retain its notice with the copied data. [Pinned dataset](https://raw.githubusercontent.com/openai/human-eval/6d43fb980f9fee3c892a914eda09951f772ad10d/data/HumanEval.jsonl.gz), [Pinned license](https://github.com/openai/human-eval/blob/6d43fb980f9fee3c892a914eda09951f772ad10d/LICENSE)

- Compressed source SHA256: `b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef`.
- Decompressed JSONL SHA256: `1d49078ba3e2b196b9344535bef34a43021f038fad9561d6ee7c53450609a6a2`.
- Selection: numerically sort all task IDs, then `random.Random(5090).sample(ids, 32)`. Use the recorded IDs in the manifest for all model runs.
- Static inspection of prompts, canonical solutions and tests found only standard-library imports (`collections`, `copy`, `hashlib`, `math`, `random`, `re`, `string`, `typing`). No NumPy references were found; no dependency-based exclusions were made.
- All canonical assemblies parsed successfully without execution. This verifies syntax only; Python 3.11 runtime validation remains a grading prerequisite.

The upstream harness constructs `prompt + completion + "\n" + test + "\ncheck(entry_point)"`. It expects a completion continuing the given function prompt. [Pinned execution harness](https://github.com/openai/human-eval/blob/6d43fb980f9fee3c892a914eda09951f772ad10d/human_eval/execution.py)

For a strict continuation protocol, ask every model to return only the indented function body after the supplied prompt, without fences or explanation. Preserve raw responses. Apply exactly the same limited extraction policy to all models, and record extraction failures rather than repairing answers selectively. Alternatively, request complete source consistently and assemble that source plus tests; label this a chat adaptation rather than the original completion protocol. Do not show canonical solutions or tests in model prompts.

Proposed run: one sample per selected task, no thinking, temperature zero, fixed 1,024 output tokens, same prompt and deadline, fresh context. Record finish reason, output tokens, answer latency, syntax failures, assertion failures and timeout failures. A 768-token budget is another valid profile but must be identical for all models; budget truncation counts as failure. Seed the grader's standard-library `random` before each test, since some upstream checks use randomized examples. Validate canonical solutions under the chosen Python 3.11 grader first to detect environment/test issues.

Grade in isolated disposable Docker containers with networking disabled, no credentials or host workspace mounts, read-only filesystem plus bounded temporary storage, dropped capabilities and process/memory/CPU/time limits. The upstream reliability guard is explicitly not a sandbox. This research step did not execute any generated code.

Report **“HumanEval fixed 32-task subset, one sample, non-thinking chat/continuation protocol”**, with the integer count passed. Do not present this as the full public HumanEval score. One task changes the subset percentage by 3.125 points, so small differences are weak evidence. The old public tasks also cannot establish freedom from training contamination or predict multi-file agent performance; retain the separate tool-use and realistic task tests.

## Follow-up: Flash quantization compatibility audit

Inspected the **actual pinned GGUF headers** using bounded HTTP range reads, including all metadata and tensor descriptors. Evidence is saved in `flash-shard1-header.json` and `flash-shard2-header.json`.

- Shard 1 declares `qwen4exp`, 256 experts with 10 selected, and 262144 context. None of its metadata keys declare a Hadamard transform or rotation.
- Its 1,223 tensor descriptors use F32, F16, BF16, Q8_0, Q4_K, Q5_K, Q6_K, IQ3_XXS, IQ3_S, IQ2_S, IQ4_NL, IQ4_XS and Q2_0.
- All these numeric type IDs exist in upstream `b11284`. The newer Q2_0 type (42) has CUDA dequantization and matrix-vector dispatch in that release.
- Shard 2 contains one IQ4_NL tensor. The filename's `IQ1_M` is a packaging label; **neither shard contains actual IQ1_M tensors**.

The method repository describes refining assignments/scales and exporting existing scalar GGUF formats, without changing their inference contract. This is consistent with the inspected file and its model card's ordinary llama.cpp command. [GSQ source](https://github.com/IST-DASLab/GSQ), [Pinned GGML type definitions](https://github.com/ggml-org/llama.cpp/blob/b11284/ggml/include/ggml.h), [CUDA conversion](https://github.com/ggml-org/llama.cpp/blob/b11284/ggml/src/ggml-cuda/convert.cu), [CUDA matrix-vector dispatch](https://github.com/ggml-org/llama.cpp/blob/b11284/ggml/src/ggml-cuda/mmvq.cu)

Conclusion: no evidence of a Bonsai-style custom rotation runtime requirement was found. Upstream b11284 is a supported candidate for a real load and correctness test. Header/type compatibility does not prove full architecture numerical correctness; inspect startup diagnostics and require meaningful correct responses before interpreting throughput.

## Follow-up: long-context source audit

In pinned Prism `prism-b10743-adfffbe`, Qwen35 passes its rotary dimension count, section layout and RoPE type into `ggml_rope_multi`, alongside YaRN frequency/scaling parameters, for both Q and K. The context code resolves the original context and inverse frequency factor from the CLI. No source-level reason was found to override the GGUF's partial rotary dimensions or interleaved sections for this test. Preserve those and its frequency base. [Qwen35 implementation](https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/src/models/qwen35.cpp), [Context parameter resolution](https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/src/llama-context.cpp), [CUDA RoPE implementation](https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/ggml/src/ggml-cuda/rope.cu)

Proposed **experimental** Bonsai profiles, calling the binary directly:

```bash
# 512K: approximately 17 GiB Q8_0 KV, before other memory
-c 524288 -np 1 -fa on --cache-type-k q8_0 --cache-type-v q8_0 \
  --rope-scaling yarn --rope-scale 2 --yarn-orig-ctx 262144 \
  --override-kv qwen35.context_length=int:524288

# 1M: approximately 17.2 GiB Q4_0 KV, before other memory
-c 1000000 -np 1 -fa on --cache-type-k q4_0 --cache-type-v q4_0 \
  --rope-scaling yarn --rope-scale 4 --yarn-orig-ctx 262144 \
  --override-kv qwen35.context_length=int:1000000
```

Source support does not certify Bonsai accuracy outside its advertised native range. Leave other YaRN controls at model/runtime defaults; independently measure retrieval at several depths and ordinary short-context quality. Q4 KV is an additional quantization variable. Distinguish a successful single retrieval from reliable general 1M reasoning.

For Flash, upstream b11284 explicitly handles quantized-cache rotation in its sparse-attention path. Its hybrid-indexer memory uses the selected K dtype for an extra raw indexer-key cache. Thus sparse attention's selected-token budget does **not** imply constant context memory: full K/V and indexer state still grow. Graph code also constructs masks and indexer-score tensors that depend on context and microbatch size. [Flash attention graph](https://github.com/ggml-org/llama.cpp/blob/b11284/src/models/qwen4exp.cpp), [Hybrid indexer allocation](https://github.com/ggml-org/llama.cpp/blob/b11284/src/llama-memory-hybrid-idx.cpp)

Calculated Flash lower bound, including its 128-dimensional indexer key: `12 × (2 × 2 × 256 + 128)` elements/token. FP16 is **27 KiB/token**; Q8_0, including its block scales, is approximately **14.34 KiB/token**. This excludes recurrent state, alignment, masks and workspaces.

| Flash context | FP16 cache estimate | Q8_0 cache estimate |
|---:|---:|---:|
| 32,768 | 0.844 GiB | 0.448 GiB |
| 65,536 | 1.688 GiB | 0.896 GiB |
| 131,072 | 3.375 GiB | 1.793 GiB |
| 262,144 | 6.750 GiB | 3.586 GiB |

Use Q8_0 as the next cache experiment after the measured FP16 baseline; try 64K before 128K. Lower `-ub` to 128 or 64 if temporary allocations are the blocker. Actual memory growth and long-context correctness decide the practical limit.

## Follow-up: Flash prefill performance investigation

The pinned upstream implementation contains concrete context-dependent work that can explain why short decode is fast while long prefill slows:

- `set_input_qsa` scans cache cells serially per microbatch/stream; its own TODO identifies O(context) host work. Increasing CPU thread count does not parallelize this ordinary C++ loop.
- The graph gathers and pools indexer keys, scores blocks, expands scores over cache cells, selects top-k and builds full-context masks before attention. Its sparse selection is not evidence of a fused constant-cost sparse prefill path.
- The PLE lazy loader uses CPU-backed memory mappings in b11284. Old issue reports about individual `pread` calls should not be assumed to describe this implementation.

[Host QSA construction](https://github.com/ggml-org/llama.cpp/blob/b11284/src/llama-memory-hybrid-idx.cpp), [Flash graph](https://github.com/ggml-org/llama.cpp/blob/b11284/src/models/qwen4exp.cpp), [Lazy model loader](https://github.com/ggml-org/llama.cpp/blob/b11284/src/llama-model-loader.cpp)

These mechanisms support hypotheses, not attribution from GPU utilization alone. Inspect major page faults and read bytes, and compare cold/warm requests without prefix-cache reuse before blaming SSD lookup. `--threads-batch` controls CPU backend prompt work but cannot fix serial QSA preparation. A larger microbatch can amortize per-batch overhead while increasing masks and scratch allocations; test 512 only in a profile with available VRAM, rather than assuming it fits the near-full 128K profile. No neutral CLI switch for a different QSA algorithm was found. Changing indexer top-k would alter model computation and require a new correctness evaluation. Disabling lazy mode alone may change tensor placement and attempt an additional 27 GiB resident allocation, so it is not an appropriate unverified tuning step.

## Follow-up: Prism server cap requires metadata override

The pinned Prism server unconditionally caps each slot at `llama_model_n_ctx_train`, even when a larger cache and YaRN scaling were requested. Therefore the earlier extended-context commands need this additional supported runtime override:

```bash
# 512K experiment
--override-kv qwen35.context_length=int:524288 \
  -c 524288 --rope-scaling yarn --rope-scale 2 --yarn-orig-ctx 262144

# 1M experiment
--override-kv qwen35.context_length=int:1000000 \
  -c 1000000 --rope-scaling yarn --rope-scale 4 --yarn-orig-ctx 262144
```

Source chain: the server compares slot size to the model's training-context field; the loader reads that field from `qwen35.context_length`; `--override-kv` replaces metadata in memory; explicit `--yarn-orig-ctx` takes precedence over that field when resolving YaRN's original context. The model file is unchanged. Keep the explicit original-context flag: omitting it risks using the inflated override as YaRN's baseline. [Server cap](https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/tools/server/server-context.cpp#L1158), [Metadata loader](https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/src/llama-model.cpp#L1367), [Override parser](https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/common/arg.cpp#L2918), [YaRN precedence](https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/src/llama-context.cpp#L216)

The override causes runtime metadata to report the larger value as training context; that is an experimental serving override, **not evidence the model was trained at that length**. Native context remains 262144. Read back the effective slot limit before sending a costly extended prompt.

## Follow-up: explicit vLLM KV budget

The canonical v0.28.0 CLI option is **`--kv-cache-memory-bytes`**, even though one startup recommendation prints the shortened `--kv-cache-memory`. Use the full name. The value is a per-GPU KV budget in bytes, not a total GPU memory cap. It replaces utilization-based cache sizing. A 4.5 GiB experiment is `--kv-cache-memory-bytes 4831838208`. [CLI declaration](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/engine/arg_utils.py#L1211), [Cache semantics](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/cache.py#L180)

The worker still performs `model_runner.profile_run()` to prepare the configured batched-token path. It skips automatic memory-profile sizing and returns the explicit budget, subject to any multimodal IPC reservation. Weights, activation workspaces and CUDA graphs are additional allocations. Therefore pinning KV memory removes one variable but does not guarantee OOM-free startup or requests. Confirm the reported token capacity meets the chosen context, and retain runtime headroom. [Exact worker path](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/v1/worker/gpu_worker.py#L489)

## Follow-up: Q4 KV calibration availability

No publisher-supplied mean-centering artifact was found in the file listings of the exact Bonsai model revision `b072e1d3b35a0a630cece372c2127528e0994386` or the development repository inspected. The publisher explicitly permits Q4 KV without a bias, while describing it as experimental and potentially lower quality. Therefore use **bare Q4 KV for the bounded 1M experiment**, retaining the exact model and runtime, and identify this as an additional quality variable. [Publisher KV guide](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/KV-CACHE.md)

The optional publisher calibration workflow runs `llama-kv-mean-center` on the target model with a short corpus and `-c 512`, producing a separate `kv-bias.gguf`; it does not modify model weights. Its launch script adds `--kv-mean-center FILE` and sets `LLAMA_ATTN_ROT_DISABLE=1` because its calibration uses unrotated K. A reused bias from another model or a mismatched rotation setting is unsuitable. No fresh calibration is needed just to run the proposed experiment, and none was generated during this research. [Calibration script](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/scripts/make_kv_bias.sh), [Matching launch logic](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/scripts/start_llama_server.sh)
