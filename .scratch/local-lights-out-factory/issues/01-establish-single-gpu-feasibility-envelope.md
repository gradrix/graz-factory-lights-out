# Establish the single-GPU feasibility envelope

Type: research
Status: resolved
Blocked by:

## Question

What context sizes, quantizations, serving engines, throughput, concurrency, structured-output behavior, tool-use behavior, and long-horizon reliability are realistically available to Qwen3.8-27B on Linux with one 32 GB RTX 5090 and 64 GB system RAM, and which claims require local benchmarking rather than documentary acceptance?

## Comments

### Resolution — 2026-09-02

Qwen3.8-27B is feasible on one 32 GB RTX 5090 as a serialized, bounded inference worker, not as a monolithic long-context or multi-request service. Adopt SGLang plus the NVFP4 checkpoint provisionally; use 8K Work atoms by default, 16K when justified, an initial hard cap of 32K, and one physical request in flight. Treat 64K–96K as experimental and 262K as unavailable until proved locally. Schema-constrained output provides syntax, not semantic correctness, and no source establishes multi-day autonomous reliability; deterministic gates, durable state, bounded retries, and a 72-hour fault-injected soak remain mandatory.

Full cited report: [Single-GPU feasibility envelope for Qwen3.8-27B](../research/single-gpu-feasibility-envelope.md)
