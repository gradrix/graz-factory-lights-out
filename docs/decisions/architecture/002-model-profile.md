# Initial model profile

Status: accepted for the bounded-task pilot, 2026-10-01.
Decision maker: agent, under the user's authorization to install the better tested local model with larger context and useful speed.

Use the downloaded ISTA-DASLab Flash-Next GSQ-RCO Coder GGUF export with llama.cpp b11284, 131072 context, Q4 K/V cache, batch/microbatch 512 and one inference slot. Keep an explicit 65536/Q8 alternative and original-vLLM rollback. The active service is separate from the original container and binds only loopback with an API key.

Rationale: this export had the strongest no-thinking result in the earlier small coding comparison. The exact 128K/Q4 configuration completed a 130580-token retrieval input in 170.86 seconds and passed twelve short checks. 128K/Q8 had poor prefill behavior; larger Flash contexts were not established. The full 32-task coding score belongs to its earlier 8K/F16 configuration, not this profile. Its reported short-context speed cannot be assumed at long contexts.

Current repository-task qualification is recorded in docs/pilot-results.md. Those tasks establish small-project behavior at the configured 128K capacity, not general coding competence over a full 128K input. Default choice remains provisional as harder tasks expose quality/latency tradeoffs. No claim of universal best model or concurrency qualification is made.

Pins: model revision 5348543e0147355ac9cbcb031184a3546350988e; llama.cpp commit 25747b08e7a0f9a59a2089ce6b98d2229b76042a; exact CUDA image ID is in ops/model.py. The GGUF SHA256 values and summarized measurements are published in docs/model-profile.md. Files were already installed and hash-verified during that study; no download was needed for this reset.

Remaining operational assumptions: Windows/WSL and Docker are running; the rig has its measured RAM/SSD resources as well as the 5090. The export uses host-mapped lookup data and is not GPU-only. No other GPU-heavy workload is admitted by GFLO. Cold-boot automation is not qualified.
