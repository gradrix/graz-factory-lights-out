# Add turn-bound repair handles without weakening source identity

Type: task
Status: resolved

## Scope

Replace manual SHA256 copying in model repair instructions with short opaque targets
mapped by the controller to full file hashes, exact current draft and work contract.
Mint fresh targets each turn, restrict to visible writable files, persist mapping as
immutable evidence. Reject unknown/stale/cross-contract targets; retain legacy hash
repair parsing, edit limits, scope checks and final gates. Same model and budgets.

## Answer

Added repair_handle responses and controller-owned RepairTargets mappings. Full source
bundle and contract digests bind each mapping; individual entries retain full SHA256.
Only visible writable files receive targets. Persist mappings before tokenization;
resolve through existing hash/exact-match/overlap/scope enforcement. Legacy repairs
remain supported. New targets are minted each turn.

Seen color worker trial reused the unchanged reviewed plan/model/gates/budgets and
passed. No target or hash protocol errors; implementation semantic retry remains.
Five implementation responses across two attempts, one test response. Replay adds
no calls; 85 original files unchanged. No new target product edits. All 449 tests
and 25 subtests pass with Docker enabled; ruff/mypy pass.

[Results](../repair-handles-results.json) include the plan and mappings. Reconstruct
with leds-color-v2-fixture.json, then use the saved plan with run-feature; no new
planning is needed. Raw evidence: .gflo/evidence/leds-color-handles-v1. Broader trials
are needed before a reliability claim; planner source-reference retry is next.
