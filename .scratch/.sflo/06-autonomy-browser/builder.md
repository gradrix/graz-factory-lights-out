# Local browser builder handoff

## Candidate and scope

Sole maintained builder used s-dev against product baseline972f767 and frozen contract SHA256 `ab3ba1d7aa4d11237de3914f2a1ed40d3dcb47a680ee181465ef8fba6b875f13`. No commits, model calls, rig service/config changes, public browsing or search implementation by builder. Actual execution described below is local Docker. Rig qualification is coordinator/independent-QA owned and pending.

Frozen candidate: `builder-candidate-v2.json`, SHA256 `44e94609e0174950894d2008649fe93a247abf9eacf4f7a3411144b011e9e0c3`. Eight source/test/docs paths are bound. The just-written original `builder-candidate.json`, hash `0d419a0f71c81a9f51ba7d8989284d1d6bbb8d7a0b93cce5ce59f4a20e9d4c95`, is preserved **unaccepted**: it traced only the primary context. No prior evidence is silently relabeled all-context qualification.

Maintained paths:

- `gflo/browser.py`: fixed-profile approval, bounded frozen inputs, approved offline package support, image/platform preflight, one-operation private store, artifact receiver, immutable evidence, offline inspect/recovery.
- `gflo/browser_pair.py`: one guardian for both owned containers, exact app-ID network join, app-death/owner-EOF/deadline supervision, ordered removal and successful daemon absence readback.
- `gflo/recipes/browser/journey.cjs`: fixed sandbox-enabled Chromium launch using actual shared memory; constrained contexts, tracing/screenshots/events, runtime and renderer/network/memory facts, bounded framed output.
- `gflo/recipes/browser/seccomp.json`: byte-identical assessed chroot-only profile, hash322b86b4…; no other relaxation.
- `gflo/__main__.py`: prepare/check/inspect/cleanup CLI, failed-result exit1, no model configuration required.
- `tests/test_browser.py`, `tests/test_browser_live.py`, `docs/local-browser.md`.

BrowserStore has its own small root/lease seam. It does not subclass DocumentStore or expose document operations. Accepted document/package-fetch behavior is unchanged.

## Interfaces

`BrowserStore(root).prepare(archives)` requires approved `playwright.tgz` and `playwright-core.tgz`; mandatory pinned SHA256s and installed Linux/amd64 app/browser image identities are verified. It returns `{id,receipt}` with complete immutable support tree hash and inspected image metadata. Existing installed images are required; no pull/download/package script fallback.

`check({app,checks,seed,case,support}, cancelled=...)` snapshots app/check trees and seed, starts one fresh pair, and returns `{id,receipt}`. The app exports `server.cjs`, binds127.0.0.1:3210 and reads `GFLO_SEED_FILE=/seed.json`. Checks export `async({page,context,request,baseURL,screenshot,newContext})`. `newContext()` is capped at4 including the initial context; concurrent calls reserve slots before asynchronous creation. Checks are controller-reviewed executable assertions, not page/model-granted capabilities.

`receipt.outcome.status` is passed/failed. `receipt.executor.facts.cleanup.confirmed` requires a successful bounded daemon query and no uncertain removal. `receipt.artifacts` binds fixed filenames to exact sizes/hashes. `inspect(id)` is offline and verifies hashes/types. `cleanup()` verifies store labels/IDs, removes browser before app, reads back absence, then removes interrupted staging/fences. Uncertain cleanup retains a fence and bounded private failure diagnostics instead of publishing a result.

## Behavior-first and concrete fixes

The initial public snapshot test failed with a missing browser module, then passed regular-file freezing and link rejection. CLI offline-inspect test failed before registration, then passed without model construction. Fixed transport tests exercise missing/extra/oversized/corrupt output, dimensions and inventory; store tests exercise support/artifact tamper, invalid approval/seed, cancellation before launch, failed commit preserving prior result, uncertain cleanup refusal and explicit recovery.

