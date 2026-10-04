# Browser security repair v3

Original v2 source remains preserved at commit `c201083`; independent report/probes under `security-browser/` and original manifests are unchanged. This is the sole builder repair of SEC-B1 through SEC-B4, with no rig/model calls, service changes or commits.

Frozen v3 manifest: `builder-candidate-v3.json`, SHA256 `bbcd59aa9ba4223a022eb0c7d0915188b530b5a35308897384d3594fdfa04da3`. Nine maintained source/test/docs paths are bound, including the new `tests/test_browser_pair.py`. Lineage names v2 manifest `44e94609e0174950894d2008649fe93a247abf9eacf4f7a3411144b011e9e0c3` and source commit. Original contract budgets/pins unchanged; coordinator explicitly chose all-redirect/all-WebSocket refusal and exceptional operator acknowledgement for daemon uncertainty. The contract did not promise same-origin redirect support.

## SEC-B1 — final cancellation fence

A regression flips cancellation inside final staging-directory sync. It failed on v2 because a passed receipt still became visible. `_commit` now checks cancellation after private validation/sync and the destination check, immediately before atomic rename. Late cancellation refuses publication, removes private staging through the existing failure path and preserves earlier records. No postcommit fallible preparation was added. Actual pair-cancellation integration now verifies explicit refusal and zero remaining containers instead of expecting a newly saved cancelled record.

## SEC-B2 — origin redirects and WebSockets

The actual owned3211 control reproduced the escape: a redirected fetch and WebSocket reached a second loopback origin inside the disposable app namespace. This was not host/Internet egress. Test assertions include a server-side hit list, so a generic later failure cannot hide forbidden contact.

The page route handler now fetches exactly one response with `maxRedirects:0`, `maxRetries:0`, a10s timeout and explicitly disposes it. Every3xx response is refused before the browser can follow a target; direct exact-origin responses are fulfilled. All WebSockets are intercepted and closed without connecting to a server. Node readiness fetch uses `redirect:'error'`, closing the earlier pre-page-policy path. Same-origin redirects and WebSocket applications are explicitly unsupported by this first profile.

Actual local controls pass: direct approved HTTP succeeds; redirected fetch, redirected navigation, same-origin redirect and WebSocket cases fail with zero side-origin hits. The five independent business journeys remain exercised by the live suite. The health-redirect regression separately requires readiness failure and absence of an app-emitted side-contact diagnostic. Trusted reviewed Node checks and their `request` client are distinct authority from page code; this distinction is documented rather than presenting routing as a sandbox for arbitrary test JavaScript.

## SEC-B3 — daemon log storage

The fixed app and browser commands now specify `--log-driver none`. Host tests first failed when that option was absent. Actual local origin tests inspect both containers' `HostConfig.LogConfig.Type == 'none'` and verify that an attached browser diagnostic still reaches the bounded controller tail. Docker daemon json-file persistence is disabled, rather than assuming the parent tail bounded daemon storage. No disk-filling probe was performed.

## SEC-B4 — unresolved creation and exceptional recovery

A controlled guardian probe reproduced `docker create` timeout followed by `No such container` removal and a successful empty list. V2 incorrectly reported cleanup confirmed. The repair tracks unresolved create operations separately when a client transport/subprocess failure, nonzero result or malformed response provides no conclusive container ID. Current absence never clears this uncertainty. The fact is persisted in `cleanup.uncertain_creates`; Store retains the recovery fence and original diagnostics and refuses publication.

This is a simulated daemon-completion ambiguity, not an observed daemon failure or demonstrated late-running process. An eventual late create could leave a dormant container/allocation; no start follows the failed create path.

Ordinary explicit cleanup can remove currently owned resources but refuses to clear uncertain-creation fences. Coordinator authorized `cleanup --acknowledge-create-uncertainty` only after the controller independently establishes the daemon has settled. An immutable recovery receipt preserves original failure/fence/available guardian evidence, source hashes and the operator acknowledgement. Its current-absence readback explicitly says it is **not proof of create completion**. The acknowledgement record is durable before deletion of the old recovery files; it is an audit of that acknowledgement/readback, not a claim that all later cleanup operations necessarily succeeded. A failed cleanup retains the fence for retry. The regression verifies ordinary refusal, durable original-failure preservation, explicit acknowledgement and subsequent permitted work.

## Verification and scope

- B1, B3 and B4 have preserved red outcomes followed by focused green checks. B2 has actual local owned-origin countercontrols before and after repair.
- Focused host/store plus controlled guardian tests:20passed (17host,3guardian).
- Actual local live suite before the added health case:4tests passed in19.406s, covering five business journeys, second-context trace contents, concurrent context cap, app death, cancellation, and the origin/logging matrix. Durable log: `builder-security-repair-live.log`. Temporary integration stores were removed by test teardown; v2 independent raw evidence remains intact.
- Full v3 `make coverage` (including health redirect): **144tests passed,86% branch-aware coverage,exit0**. Durable log: `builder-coverage-v3.log`. All nine frozen hashes reverified unchanged; coordinator preserved source at91b1e76.
- `git diff --check` passed. Frozen manifest sent to the original independent security reviewer and coordinator; no further source mutations planned during review.

Rig requalification and independent acceptance remain coordinator/reviewer owned. No fullStage4/public-browser/search acceptance is implied. The browser/container package pins, resource/artifact budgets and five frozen application fixtures were not relaxed or changed.
