# Browser v2 independent security assessment

2026-10-02. Skill: security-check. **Outcome: repair required (B1–B4). Coverage: bounded source review, controlled faults and actual owned local Docker probes completed as described below; target-rig qualification remains separate.** No maintained source edits, model calls, rig operations or shared-service changes were performed.

## Frozen identity and authority

Candidate [builder-candidate-v2.json](builder-candidate-v2.json), SHA-256 **`44e94609e0174950894d2008649fe93a247abf9eacf4f7a3411144b011e9e0c3`**, commit **`c201083`**. Contract SHA-256 `ab3ba1d7aa4d11237de3914f2a1ed40d3dcb47a680ee181465ef8fba6b875f13`. All eight candidate files matched before and after testing; committed bytes independently match the manifest. [Before](security-browser/hashes-before.json), [after](security-browser/hashes-after.json).

I reconstructed `gflo/` from the immutable commit under ignored `.gflo/browser-security-v2/frozen/`. Probes import that source and launch its guardian via explicit `PYTHONPATH`. Trusted parties are controller approval, reviewed checks/helper, prepared support, controller-owned private store and Docker. Application/page content is untrusted. A hostile writer with controller filesystem access and browser/kernel exploitation are outside this assessment. The app and all additional endpoints used below belong to disposable test containers; port3211 is inside the same isolated owned network namespace, never a host service.

## Findings

### B1 — cancellation during final validation can publish a passing result

**Observed, high confidence; acceptance integrity defect.** `BrowserStore.check()` samples cancellation before `_commit()`. That method writes/validates the receipt and syncs staging before its final rename, without another cancellation fence. The controlled `late-cancel` probe makes cancellation become true in `sync_directory()`: the call returns a resolvable **passed** result despite the true cancellation signal. The uncancelled control passes; sync/rename exceptions publish nothing and preserve the prior result.

Evidence: [probe.py](security-browser/probe.py), [fault-results.json](security-browser/fault-results.json), case `late-cancel`. The executor is controlled and the injected sync callback is explicit; this is not an actual filesystem outage. Repair: check cancellation after fallible private preparation and immediately before the publication rename, either refusing publication or preparing an explicitly failed result without reintroducing postcommit I/O.

### B2 — redirects and WebSockets bypass the intended origin policy

**Observed in actual Chromium containers, high confidence; policy enforcement defect.** A page fetches the approved `/redirect` endpoint; its302 leads to `http://127.0.0.1:3211/side`. The side server records the request and the result is **passed**. A direct fetch to that same origin is blocked, leaves zero side hits and records failure. Top-level navigation through the redirect reaches the side server before `framenavigated` detects it and fails the result. Thus the navigation check detects the policy violation after the request rather than preventing it.

A page-created WebSocket to `ws://127.0.0.1:3211/ws` also establishes a connection and produces a **passed** receipt. HTTP route interception does not govern this path. The helper installs neither a separate WebSocket route nor an equivalent policy.

Evidence: [live.py](security-browser/live.py), [live-results.json](security-browser/live-results.json), `direct-cross-origin`, `redirect-fetch`, `redirect-navigation`, `websocket-cross-origin`. Browser console evidence records the independent side-server hit counter through the primary endpoint. The observed redirect behavior is consistent with Playwright's description that the route handler handles the original request while the browser follows redirects. [Official Playwright network documentation](https://playwright.dev/docs/next/network).

The measured impact is access to another endpoint in the disposable app namespace and false policy success. **No host/LAN/public egress was demonstrated**: network-none isolation remains in place. Repair: reject redirects before delivering them to the browser, or validate each bounded redirect hop; explicitly block WebSockets in this initial profile. Keep same-origin positive and blocked-direct controls alongside the two bypass regressions.

### B3 — Docker daemon logs have no configured byte bound

**Source and actual configuration evidence, high confidence; host resource risk.** Both actual containers report `LogConfig: {Type: "json-file", Config: {}}`. Fixed command construction supplies neither a logging driver choice nor rotation limits. The guardian bounds its retained stderr tail to16KiB and stdout spool to approximately24MiB, but these bounds do not constrain the daemon's independent app/browser log files. Docker documents that its default JSON logging has no rotation. [Official Docker logging documentation](https://docs.docker.com/engine/logging/configure/).

Evidence: every actual executor readback in [live-results.json](security-browser/live-results.json), `executor.facts.containers.*.host.LogConfig`; source `BrowserStore.check().command()`. A noisy untrusted app can consume host log disk during its permitted lifetime, outside the64MiB store staging reserve and container tmpfs limits. **No disk-filling test was performed**, and no unbounded elapsed lifetime is claimed. Repair: disable daemon persistence for these attached disposable containers, or provide explicit finite rotation bounds and account for them; verify attached diagnostics still work.

### B4 — timed-out create loses its uncertainty after a current absence query

**Controlled observation plus explicit inference; conservative recovery defect.** Injected `docker create` timeout, followed by both removals reporting `No such container` and a successful empty label query, produces `cleanup.confirmed=true` and exit1. Store code consequently removes its recovery marker and can admit new work. This proves the classification; it does not reproduce an actual delayed daemon operation.

