# Initial model profile

Status: accepted for the bounded-task pilot, 2026-10-01.
Decision maker: agent, under the user's authorization to install the better tested local model with larger context and useful speed.

Use the downloaded ISTA-DASLab Flash-Next GSQ-RCO Coder GGUF export with llama.cpp b11284, 131072 context, Q4 K/V cache, batch/microbatch 512 and one inference slot. Keep an explicit 65536/Q8 alternative and original-vLLM rollback. The active service is separate from the original container and binds only loopback with an API key.

Rationale: this export had the strongest no-thinking result in the earlier small coding comparison. The exact 128K/Q4 configuration completed a 130580-token retrieval input in 170.86 seconds and passed twelve short checks. 128K/Q8 had poor prefill behavior; larger Flash contexts were not established. The full 32-task coding score belongs to its earlier 8K/F16 configuration, not this profile. Its reported short-context speed cannot be assumed at long contexts.

Current repository-task qualification is recorded in docs/pilot-results.md. Those tasks establish small-project behavior at the configured 128K capacity, not general coding competence over a full 128K input. Default choice remains provisional as harder tasks expose quality/latency tradeoffs. No claim of universal best model or concurrency qualification is made.

Pins: model revision 5348543e0147355ac9cbcb031184a3546350988e; llama.cpp commit 25747b08e7a0f9a59a2089ce6b98d2229b76042a; exact CUDA image ID is in ops/model.py. The GGUF SHA256 values and summarized measurements are published in docs/model-profile.md. Files were already installed and hash-verified during that study; no download was needed for this reset.

Remaining operational assumptions: Windows/WSL and Docker are running; the rig has its measured RAM/SSD resources as well as the 5090. The export uses host-mapped lookup data and is not GPU-only. No other GPU-heavy workload is admitted by GFLO. Cold-boot automation is not qualified.

## Superseding trial default, 2026-10-02

Decision maker: agent, under the same authorization. Use 98304/Q4 for the next qualification runs; retain explicit 131072/Q4 and 65536/Q8 options and permit explicit KV type for controlled comparisons. This supersedes the original default allocation above, not historical qualification results or the model/runtime pins.

An identical 16947-token prompt decoded at a warm median16.52tokens/s on128K after restart,74.92 on64K/Q4 and73.95 on96K/Q4. Only allocation changed. 96K also retrieved three exact values across81441 inputtokens in96.72seconds. VRAM residency pressure is the likely mechanism; allocation-sensitive throughput is measured, but memory residency itself was not traced. 96K is the largest tested allocation retaining speed, not the physical maximum.

The original environment cohort accepted1/3 and retained two900-second timeouts. Fresh independently checked API and TypeScript tasks will qualify the new setting; retrieval does not establish full-window coding reliability. Evidence and remaining limits: [profile](../../model-profile.md), [throughput experiment](../../../.scratch/autonomy/issues/05-serving-throughput.md). Revisit this reversible choice if desktop GPU load or project context needs change.
