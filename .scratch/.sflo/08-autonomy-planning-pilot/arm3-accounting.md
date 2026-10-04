# Arm 3 failure accounting and boundary readback

**Arm outcome: FAILED at the shared request limit. Accounting/lifetime readback: PASS.** Arm `3-config-preview-decomposed`; milestone `ba6255bd4d74` remains accepted; child `300151e5e413` is durably interrupted; the parent is failed with `Shared completion request budget exhausted`. No milestone pass was promoted to final acceptance.

This review reads the completed local copy only. No candidate execution, rig/model/endpoint call or remote inspection. [Detailed audit and hashes](arm3-accounting.json), [read-only reproduction](arm3-accounting-audit.py). All 457 reviewed files stayed byte-identical during the audit, including the SQLite database read with immutable/read-only mode and no WAL present.

## Exact exhaustion and no 49th transport

The shared ledger contains **48 of 48** charged requests, numbered exactly 1–48, matching the durable progress reservations and exactly 48 request directories. Every directory contains complete raw/canonical request and response bodies plus its HTTP200 transport receipt; all canonical hashes, raw byte counts and reported usage match. No failed transport was silently removed or reset.

| Allocation | Charged calls |
|---|---|
|Planner / plan review|1 / 2|
|Task 1 implementation / code review|3–26 / 27|
|Task 2 implementation|28–48|
|Task 2 review / final full review|None|

Task 1 used its full 24 worker turns (`limited:true`) and then passed milestone checks/review. Task 2 received 21 returned implementation responses. Its trajectory contains **22 planned request events but only 21 responses**, ending at planned turn 22. That final trace event is written before the request wrapper; it is not a 49th HTTP request. The wrapper's frozen pretransport reservation rejected it, as corroborated by the interruption record, parent failure, unchanged 48-entry ledger and absence of request49/raw-transport artifacts. This establishes denial through the reviewed transport path; no independent network packet capture is claimed.

The persistent database records task 1 accepted/one attempt and task 2 interrupted/one attempt with the exact shared-budget error. Task 2 has no accepted receipt or completed worker result. Parent exit code is 1, status failed and integrity_confirmed false; no final-verification or final-review artifact exists. The recorded partial task 2 workspace fingerprint `93275b3e323ea486cdb544c6126fe98883ee184f15f1bf8c9c27a12af6479c9c` is evidence of retained work, not an accepted candidate.

## Profile, usage and elapsed time

All 48 requests retain `flash-next-coder`, temperature 0, medium reasoning, 4096 output / 1024 thinking caps and enabled thinking. Tools are exactly run/check/question on implementation requests; planner/reviews are tool-free. The maximum raw request is 196561 bytes and response 14622 bytes, within capture bounds. There are 45 implementation, one planner, one plan-review and one code-review request. Finish reasons are 45 tool_calls and three stop.

| Reported metric | Value |
|---|---:|
|Prompt tokens|1106081|
|Completion tokens|38751|
|Total tokens|1144832|
|Cached prompt tokens, explicitly reported|1043590|
|Missing values for these four fields|0 of 48 calls|
|Work / cleanup|873.5400s / 1.2695s|
|Sum of request elapsed times|828.1558s|
|Request latency minimum / median / maximum|3.3075s / 15.8038s / 54.5403s|

The request limit caused failure before the 1800-second work deadline. Cleanup stayed within 150 seconds. Totals include repeated conversation input; cached prompt tokens are a subset, not extra total tokens. No aggregate token ceiling, missing-value estimate or separate reasoning-token count is invented. Original server timing fields remain in the JSON.

## Plan, fixed checks and actual handoff

Saved plan and passing plan review exactly match charged responses 1/2. The review received the original public input plus the returned plan. Task 1 covers B1/B2; task 2 covers B3–B5 and depends on task 1. Together they cover all frozen requirement IDs. Both child contracts keep the full original objective and frozen checks/environment/limits. The planner input contains exactly the nine original fixture source files; their bytes and the retained original repository match the manifest.

Milestone checks remain `python -I /acceptance/check.py --project /workspace --phase milestone`; child 2 is bound to the full phase. All acceptance files/fingerprints and both contract hashes match. The first milestone verification records passing milestone checks and offline wheel build/install plus 11 generated tests. No final full acceptance is inferred from those milestone results.

Task 1's accepted candidate `05a300568c6742c59ca01d034f8b55196b3202c7b10557528bbb18df456a0e78`, patch and acceptance artifacts remain intact. The private checkpoint's content and complete mode map match it. Commit `6888fc6cef5f05d04d41c92f032f33d52f385729` binds tree `61b5e416061618ca9533ff47be96046e04b26803`, also saved as task 2's base tree/commit; Git objects were read/decompressed without running candidate code.

This actual handoff exercised nontrivial mode restoration: its pre-restoration fingerprint `c9d6667bf61fbcc4511d0e6b34852e35819d4d5f95fddaf4e71085c8203b3f36` differs from the final restored fingerprint, which exactly equals accepted task 1. The mode-map SHA is `1b86448fe977d83cee38dc722eea909ff0c953cf4822c5769e4f50b4988257af`. Recorded base bytes/tree remain consistent. This is readback of the frozen pending-only restoration receipt and retained checkpoint, not a new execution of restoration.

## Environment and cleanup

Both tasks retain the approved `python-api` receipt `e591c2d6f97b02fc2a99ecef01848a4e74d743e499aeec3b4d4d7d6c6c400acb`: Python3.12.13, FastAPI0.115.12, Pydantic2.13.5, HTTPX0.28.1, Uvicorn0.34.2 and setuptools78.1.0; executor image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`. Bound project-manifest inputs match both retained workspaces. Remote receipts were not re-resolved during this audit.

All 53 creation attestations show the approved nonroot, runc, network-none, readonly-root, cap-drop/no-new-privileges and resource limits, with no devices/GPU requests. Mounts contain only the matching child workspace, read-only approved dependencies, and—in four records—read-only acceptance plus read-only workspace. No credentials, socket, private reference solution or unrelated host path appears.

Both exact workspace labels have final confirmed-absence receipts; no removals were needed, no uncertainty marker remains, and the client group is absent. As in the other arms, per-operation absence is supported by the frozen attestation/fence control flow rather than individually retained daemon replies; final absence is explicit. Two preflight and two cleanup idle observations match the exact approved serving identity, with pair gaps 1.1175s / 1.1174s. No service change or repeated test was performed for this audit.

The failure remains a failure. This accounting PASS establishes preserved limits and evidence, not semantic completion or planning superiority.
