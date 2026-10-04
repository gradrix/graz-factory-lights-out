# Arm 2 accounting, plan and handoff readback

**PASS for persisted accounting and execution-boundary evidence.** Arm `2-manifest-reconcile-decomposed`; milestone run `b90b66156d7f`, final run `037a513a8192`; Factory accepted final candidate `f3170468840e203ac45fe8e2f563a736b774ad25794bbca53c41197825f9742a`. This is local read-only review of completed evidence; no candidate execution, rig access or model calls. Independent semantic/test/docs QA remains separate.

[Machine-readable audit and per-call hashes](arm2-accounting.json), [read-only reproduction](arm2-accounting-audit.py). All 361 reviewed files remained byte-identical during the audit.

## Shared pool and observed limit

**36 of 48 requests** share one arm ledger and absolute deadline. Numbers and durable progress reservations are exactly 1–36, with no gap, duplicate or unrecorded request directory. Both children used one Factory attempt, within the fixed three-attempt limit.

| Allocation | Ledger calls |
|---|---|
|Planner / fresh plan review|1 / 2|
|Task 1 implementation / review|3–9 / 10|
|Task 2 implementation / review|11–34 / 35|
|Final original-objective review|36|

The implementation total is 31 calls; there are three code reviews and one each planner/plan review. No question-assessment call occurred. **Task 2 used all 24 worker turns and recorded `Model turn budget exhausted`, `limited:true`.** Subsequent fixed checks and fresh review accepted its candidate. This is recorded as a worker-turn limit reached, not a normal model completion or a request-budget overrun. Task 1 ended normally after seven turns. This accounting does not decide whether the final implementation satisfies every requirement.

All 36 raw request/response pairs are complete, parse to their canonical files and match ledger hashes/usage. HTTP status is 200 throughout with exact captured byte counts. Maximum raw request is 121666 bytes; maximum raw response is 15136 bytes. Every request retains the frozen model, temperature 0, medium reasoning, 4096 output / 1024 thinking caps and enabled thinking. Implementation uses exactly run/check/question tools; planner and reviews are tool-free. Response finish reasons total 30 tool_calls and six stop; the latter include planner/reviewer responses and do not erase task 2's recorded turn exhaustion.

## Reported usage and time

| Metric | Observation |
|---|---:|
|Prompt tokens reported|412232|
|Completion tokens reported|24483|
|Total tokens reported|436715|
|Cached prompt tokens explicitly reported|365905|
|Missing values for these four fields|0 of 36 calls|
|Work / cleanup elapsed|494.7847s / 1.2662s|
|Sum of request elapsed times|474.8027s|
|Request latency minimum / median / maximum|2.1274s / 8.0714s / 56.7189s|

Work and cleanup are within 1800s / 150s. Token totals count repeated conversation requests; cached prompt tokens are a reported subset, not extra tokens added to total. No aggregate token ceiling, missing-token estimate or reasoning-token count is invented. Original per-response timing fields remain available in the JSON.

## Plan authority and original requirements

Saved plan and plan review exactly match charged responses 1 and 2. The second request includes the original public planner input and the exact returned plan. Its decision is pass. The planner input contains all frozen requirements, milestone IDs and exactly the eight original source files, whose content hashes match the fixture manifest.

The plan has exactly two ordered tasks with fixed schema. Task 1 covers A1/A2, task 2 covers A3–A6, and task 2 depends on task 1. No plan field selects checks, environment, packages or budget. Both child contracts retain the complete original objective and controller restrictions before the ordered scope. Task 1's checks are the fixed milestone command; task 2 and final verification use the original full command. Both contracts preserve three attempts, 24 turns and required review. Semantic quality of the proposed split and implemented behavior belongs to QA.

## Exact checkpoint handoff

Task 1's accepted candidate `c92f041bfcb070b1b0e0fc1b70af108ce5ea66e98048da817526912c66849872`, patch hash and accepted artifacts remain intact. Checkpoint content and the full file/directory mode map match that retained workspace exactly, excluding only controller-created Git metadata.

The checkpoint commit is `e8c430e535e36f7d2cb30d7987bec6c9eee25b77`. Its object hash and tree were checked by reading/decompressing Git objects, without invoking project code. The tree equals task 2's saved base tree `55dee6834db84f388691bfdfd1e2c07ecdd037da`; task 2's contract names the same checkpoint commit. The restoration receipt binds the saved base bytes and mode-map SHA `c1cd8aaa215eda39585ed79afaa126f623a2df01eb2958dd9f33cb63c23e6444`.

The recorded task 2 pre-execution fingerprint equals the accepted task 1 fingerprint before and after restoration. In this actual handoff the fingerprint did not change; nontrivial permission restoration was covered by controlled tests, not observed here. The current final workspace has correctly advanced to a different accepted candidate. Both accepted contracts/artifacts and the original eight fixture source files match their saved hashes.

## Environment, executors and idle evidence

Both tasks retain the approved `python-stdlib` environment receipt `36cd138cbdc332246a2db473301200117f82404a4504c675db95966645348975`, Python 3.12.13, and pinned executor image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`. Acceptance bytes/fingerprints match the immutable fixture. Final full acceptance and generated unittest checks exited 0; the latter reports 12 tests. No remote environment was re-resolved during this audit.

All 37 unique creation records show the same approved nonroot/runc/network-none/readonly-root/cap-drop/no-new-privileges limits, no devices/GPU requests, and only the matching child workspace plus read-only approved dependencies. Six include read-only acceptance and read-only workspace. No model key, socket, reference solution or unrelated host mount appears. Final absence receipts cover both exact child workspace labels; client group absence and no uncertainty marker are recorded.

Per-operation daemon absence replies are not individually retained: successful continuation is supported by the frozen creation-attestation/fence control flow. Final absence is explicit. Four serving observations show two fresh idle pairs, separated by 1.1182s and 1.1174s, all with the same approved container/image/start identity and one 98304/Q4/Q4 slot. These observations apply to this completed arm; subsequent arms still require their own fresh observations.

No planning superiority, reliability rate or semantic acceptance is inferred from this accounting PASS.
