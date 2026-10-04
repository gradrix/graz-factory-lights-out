# Arm 1 accounting and boundary readback

**PASS for persisted accounting and execution-boundary evidence.** Arm `1-manifest-reconcile-direct`, run `b420f7770b76`, Factory accepted candidate `5dc1f9fd353e215802c8b363f20db41371ae5db99b086601c054a348bb3d918d`. This is read-only review of the completed local copy while other arms run. No candidate execution, rig access, endpoint request or model call. Semantic, test and documentation review belongs to separate QA; Factory acceptance is not relabeled as independent semantic acceptance here.

[Machine-readable results and per-call hashes](arm1-accounting.json), [read-only reproduction](arm1-accounting-audit.py). All 220 reviewed local files remained byte-identical during the audit.

## Calls, captures and profile

- **23 of 48 completion requests:**21 implementation and2 code reviews. No planner, plan-review or question-assessment request occurred in this direct arm. Ledger numbers and durable progress reservations are exactly 1–23, with no gaps, duplicates or additional request directories. One Factory attempt is recorded, within 3 attempts / 24 worker turns.
- Every call has canonical request/response, raw request/response and transport receipt. All 23 raw bodies parse to their canonical counterparts; canonical hashes match the ledger, reported usage matches each response, and transport records are HTTP 200 / complete with exact raw byte counts. All statuses are returned;20 responses end in tool_calls and3 in stop. Maximum raw request 103361 bytes, maximum raw response 11395 bytes, below the configured 4 MiB / 1 MiB capture bounds.
- Every request uses `flash-next-coder`, temperature 0, 4096 max output, medium reasoning, 1024 thinking and enabled thinking. Implementation tools are exactly run/check/question; reviews have no tools/functions. Raw bodies contain payloads, not authentication headers; credentials/config were not read by this audit.

## Reported usage and latency

| Metric | Total / observation |
|---|---:|
|Prompt tokens reported|322919|
|Completion tokens reported|15612|
|Total tokens reported|338531|
|Cached prompt tokens explicitly reported|301883|
|Missing values for any of these four fields|0 of 23 calls|
|Work elapsed|321.0771s of 1800s|
|Cleanup elapsed|1.2523s of 150s|
|Sum of measured request elapsed times|305.5564s|
|Request latency minimum / median / maximum|2.8967 /10.4799 /37.3088s|

Prompt and total usage are sums across repeated conversation requests, not unique input volume. Cached prompt tokens are an explicit reported subset, not extra tokens added to the total. No aggregate token ceiling, unreported reasoning-token count, missing usage estimate or inferred server cancellation is claimed. Per-response timing fields are retained as reported in the JSON without substituting them for controller elapsed time.

## Fixed acceptance and environment

The saved contract hash, accepted candidate fingerprint, patch hash and verification/review artifact hashes match local bytes. The copied acceptance fingerprint and each acceptance file match the frozen fixture manifest. The 8 original source files exactly match the frozen source fixture. Full acceptance remains the fixed `python -I /acceptance/check.py --project /workspace --phase full`, supplemented by generated unittest discovery. Both final checks exited 0; the persisted generated-test output reports 11 tests. Their substantive usefulness is left to QA.

Task and child environment bindings equal the approved `python-stdlib` receipt `36cd138cbdc332246a2db473301200117f82404a4504c675db95966645348975`, pinned executor image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, Python 3.12.13. This readback compares saved approved bindings; it does not re-resolve the remote environment during the timed experiment.

## Executor and serving lifecycle

All 25 unique executor creation records show runc/networknone, nonroot 1000:1000, readonly root, cap-drop ALL, no-new-privileges, 1 GiB memory/swap, 2 CPUs, 128 PIDs, 16 MiB shared memory and no devices/GPU requests. Mounts are limited to this run's workspace and read-only approved dependencies; 6 executors also have the exact read-only acceptance directory with read-only workspace. No credentials, Docker socket, private references or unrelated host path appears in the mount set.

The final receipt records the exact workspace-label absence, no removals required, client group absent, cleanup confirmed and no uncertain-executor marker. Creation records do not individually contain daemon absence replies: per-operation cleanup completion is supported by the frozen attestation/fence control flow and successful continuation; final absence is explicitly recorded. No live daemon inspection was repeated.

Four fresh serving observations form preflight and cleanup idle pairs separated by 1.1672s and 1.1175s. All carry the same approved container/image/start identity and one idle 98304/Q4/Q4 slot. Parent records exit 0, no stop reason, before-deadline work and confirmed integrity. These facts support this completed arm's boundary accounting; they do not clear a later arm without its own fresh observations or establish comparative planning value.
