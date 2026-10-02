# Local model profile

Measured on MONSTER-GAMING-PC, September 30–October 1, 2026. These are retained experiment results, not a claim about the newest or universally best model.

## Installed default

Flash-Next GSQ-RCO Coder, the pruned ISTA-DASLab GGUF export, served by llama.cpp b11284:

- Context: 131072, Q4 K/V cache; one slot; batch/microbatch 512.
- Short warmed generation: 95.35 tokens/s in the installed profile.
- Earlier near-limit retrieval: 130580 input tokens, correct values inside Markdown fences, 170.86 seconds. Strict bare-JSON grading failed the framing.
- Current repository pilot: maximum initial prompt 16928 tokens. Full-window coding reliability is not qualified.
- Uses host-mapped lookup data as well as the 5090; not a GPU-only footprint.

Model revision: `5348543e0147355ac9cbcb031184a3546350988e`.
Runtime revision: `25747b08e7a0f9a59a2089ce6b98d2229b76042a`.
Image identity and launch flags: [ops/model.py](../ops/model.py).

Verified GGUF SHA256 values:

```text
e11083ba855e7666b48ea3f2db6a9c3a20c18751a012cc24f948de91b7087fad
316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113
```

## Earlier alternatives

| Configuration | Short warmed tokens/s | Largest exercised context | What it established |
| --- | ---: | ---: | --- |
| Original Qwen3.8 NVFP4, eager vLLM | 9.45 | 32768 configured | Baseline |
| Same checkpoint, decode graphs and explicit FP8 KV budget | 61.45 | 131072 | Two near-limit retrieval probes passed |
| Qwen3.8 UD-Q4_K_M GGUF | 77.65 | 262144 | One near-limit retrieval probe passed |
| Bonsai 2 27B PQ2_0 | 129.27 | 262144 native | Native retrieval passed; weaker no-thinking coding subset |
| Flash Coder, initial 8K/F16 profile | 102.66 | 8192 for coding subset | Strongest no-thinking result in the small subset |

The 32-task public coding subset saturated with thinking enabled: all four candidate configurations passed. That small public set is not a large-project agent benchmark. Different engines, quantizations and allocations changed together, so these compare usable profiles rather than isolated model quality.

Bonsai also completed experimental 1M-token retrieval with Q4 KV/YaRN, taking 47 minutes and decoding at about 4.6 tokens/s near the limit. This does not justify a 1M default or establish general reasoning quality at that length. Flash 128K/Q8 had poor prefill behavior; 128K/Q4 was the practical larger tested Flash profile.

Full experimental traces and downloaded models remain local. The compact current pilot receipt is [first-pilot.json](evidence/first-pilot.json). Serving, startup prerequisites and tested rollback are documented in [operations](operations.md). Future model choice is an experiment in the [roadmap](roadmap.md), not a permanent architectural dependency.
