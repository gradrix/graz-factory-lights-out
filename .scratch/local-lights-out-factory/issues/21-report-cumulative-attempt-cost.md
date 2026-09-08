# Report cumulative Attempt cost

Type: task
Status: resolved
Blocked by: 19

## Scope

First bounded Stage 2 reporting increment. Add a read-only CLI report from durable
Attempt observations, including failed Attempts and retries. Report validated
prompt/completion usage and observed model time separately from missing evidence.
Do not infer complete costs from successful turns, mutate history, or claim
replan accounting before a replan scheduler exists.

## Acceptance

Preserve per-Attempt provenance and failures; report cumulative and retry usage,
missing validated usage/timing, and explicit measurement limits. Hash-verify
referenced artifacts. Test failed turns, retries, corruption and repeated reads;
run against the retained real-model pilot ledger.

## Answer

Added `gflo --db PATH report ATOM_ID`: cumulative/per-Attempt observations, retry totals, validated token counts, observed model time, failure provenance and explicit missing-accounting indicators. Artifact reads verify hashes; no history changes or model calls. Three focused tests cover retries with unavailable usage, corrupt turn artifacts and legacy missing timing. Retained graph-pilot reports reproduce 12,166 prompt and 2,061 completion tokens including retry observations. Full suite: 166 tests, 25 subtests passed; eight optional Docker tests skipped. Costs lost before durable observation and replanning are explicitly outside this report.
