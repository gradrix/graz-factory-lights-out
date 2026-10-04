# Arm 4 and whole-run accounting readback

**Arm 4 outcome: FAILED. Accounting/lifetime/manifest readback: PASS.** Arm `4-config-preview-direct`, child `a8aac6d4726e`, exhausted the shared 48-request budget. The parent persisted failed/exit 1 and the child persisted interrupted; no accepted receipt or final review exists. This independent audit used only local saved evidence: no candidate execution, rig access or model call.

[Detailed accounting, hashes and whole-run totals](arm4-accounting.json), [read-only reproduction](arm4-accounting-audit.py). All 410 reviewed arm files stayed byte-identical during the audit; the completed SQLite database was opened immutable/read-only, with no WAL present.

## Attempts and the refused next transport

All 48 charged requests are implementation calls, with complete raw/canonical request and response captures. Ledger numbers, request directories and durable progress reservations are exactly 1–48. Raw bodies parse to their canonical files; ledger hashes, HTTP 200 complete-byte receipts and usage match. Every response has finish_reason `tool_calls`; there is no normal model final-answer response.

| Attempt | Planned worker requests | Returned transports | Recorded outcome |
|---|---:|---:|---|
|1|24|24|Turn limit; full acceptance and package/test check failed|
|2|24|24|Turn limit; full acceptance failed; package/test check passed|
|3|1|0|Shared request budget refused transport|

Attempts 1 and 2 each record `Model turn budget exhausted`, `limited:true`. Attempt 3's trajectory contains a planned turn 1 request but no response or transport capture. The worker writes that trace before entering the budget wrapper. The unchanged pretransport reservation guard, exact 48 capture/ledger count and durable interruption error establish that the planned request was refused before a 49th transport. This is evidence through the frozen controlled request path, not an independent network packet capture.

These are three **documented internal attempts within the fixed limit**, not hidden extra arm retries. Each used the same arm budget. No planner, question assessment or code review consumed a request here: checks failed before review admission. The absence of final-verification/final-review/accepted artifacts agrees with failed parent status and `integrity_confirmed:false`. The retained partial workspace fingerprint `ed33eb40d9abf8175f80ebcc47153576a6c0eec10ba42bfc39b4b3ee253395ba` is not an accepted candidate.

## Arm 4 profile, usage and time

All calls retain `flash-next-coder`, temperature 0, medium reasoning, 4096 output / 1024 thinking caps, enabled thinking and exactly run/check/question tools. Maximum raw request 190164 bytes and response 11600 bytes remain below capture limits.

| Reported metric | Value |
|---|---:|
|Prompt tokens|1148091|
|Completion tokens|39305|
|Total tokens|1187396|
|Cached prompt tokens explicitly reported|1099131|
|Missing values for these four fields|0 of 48 calls|
|Work / cleanup|963.9860s /1.2505s|
|Sum of request elapsed times|822.2100s|
|Request latency min / median / max|4.1263s /12.7238s /49.0731s|

Failure was the request ceiling, not the 1800-second work deadline. Cleanup remained within 150 seconds. Cached tokens are a subset of repeated prompt usage; they are not added to total. No missing usage, independent reasoning-token count or aggregate token ceiling is invented.

## Fixed inputs, checks and execution boundary

The child contract keeps the full original objective, full-phase check, three-attempt/24-turn limits, required review and approved `python-api` environment. Its hash matches the database. Acceptance bytes/fingerprint and all nine original source files match the frozen manifest; dependency-bound project inputs remain unchanged in the partial workspace. The two recorded verification failures remain failures; this audit does not reinterpret their semantic causes or rerun the candidate.

The environment receipt is `e591c2d6f97b02fc2a99ecef01848a4e74d743e499aeec3b4d4d7d6c6c400acb`, pinned executor image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`. Saved runtime versions match the approved Python 3.12.13/API profile; no remote receipt was re-resolved.

All 59 executor creation records show approved nonroot/runc/network-none/readonly-root/cap-drop/no-new-privileges/resource limits and no devices/GPU requests. Mounts are only the exact child workspace plus read-only dependencies; eight also have read-only acceptance and workspace. No credential, socket, private reference or unrelated host mount appears. Final exact-label absence, client-group absence, no uncertainty marker and confirmed cleanup are recorded. Per-operation absence remains supported by the frozen attestation/fence path; individual daemon absence replies are not separately persisted.

Four serving observations form preflight and cleanup idle pairs separated by 1.1178s and 1.1180s, all with the unchanged approved container/image/start identity and one 98304/Q4/Q4 slot. No additional live observation was made here.

## Whole-run manifest and totals

Independently verified **all 1334 artifact entries**, not only the coordinator's Boolean report. Manifest SHA256 `83340a9d6356ea9186e4ff117493975fa1a84056c7b560c532b23eedb3ef6c5d` matches both downloaded copies and `trial-download-integrity.json`. Each local file hash matches. The actual file set also matches after the writer's documented exclusions: `.git` metadata and the manifest itself. The summary's four rows equal their individual arm results exactly; earlier accounting evidence hashes still match the completed copies.

Frozen order is retained: stdlib direct, stdlib decomposed, API decomposed, API direct. Per-arm charged counts are **23, 36, 48, 48**. Every arm has client-group absence, cleanup and fresh idle confirmation; all serving identities agree. Executor creation records total 174.

| Four-arm aggregate | Total |
|---|---:|
|Charged project requests|155|
|Implementation / code review / planner / plan review|145 /6 /2 /2|
|Reported prompt tokens|2989323|
|Reported completion tokens|118151|
|Reported total tokens|3107474|
|Explicit cached prompt tokens|2810509|
|Sum of arm work durations|2653.3877s|
|Sum of cleanup durations|5.0385s|
|Sum of request elapsed durations|2430.7249s|

All 155 project responses report all four usage fields. The separate admitted cancellation experiment consumed one additional request; it returned no usage and is **excluded** from these token totals. Work/cleanup sums are component durations, not an invented end-to-end experiment wall time including preflight/staging.

The Factory outcomes remain **accepted, accepted, failed, failed**. Independent semantic verdicts belong to QA and may differ from Factory acceptance. No failed trajectory is promoted or omitted in these records; all recorded retries are admitted internal attempts. Two cases do not establish a reliability rate or planning superiority.
