# RTX 5090 local model study — September 30, 2026

**Completed on MONSTER-GAMING-PC. The original server is restored and verified.**

The strongest immediate improvement is the existing Qwen/vLLM profile: **9.45 → 61.45 warmed tokens/s**, with **131072 context** verified on two near-limit inputs. For alternatives, **Flash Coder** had the best no-thinking coding result in this small sample, while **Bonsai 2 PQ2_0** offered the fastest short-prompt decoding and the most context headroom. All four candidate configurations passed the 32-task subset with medium thinking.

**Largest verified window: 1000000 tokens with Bonsai, Q4 KV and experimental YaRN.** A 999547-token input passed exact retrieval, but took **47 minutes** and then generated at only **4.6 tokens/s**. Use native 262144 Bonsai context for normal large-context work; reserve the 524K and 1M extrapolations for offline experiments. A single successful retrieval probe does not certify general reasoning across that entire window.

## What was inspected

MONSTER-GAMING-PC runs WSL2 with an RTX 5090 reporting 32,607 MiB VRAM, 44 GiB host RAM and four exposed logical CPUs on a Ryzen 7 9800X3D. The existing `local-vllm` container serves `Inferact/Qwen3.8-27B-NVFP4` through vLLM 0.28.0+cu129, with 32,768 context, four sequence slots, FP8 KV, eager execution and a GPU-memory fraction of 0.85. It is text-only. The original container, volumes and private configuration were retained.

The use case was assumed to be coding and agent work. No private code or documents were sent to the models. All measurements below are from this rig, one request at a time except the explicitly identified baseline overlap.

## Choosing a profile

| Priority | Practical candidate | Evidence and trade-off |
|---|---|---|
| Coding with little or no thinking | Flash-Next GSQ-RCO Coder | Strongest observed no-thinking subset result, 32/32, with all custom checks and both repairs passing. Requires host-mapped lookup data and a separate upstream runtime. Large prompts are slower than Bonsai. |
| Fast generation and substantial context headroom | Ternary Bonsai 2 27B PQ2_0 | Fastest short-prompt decoding, 129 tokens/s, and native 262K retrieval verified twice. Use medium thinking for harder code: no-thinking accuracy was lower on this subset. |
| Keep the unpruned dense Qwen base in a compact format | Qwen3.8-27B UD-Q4_K_M | 31/32 without thinking, 32/32 with it, and a real near-262K request passed. Slower than Bonsai, with less memory headroom. |
| Keep the existing vLLM integration and weights | Graph-enabled NVFP4 profile with explicit KV budget | 61.45 tokens/s, about 6.5 times the original warmed speed, and two near-131K requests passed in about 36 seconds each. Uses one sequence slot instead of four. |

These are choices among measured configurations, not proof of a universal best model for every 5090 workload. The coding sample is small and public, all medium-thinking scores reach its ceiling, and general knowledge, multilingual work, vision and production-scale agent reliability were not qualified. The Bonsai publisher also lists unresolved tool-loop and malformed-call issues; two passing repair workflows do not override that warning. See the cited research for those known issues.

## Short-context comparison

Generation speed is the average of two warmed 256-token counting generations. It is neither prompt-processing speed nor concurrent throughput. The custom suite comprises eight code tasks, three tool-argument checks, one JSON task and two small tool-driven repair workflows.

| Configuration | Warm generation, tokens/s | Custom checks + repairs | HumanEval subset, no thinking | Same subset, medium thinking |
|---|---:|---:|---:|---:|
| Original vLLM, eager, 32K | 9.45 | 14/14 | Not run | Not run |
| Same NVFP4 checkpoint, vLLM decode graphs, 64K | 59.59 | 13/14 | 30/32 | 32/32 |
| Same NVFP4 checkpoint, decode graphs, 131K, explicit 4.5 GiB KV | 61.45 | 11/12 short checks; repairs not repeated | Not repeated | Not repeated |
| Qwen3.8-27B UD-Q4_K_M, Prism, 32K | 77.65 | 14/14 | 31/32 | 32/32 |
| Ternary Bonsai 2 27B PQ2_0, Prism, 32K | 129.27 | 13/14 | 28/32 | 32/32 |
| Flash-Next GSQ-RCO Coder, upstream llama.cpp, 8K | 102.66 | 14/14 | 32/32 | 32/32 |

