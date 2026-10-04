# Protocol-successor trial: independent accounting and lifetime audit

**PASS for recorded accounting, integrity, isolation and lifetime.** All four reviews completed with valid final JSON. The separate [semantic gate fails](qa-trial-final.md): case01 claimed a corrected full-suite execution that did not occur. Structural completion and correct classification labels do not establish truthful evidence claims.

Frozen prototype `847f90e9d4fe515e6c6eada9eb200008b6441fd2`; mechanism SHA256 `c69e90f8359603b9bf6636fa02a6b0887a4ba2af38f9f481243f9c8e831530a8`. Admission SHA256 `a42d57ef6b5e310c1356c8153722b3fc10524ccbfd1e90aa76bca8d38e1e3f7a`. Full artifact manifest SHA256 `46960c632593785cb5e033dec3126d76fc5bc97206adde8c59450161fef52804`.

## Terminal accounting

| Case | Exploration + final requests | Commands | Valid verdict | Work seconds | Cleanup seconds |
|---|---:|---:|---|---:|---:|
| case-01 | 5 + 1 | 7 | repair | 172.890 | 1.346 |
| case-02 | 6 + 1 | 9 | pass | 185.172 | 1.370 |
| case-03 | 4 + 1 | 5 | pass | 127.516 | 1.316 |
| case-04 | 7 + 1 | 12 | repair | 180.707 | 1.423 |

**26 charged requests: 22 exploration and four final; 33 attested commands; zero recovery events.** Every ledger ends in final phase with exactly one durable final reservation. Cases01–03 transitioned after an exploratory no-tool response. Case04 reached seven exploratory requests and twelve commands, then used the reserved eighth request for its final verdict. No ninth request, repeated finalization, additional transport directory or controller retry appears in the reconciled trajectory. Remaining request credits were 2, 1, 3 and 0.

Every final request omits tools/tool_choice and sets `response_format={"type":"json_object"}`. Every final response finishes with `stop`, contains no tool calls and strictly parses to the exact persisted verdict. Exploratory prose was retained only as context. Request/command reservation journals, numbered raw artifacts and ledgers agree. All 26 HTTP captures are complete status200; raw and decoded bodies match and their hashes match the charged ledger.

No response used length recovery, and no partially executed phase-boundary batch occurred in this trial. Those branches remain covered by the separately recorded controlled tests, not falsely claimed as actual trial observations. All proposed tool calls in nonterminal exploration were matched to actual command records, and every following request's history was reconstructed: matching assistant calls, exact bounded tool feedback, original source/system policy and explicit final-phase instruction. No command output replaced controller authority.

## Usage and elapsed time

Explicit recorded usage is **337,752 prompt tokens + 21,212 completion tokens = 358,964 total tokens**, with **223,771 cached prompt tokens** already included in the prompt total. All 26 usage records are present and reconcile; cached tokens are not added twice.

Recorded sums are **666.285 work seconds**, **5.453 cleanup seconds**, **649.434 request elapsed seconds** and **14.497 command elapsed seconds**. These are separate accumulated measurements, not an inferred end-to-end wall duration or generation throughput. Final-request elapsed times were64.649,60.480,43.182 and65.667 seconds. Per-case usage, latency min/median/max, phase totals and input fingerprints are in [trial-accounting.json](trial-accounting.json).

All requests retained flash-next-coder, medium reasoning, temperature0,4096 output tokens and1024 thinking tokens. Maximum raw request/response sizes were71,480/6,673 bytes, below4MiB/1MiB. Each case stayed within eight requests, twelve commands,300workseconds and150cleanupseconds. Case02's185.172seconds of total work includes its separately reserved final phase and does not violate the180-second exploration boundary.

## Execution and lifetime

All33 command records bind the exact requested command to a random start nonce, raw stdout, creation receipt and cleanup receipt. Nonces and hashes match; nonce removal and bounded model-visible feedback were independently reconstructed. All commands have recorded timeouts<=60seconds. No command reports timeout or guardian output limiting. Two actual commands returned nonzero (case01 exit2; case02 exit1); their results remain failed-check evidence. Other command exits were zero, which alone does not prove every narrated test passed.

Every creation receipt has the pinned image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, nonroot1000:1000, runc, networknone, read-only root, cap-dropALL, no-new-privileges,1GiB memory/swap,2CPU,128PIDs,16MiB shared memory and128MiB temporary space. Exactly two read-only bind mounts expose only that case's `/candidate` and the approved stdlib `/opt/deps`. No host workspace, credential, socket or GPU/device mount appears. Arguments specify log-driver none; that is recorded argument evidence, not an independent LogConfig query.

All source file sets, bytes, recorded modes and downloaded modes match the unchanged public fixture, including each full objective hash. Source and tool output remain data in the reconstructed conversation. All four parent results affirm client process-group absence, command cleanup and fresh idle. Every command has exact-name confirmed absence, with no retained uncertainty fence.

All16 serving observations match the admitted container/image/start identity, single idle slot,98304 context andQ4 cache profile. Each preflight/final pair is separated by at least one second. No serving restart or identity change is recorded. Cleanup was1.316–1.423seconds per case within its shared allowance.

## Reproduction and boundaries

[Read-only script](trial-accounting.py): `python3 .scratch/.sflo/09-autonomy-executable-review-protocol/trial-accounting.py`. It independently verifies all **406 manifest entries**, the exact included file set, unchanged before/after artifacts, root/per-case result equality, admitted gate hashes and all37 bound source/assets. Raw data resides in `.gflo/executable-review-protocol-trial-1/`. The script was prepared before terminal downloads; execution began only after coordinator authorization. One initial metadata-path mismatch in the audit script was corrected to read the rig output root from the process receipt; this was an audit adaptation, not a product failure or rerun of the experiment.

This assessment uses persisted receipts and the frozen trusted-controller implementation. It performs no rig/model calls, candidate execution, live daemon checks or packet capture. It establishes no extra calls within this admitted controller trajectory, not absence of unrelated serving clients. Recovery/time-boundary behavior is not newly validated by a trial that did not exercise it. The initial failed trial remains separate and unchanged. This accounting pass cannot override the successor's failed truthful-evidence gate or authorize another trial or maintained promotion.