A client timeout does not itself establish that the daemon completed or cancelled creation. A possible later completion would create a dormant owned container after the absence snapshot, without the recovery fence. No late process execution is claimed: the failing create path never proceeds to `docker start`. Repair: preserve an explicit ambiguous-create flag through cleanup and require recovery rather than upgrading that uncertainty to confirmed cleanup solely from a current empty list.

Evidence: [guardian.py](security-browser/guardian.py), [guardian-results.json](security-browser/guardian-results.json), `create-timeout`. Clean control returns0/confirmed; failed absence query and removal errors correctly return125/unconfirmed. **No actual shared-daemon outage was tested.**

## Passing coverage and limits

- **Input/framing:** 23 independent source-seam observations cover normal copy, symlink/hardlink/FIFO/deep-path/byte refusal; complete frame versus extra/truncated/missing/traversal/oversized PNG/oversized metadata;512 versus513 event entries; sync/rename/transport/executor/cleanup failures and prior-good preservation. Synthetic framing controls exercise the documented header/signature checks, not full PNG rendering or ZIP decoding. Trace ZIPs remain opaque on the host.
- **Actual policy controls:** ten fresh owned pairs. Inert hostile instructions remain page data and pass. Direct cross-origin HTTP, target-created popup, data frame, download and file-input interaction produce failed receipts. Calling the replaced `window.open` and catching its exception passes because the popup was prevented. A target popup is detected/closed; this is not proof its initial page never existed. The redirect/WebSocket exceptions are B2.
- **Actual owner death:** independent SIGKILL after first owned object appeared and during a copied-helper artifact barrier. Both phase observations succeeded; successful daemon queries found no remaining owned objects within approximately0.27/0.32seconds after owner kill. Admission stayed fenced; explicit cleanup removed private incomplete staging and retained prepared support. [lifecycle.py](security-browser/lifecycle.py), [lifecycle-results.json](security-browser/lifecycle-results.json). Artifact timing uses a deliberately paused private helper copy; all launch/container boundaries remain the candidate's. This establishes ordinary owner-death cleanup, not daemon-loss cleanup.
- **Sandbox/shared memory:** actual local positive receipt reports Chromium153.0.8010.12, Playwright/core1.63.0, copied seccomp hash `322b86b4f7f5b597ed6a9c2cfd6193a4b249a51c8bc9cfba8ff1a485070b24e8`. Renderer UID1000, effective capabilities0, NoNewPrivs1, seccomp mode2 with two filters versus outer browser one, and separate user/PID/network namespaces. No `--no-sandbox` or `--disable-dev-shm-usage` appeared. Network utility remains `service-sandbox-type=none` under outer container isolation; no claim that every Chromium process has renderer restrictions. Initial positive workload sampled5,324,800 bytes used in private256MiB `/dev/shm` across8samples, cgroup peak176,844,800 bytes under1GiB, no OOM events. These are workload samples, not worst-case bounds or target-rig evidence.
- **Container facts:** exact app-ID namespace join; no external interfaces/routes; gateway/LAN/publicIPv4/IPv6 connection controls return `ENETUNREACH`; fixed runc/nonroot/read-only/cap-drop-ALL/no-new-privileges/private-IPC/resource settings; only frozen RO app/seed or support/check/helper binds; no device requests, GPU, socket, host credentials or host writer mounts. Source retains no weaker sandbox fallback.

Independent functional QA owns five fixture controls/mutants, trace contents, CLI replay and ordinary cancellation. Builder tests and lifecycle reports are supplementary evidence, not counted here as my independent measurements. Original-profile negative, full deadline run, exhaustive output-flood matrix, actual rig five journeys and rig shared-memory adequacy are not newly measured by this report. Current repairs block acceptance regardless of those remaining gates.

## Reproduction and retained failures

Run `python3 .scratch/.sflo/06-autonomy-browser/security-browser/probe.py`, then `guardian.py`, `live.py` or `lifecycle.py` from the same directory path. Scripts reconstruct `c201083` through Git into ignored private storage; live scripts require already installed pinned images and approved local package archives at `.gflo/browser-boundary-prototype/`. They make no image pull or public-document request. Existing result JSON should be copied before rerunning scripts, which overwrite their own result file; live stores enforce normal record limits.

The first live harness attempt accidentally used Node `console.log`, corrupting its own binary stdout framing. Candidate correctly saved a failed artifact result, ID `9789b659d97ed6c7e596b56da4baa416f59440b51774d4cbe4488ed5bed6e0c3`, retained in the private live store. The corrected harness logs inside the page, where bounded events capture it. This harness failure is not a product finding and was not counted as a policy result.

All owned live containers were removed; only controller-owned evidence/store files remain. B1–B4 were sent promptly to coordinator and builder. A repaired candidate requires a new immutable identity and separate recheck; this report remains the v2 record. No universal security certification, public browsing/search acceptance or full Stage4 acceptance is implied.