The HumanEval numbers are a fixed 32-task chat adaptation, selected with seed 5090 from the original public 164-task dataset. They are not official full HumanEval scores. Temperature was zero; no-thinking output allowance was 1,024 tokens and medium-thinking allowance was 4,096 including reasoning. All canonical solutions passed the grading sandbox before model evaluation. The small, public set can be memorized and has a ceiling effect: 32/32 does not establish equal general coding ability.

Model, quantization, serving engine and context allocation differ together. These measurements compare usable configurations, not isolated quantization quality. All GGUF contenders used the same OpenAI-compatible client settings; the Flash model needed a newer, separate runtime. Large-window generation slows down substantially.

Token rate alone also misses reasoning length. Across the 32 medium-thinking tasks, Bonsai took 191.95 seconds of summed request time for 23,660 output tokens, while Flash took 190.40 seconds for 17,171 tokens. Qwen GGUF took 262.24 seconds for 19,651 tokens. These sums exclude the separate grading containers. Bonsai's faster decoding did not make this particular reasoning suite faster than Flash.

Graph-enabled vLLM took 440.64 seconds for 26,642 output tokens on that same suite. Its earlier four-task diagnostic failed one case that passed in the later complete run; both are retained. One temperature-zero sample does not establish repeatability or general reliability.

### Observed failures

- Graph vLLM failed the custom CSV task by exhausting its 768-token allowance. Its no-thinking HumanEval failures were a stray closing code fence and one arithmetic-precedence error.
- Bonsai failed the custom CSV task and four no-thinking HumanEval tasks. Medium thinking passed all 32 selected tasks.
- Qwen GGUF failed one no-thinking HumanEval task; medium thinking corrected that case and passed all 32.
- The four-task thinking diagnostics preceded the complete 32-task runs and are reported separately in raw artifacts. Do not mix their denominators.

## Context actually exercised

Each strict probe requests three random facts placed at 10%, 50% and 90% depth, plus an absent-key result. Distractor records are unique, actual server tokens are counted, and exact JSON is required. This proves retrieval on those inputs; it does not establish reliable synthesis or code understanding throughout the window.

| Profile | Configured window | Largest tested input | Strict result | Near-limit response time |
|---|---:|---:|---|---:|
| Original vLLM eager, FP8 KV | 32,768 | 31,504 | 1/2 random probes; both contained all values | Timing excluded: one overlap |
| Tuned vLLM eager, FP8 KV | 98,304 | 96,540 | 2/2 near-97K probes | 29.9–30.1 s |
| vLLM decode graphs, FP8 KV | 65,536 | 64,514 | 2/2 | 12.9–13.1 s |
| vLLM decode graphs, explicit 4.5 GiB FP8 KV | 131,072 | 130,580 | 2/2 | 36.2–36.3 s |
| Qwen GGUF, Q8_0 KV | 262,144 | 261,599 | 1/1 | 237.1 s |
| Bonsai, F16 KV | 262,144 | 261,627 | 2/2 at maximum; 8/8 across four sizes | 223.5–223.8 s |
| Flash, Q8_0 KV, batch 512 | 65,536 | 65,045 | All four values correct; Markdown fence fails strict JSON | 81.8 s |
| Flash, Q4_0 KV, batch 512 | 131,072 | 130,580 | All four values correct; Markdown fence fails strict JSON | 170.9 s |
| Bonsai, Q8_0 KV, experimental YaRN factor 2 | 524,288 | 523,724 | 1/1, exact JSON | 824.5 s (13 min 45 s) |
| Bonsai, Q4_0 KV, experimental YaRN factor 4 | 1,000,000 | 999,547 | 1/1, exact JSON | 2820.5 s (47 min) |

Bonsai's other native-window probes took about 10 s at 31.5K input, 26 s at 65K, and 70 s at 130.6K. At 261.6K input, generation fell to about 54 tokens/s after approximately 222 seconds of prefill. Qwen GGUF generated about 36 tokens/s after approximately 235 seconds of prefill at the same input length.

