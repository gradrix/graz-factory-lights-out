# One real request cancellation probe

Agent-defined prerequisite experiment within unit08, authorized by the user's ongoing real-rig testing request. This document fixes the scope; it does not admit execution before the harness and probe gates below pass.

## Purpose and admission

Measure whether terminating one owned completion client leaves the unchanged local model service positively idle within a bounded cleanup period. This is a lifecycle test, separate from the four project arms and their budgets. It cannot establish general cancellation reliability.

Before execution, freeze the prototype source commit, strict serving probe, cancellation driver, controlled-test and independent security results in an admission receipt. Require the unit08 contract SHA256 `d52ae8c2f322f417fed6c8cf6ace5343720cc40f86f0d0aeb6b9294e2fc33bea`, the existing serving identity, exclusive pilot lease, and two fresh idle observations. Any uncertainty refuses dispatch. Do not change the serving profile, runtime, key, installed factory or unrelated workloads.

## Request and limits

One POST only to the existing loopback completion endpoint, using alias `flash-next-coder`, temperature0, medium reasoning, 4096 maximum output tokens and1024 thinking tokens, with thinking enabled. No tools, source code or private data. Freeze and hash the exact benign counting request before admission. Persist its request and durable pretransport debit outside worker mounts. No retry or second probe after failure under this identity.

An independent supervisor starts a60second work deadline before launching the owned client in its own process group. Poll the strict serving probe freshly until busy is positively observed, the client exits, or the deadline expires. On positive busy, terminate the client group immediately; record the observation and termination timings. A request that finishes before busy is observed is inconclusive, not a successful cancellation test. Client response capture is bounded to1MiB; errors expose type and safe reason only, never headers/key/configuration.

Positive busy requires a valid same-identity slot with `is_processing is True` and healthy service; `idle:false` alone also covers unknown states and is insufficient. Immediately before TERM, confirm the client is still alive. Record exit/signal and whether a complete response already arrived. Normal completion before the stop is inconclusive. Use the existing ModelWorker.request seam for the sole POST.

At the first stop transition, start one150second cleanup deadline. All TERM/KILL waits, process-absence checks and fresh serving probes consume this same allowance. Confirm the owned client group is gone and obtain two fresh idle observations separated by at least one second, with the exact same container/image/start/profile identity. Do not erase slots, unload, restart or reconfigure the model. Unknown identity, uncertain client absence or missing idle at expiry stops the pilot without another arm.

## Evidence and interpretation

Save request hash, candidate/probe hashes, serving identity, bounded chronological observations, process lifecycle, monotonic durations, charge count, response/error if obtained, and final outcome. A pass requires observed idle before dispatch, observed busy while the request client lives, deliberate termination before its normal completion, confirmed client absence, and same-identity settled idle after termination within cleanup. Preserve inconclusive and failed outcomes explicitly. Only a passing result can clear this lifecycle prerequisite; frozen harness, fixture and independent review gates remain separately necessary for the four arms.
