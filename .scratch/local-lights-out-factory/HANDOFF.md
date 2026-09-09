# GFLO handoff — supervised self-trial ready for review

## Current checkpoint — 2026-09-09

User asked to observe and improve a bounded GFLO self-modification trial. Completed
qualification checkpoint was committed locally as `3cdd83e`. The main CLI is unchanged.
A reviewed local-model candidate adds `history ATOM --attempt N` on branch
`trial/history-attempt-filter`, commit `091654a`, in `.gflo/self-trial-checkout`.
Await owner review before merging, per the agreed supervised trial. Nothing pushed.

First campaign failed on a guessed provider field and missing-ordinal handling.
A new campaign with exact result shape and explicit missing-ordinal behavior passed
3/3 runs in five attempts. All candidates passed 279 tests + 25 subtests each,
eight optional Docker skips. Selected candidate lint and mypy passed. This is one
seen feature repeated, not large-system qualification or autonomous self-improvement.

Added a pinned CPython 3.11/Linux x86-64 dependency image recipe and wheel-hash lock
under `infra/worker/`. Trusted acquisition/build only; candidate containers remain
restricted and offline. Full repository/tests exceed 256 KiB; reviews used bounded
batches without increasing limits. All runtime source was available in each batch.

## Next actions

1. Owner reviews `git diff 3cdd83e..091654a` and chooses whether to merge the CLI
   feature. Branch includes the 19-line implementation, tests, and usage docs.
2. Diagnose recurring resource-probe halts in [issue 30](issues/30-diagnose-memory-qualification-halts.md).
   Memory probe can exit 137 without Docker OOMKilled. Do not accept exit code alone
   or weaken controls. Explicit unchanged requalification succeeded.
3. Apply exact provider-result contracts systematically when preparing further tasks;
   only split workers where independently validated ownership justifies it.

[Portable trial results](self-history-trial-results.json) retain manifests, costs,
candidate hashes, and complete regression summaries. Raw evidence under `.gflo/evidence/`:
`self-history-filter-v1` (failed), `self-history-filter-contract-v1` (passed),
`self-history-review-v3` (passed). Earlier review v1 failed on a harness field access;
v2 halted on resource qualification. Both preserved. Image and raw evidence need
separate transfer or recreation. Git branch/commits preserve the actual feature.

[Issue 29](issues/29-trial-history-attempt-filter.md) is ready-for-human, trial work
complete. [Previous checkpoint](handoff-before-self-trial-2026-09-09.md) preserves
stateful workload results and reproduction commands. Keep `.scratch/` tracked.