vLLM's initial 131072 graph attempt failed automatic capacity validation: 4.31 GiB KV required versus 2.49 GiB available, with an estimated supported maximum of 72,128 tokens. A later identical 64K graph restart reported 4.59 GiB available instead of 2.36 GiB, so the initial failure was not treated as a fixed hardware ceiling. Setting `--kv-cache-memory-bytes 4831838208` made the larger experiment explicit: the 131072 profile started at 30753 MiB total GPU memory, retained 61.45 tokens/s on warmed short generations, and passed both 130.6K probes. They took 36.30 and 36.20 seconds, with first output after about 35 seconds and subsequent generation around 54 tokens/s. This KV setting overrides automatic cache sizing; it is not a total VRAM cap.

The 131K profile passed 11/12 short checks; CSV failed an assertion, whereas the earlier 64K CSV failure exhausted its output budget. The complete HumanEval and repair results belong to the 64K profile and were not silently relabeled as 131K tests. At 65K in the separate eager profile, one response repeated otherwise correct JSON and hit the output limit; this remains a strict failure.

### Flash capacity and latency boundary

Flash loaded at 131K with Q8 KV, using 32,065 MiB total GPU memory. Its first 31.5K input took 232.45 seconds. Reducing the allocation to 64K and increasing batch/microbatch from 256 to 512 cut the same input to 37.11 seconds. Host lookup-table pages were also warmer, so that is a configuration comparison, not an isolated batching experiment.

A renewed 131K/Q8/batch-512 attempt made very slow prefill progress and was deliberately cancelled. It was neither an OOM nor a completed correctness failure. Switching that configuration to Q4 KV used 31,678 MiB at readiness and completed a real 130,580-token input in 170.86 seconds. It generated approximately 27 tokens/s after 168.10 seconds of prefill. The twelve short custom checks passed under both the 64K/Q8 and 131K/Q4 profiles; the complete HumanEval comparison used the 8K/F16 profile, so its score should not be treated as a full qualification of the larger-cache variants.

All four completed Flash retrieval probes returned the correct values inside Markdown fences. Raw strict grades remain failures; no answer repair was applied selectively. Applications requiring bare JSON should use a separately tested structured-output contract or normalize framing explicitly. The research report identifies source-level prefill work that may contribute to the slowdown, but this study does not isolate the dominant kernel or paging cause.

### Experimental Bonsai extension

The initial 512K launch allocated the requested cache but the pinned Prism server capped its request slot to the model's native 262144. A real 523724-token request was rejected with HTTP 400. This was a serving cap, not an observed memory or retrieval failure.

The supported workaround adds `--override-kv qwen35.context_length=int:524288` while retaining `--rope-scaling yarn --rope-scale 2 --yarn-orig-ctx 262144`. The override changes runtime metadata, not the model file or its actual training history. The explicit original context keeps YaRN anchored at 262144. The revised launcher now reads back the server's actual request limit and fails when it is smaller than requested. This profile uses 524288/Q8 KV and consumed 28406 MiB total GPU memory at readiness. Publisher-supported Bonsai context remains 262144.

The corrected 524K profile completed 523724 input tokens plus 69 output tokens, returning all facts and the absent-key result in exact JSON. Total time was 824.55 seconds, with 821.95 seconds until first output and approximately 26.2 tokens/s thereafter. Its exact configuration also passed all twelve short regression checks after that request.

The 1M profile used Q4_0 KV, YaRN factor 4, the same explicit original context, and `qwen35.context_length=int:1000000` as its runtime override. Actual slot readback was 1000000; total GPU memory at readiness was 30881 MiB. It passed twelve short checks, a 31504-token retrieval probe, and then the full **999547-input-token** probe. The full request returned 69 output tokens in exact JSON, with zero cached input tokens reported. Total time was **2820.46 seconds**, first output arrived after **2805.57 seconds**, and subsequent generation was approximately **4.57 tokens/s**. The short-context 129-token/s headline does not apply at this length.

These are single successful retrieval probes under experimental extrapolation, not general long-context quality guarantees. Bare Q4 KV is explicitly experimental in Prism's guidance. No matching publisher calibration file was found, so no unrelated calibration was reused. This study stops at the Qwen family's advertised 1M extension range; it does not establish an absolute physical limit for every possible CPU/GPU offload configuration.