A bounded-enumeration falsifier exposed scanning beyond the allowed entry count; copying now stops immediately at the budget. Seed/archive reads also use explicit maximum lengths. Root identified inappropriate DocumentStore inheritance; the correction leaves accepted document code untouched.

The first actual launch failed because Node could not resolve sibling playwright-core. Failure receipt `8e619c4546007505289163f48d995bc3aa3d77f81f81d13160420863053307c6` remains under `.gflo/browser-builder`. Adding fixed `NODE_PATH=/support` corrected package resolution without changing sandbox/network policy.

Root identified missing second-context trace evidence. The added actual conflict assertion failed against the original primary-only ZIP. The repair starts/stops tracing on every context. One opaque outer `trace.zip` contains `manifest.json` and `context-1.zip` through `context-4.zip`, within the unchanged16MiB aggregate bound. `outcome.runtime.traces` exposes context index/name/size/hash. Actual conflict test now verifies two nonempty inner traces and finds the second session's `Second` input, `Reserve` selector and `click` actions, using bounded in-memory ZIP inspection without host extraction. Usage docs give deliberate manual viewing steps. Concurrent context-cap negative passes.

## Actual local execution

All five frozen independent public journeys passed locally: create/reload, validation without mutation, edit/cancel, two-context conflict and failed-save explicit retry. First-generation IDs are in `builder-first-journeys.json` plus create/reload `43c4af503561350393b9de3089c8dfbb1b4338e7d4570e91135b3b56208d80f3`. Those original receipts predate the trace repair and remain limited to their recorded trace scope. The maintained live regression suite repeats all five on current source and explicitly checks second-context trace content.

Real-shm launch omits `--disable-dev-shm-usage`, uses `chromiumSandbox:true`, preserves runc/UID1000/capdrop/no-new-privileges/read-only/privateIPC/noGPU and exact images. The first five runs measured `/dev/shm` peaks9,142,272–14,483,456bytes. Runtime capture also records cgroup memory.current/peak/stat/events and renderer process namespaces/seccomp/flags. This is local evidence, not the required independent rig qualification or a general memory-capacity claim.

`builder-local-probes.json` records actual external-navigation/assertion/event-flood/download/file-upload failures and an inert hostile-text positive control; each confirmed no remaining containers. `builder-lifecycle.json` records ownerSIGKILL during startup and artifact finalization, and cancellation during artifact finalization. All observed the intended phase and left no containers. Owner death left private staging/recovery fences, cleared explicitly; cancellation saved a failed receipt only after confirmed cleanup. Artifact-phase delay is an explicitly identified copied-helper fault injection, not normal production latency. Original probe scripts and receipts are retained.

Transport disk accounting: at most24MiB spool +24MiB extracted artifacts +5MiB app/check inputs +64KiB seed/metadata, beneath64MiB reserved headroom. No additional archive-validation spool is created. Fixed package support actually contains18,547,881bytes; preparation uses approved archive bytes in memory, separate from check staging. Container trace temporary storage has independent256MiB tmpfs/1GiB memory limits.

## Gates and remaining checks

- Focused host policy/store tests pass; actual local integration includes five flows, app-death failure, pair cancellation, concurrent context cap and second-context trace assertions.
- Original incomplete coverage gate:82%, preserved in `builder-coverage-initial.log`; missing paired-guardian execution was not accepted.
- Subsequent complete gate before final trace repair:134tests/86%, followed by the135test input-budget gate at86%; these are historical development evidence.
- Final v2 complete `make coverage`: **137tests passed,86% branch-aware coverage,exit0**. Durable output `builder-coverage-candidate-v2.log`. All eight frozen source/test/docs hashes reverified unchanged.
- `git diff --check` passed. Independent functional/security reviewers have the frozen v2 manifest; no source changes planned during review.

Success means frozen executable assertions, complete bounded artifacts and confirmed cleanup. It does not establish arbitrary product coverage, hostile public-browser safety, or local-model web-app implementation skill. Rig five-flow/shared-memory/renderer/lifecycle negatives and independent security acceptance remain pending. The fullStage4 research/search/public-browser gate remains separate. Numeric limits were not relaxed after results.