## Research and scope

The [primary-source research](model-research.md) covers Qwen3.8, Flash-Next, Bonsai 2, Swift 1.5, Gemma 4, Nemotron 3 Nano and GLM-4.7-Flash, including model identities, licenses where relevant, memory calculations, pinned artifacts and engine support. Only the configurations in the measured tables were run. SGLang, speculative decoding, vision, production concurrency and a real GFLO repository pilot were not tested.

Flash's 6B active-parameter count is not its memory footprint. The tested Coder export prunes half the experts; it is not the complete official Flash-Next model. Its files comprise about 27.57 GiB transformer weights and 26.82 GiB lookup data, with the latter read lazily from SSD/host cache. This distinction matters when interpreting both quality and cold-start behavior.

## Reproduction and artifacts

### Exact temporary profiles on the rig

Run these from `/home/gradrix/benchmark-5090`. Each command replaces the temporary server and stops the original while it runs. The experimental API is exposed only at host loopback port 18000. These are test launches, not permanent deployment edits.

```bash
# Existing model: fast decoding and a verified 131072 window.
python3 profiles.py vllm --context 131072 --graphs --kv-bytes 4831838208

# Bonsai: publisher-supported native window, full-precision KV.
python3 profiles.py bonsai --context 262144 --cache f16

# Flash Coder: larger tested window, compressed KV, host-mapped lookup data.
python3 profiles.py flash --context 131072 --cache q4_0 --batch 512

# Original dense Qwen base in GGUF form.
python3 profiles.py qwen --context 262144 --cache q8_0

# Experimental Bonsai extension, one full near-limit retrieval probe passed.
python3 profiles.py bonsai --context 524288 --cache q8_0 --scale 2

# Extreme experimental profile: validated retrieval, approximately 47-minute prefill.
python3 profiles.py bonsai --context 1000000 --cache q4_0 --scale 4

# Return to the unchanged original service and verify it.
python3 profiles.py restore
python3 verify_restore.py
```

For the GGUF servers, the measured client modes are `reasoning_effort: "none"` and `reasoning_effort: "medium"`, with the server using `--reasoning auto`. The harness records the entire request body and includes the corresponding chat-template settings. Do not assume that a similarly named UI preset uses the same reasoning budget. Context capacity includes prompt, chat formatting, reasoning and output; leave substantially more than the benchmark's 512-token reserve for real coding answers.

See [README.md](README.md) for the automated runner and sandbox protocol; [summary.json](summary.json) for computed totals; `results/*.jsonl` for actual prompts, responses, timings and grades; and `profiles/` plus `logs/` for launch commands and startup evidence. Checksums and model/runtime revisions are recorded in the research document. Downloaded weights and runtime binaries remain on the rig under `/home/gradrix/benchmark-5090`.

The experimental servers bind only host loopback port 18000. Private restore metadata and API credentials remain only on the rig in mode-0600 files and are excluded from this study directory. The original server uses port 8000.

## Final state and verification

- `local-vllm` is running with its original container ID, image, command, environment, mounts and port bindings. The cached model revision still matches `6128240ebaf4eaa7bad2b3d1c72c37d677c5f462`.
- Authenticated `/v1/models` reports `qwen3.8-27b`, `Inferact/Qwen3.8-27B-NVFP4`, and `max_model_len: 32768`. A synthetic generation returned the expected `42`. The temporary benchmark server is absent. All eleven checks in [restoration-check.json](restoration-check.json) passed.
- The dataset hash and task order match across all eight full 32-task coding runs. The seeded replay audit preserved all eight recorded outcomes for the sole randomized selected test. See [random-grading-audit.json](random-grading-audit.json) and [grading-environment.json](grading-environment.json).
- A scan of 96 export candidates found no matching credential values from the original container's secret environment variables. Private files were excluded from collection.
- Downloaded models, runtimes, scripts and raw results remain under `/home/gradrix/benchmark-5090`, occupying approximately **78 GiB**. No permanent serving configuration was changed. Repository additions are confined to this study directory; no commit or push was made.
