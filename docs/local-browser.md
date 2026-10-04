# Owned local application checks

`browser` runs a frozen, controller-reviewed Playwright journey against one disposable Node application. It requires no model configuration. This profile supports Node built-ins and `server.cjs`, listening on `127.0.0.1:3210`, with `GET /health` returning success when ready. It does not support public browsing, search, arbitrary application dependencies or production targets.

## Prepare and run

Provision the exact app/browser images before use; execution never pulls images. The trusted recipe binds app image `sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0` and browser image `sha256:2c1f4e0fd6450f43ddb46d60c2a6df30855a8588e165b1f2559fb0eda8d7ff35`. Supply approved offline archives named `playwright.tgz` and `playwright-core.tgz`, exactly version1.63.0. Their mandatory SHA256s are in `gflo/browser.py`; no lifecycle scripts or browser downloads run during preparation.

```sh
python3 -m gflo browser prepare approved-archives/
```

The returned support ID binds the immutable complete package tree. Create an approval JSON:

```json
{
  "app": "candidate/app",
  "checks": "reviewed-checks/create-reload",
  "seed": "reviewed-checks/create-reload/seed.json",
  "case": "create-reload",
  "support": "SUPPORT_SHA256"
}
```

Paths are relative to the invoking controller's working directory. The app receives `GFLO_SEED_FILE=/seed.json`; this file is read-only. Mutable application state belongs under `/tmp`, which is discarded after the run. Files are copied privately and hashed before launch; links, special files, changing inputs and oversized trees are rejected. Caps: app4MiB/256entries, checks1MiB/64entries, seed64KiB.

Each checks directory contains `journey.cjs` exporting one async function:

```js
module.exports = async ({page, context, request, baseURL, screenshot, newContext}) => {
  await page.goto(baseURL);
  // Ordinary Node assertions and Playwright locators establish product behavior.
  require('node:assert/strict').equal(await page.title(), 'Expected title');
  await screenshot();
};
```

`request` is the context HTTP client for independently checking server state. It belongs to trusted reviewed check code, which must use the approved baseURL; page-routing restrictions are not a sandbox for arbitrary Node test code. The network namespace still confines that code to the disposable application. `newContext()` creates another context with the same profile and automatic cleanup (maximum four contexts); `screenshot(otherPage)` captures an optional second page. Check code is reviewed executable code, not untrusted page text. It cannot grant Docker/host capabilities; the controller owns all container options and target topology.

```sh
python3 -m gflo browser check approval.json
python3 -m gflo browser inspect RESULT_SHA256
```

A failed result returns CLI exit1 and a receipt when bounded capture and cleanup complete. Cancellation at the final publication fence refuses the new record; previously completed results remain. An unavailable/uncertain executor cleanup raises an error and retains a recovery fence instead of publishing. Inspection is offline: it verifies hashes without browser/network/model execution. A rerun creates fresh application state, browser contexts and a new result. Screenshots and traces remain private evidence; no HTML report or trace is automatically rendered/extracted. The single opaque `trace.zip` contains `manifest.json` and `context-1.zip` through `context-4.zip`, one Playwright trace for every created context. The16MiB limit applies to the complete outer ZIP. To view one manually: verify the saved receipt first, copy the selected inner ZIP into a disposable offline directory with a trusted archive tool, then open that inner ZIP in the matching Playwright Trace Viewer. Never automatically extract trace members into a project or serve an untrusted report.

## Boundary and limits

The app has a network-none namespace; browser joins that exact owned app container ID. No ports are published. Namespace isolation denies gateway/LAN/Internet access independently of page routing. Page requests outside the fixed origin are aborted. This initial profile refuses every HTTP3xx response, including same-origin redirects, and blocks all WebSockets before a server connection. Readiness also refuses redirects. Redirecting/WebSocket applications are unsupported; there is no fallback. Service workers, accepted downloads, popups and file input interaction are disabled or cause explicit failure. Unexpected frame navigation and browser errors fail the check. Page instructions have no scheduling or tool authority.

Both containers explicitly use `--log-driver none`: Docker does not retain an unbounded daemon json-file log, while attached stdout/stderr still supplies bounded diagnostics. Both containers use runc, UID1000, read-only root, dropped capabilities and no-new-privileges. App:128MiB memory/swap,0.25CPU,64PIDs,16MiB private shm/tmpfs. Browser:1GiB memory/swap,2CPU,256PIDs,256MiB private shm/tmpfs, init, pinned assessed seccomp. Chromium sandboxing is enabled; `--disable-dev-shm-usage` is omitted to use actual shared memory. Runtime receipts include browser/process isolation facts, `/dev/shm` samples and cgroup memory facts. No host IPC, project writer, credentials, socket or GPU devices are mounted.

Work bounds: readiness15s, launch20s, journey60s, finalization15s, overall110s. Actions5s, navigation10s. The pair guardian has a separate130s maximum parent wait for in-flight creation, ordered removal, daemon readback and process exit; bounded reader joins can add10s. It observes owner EOF and app death through browser artifact completion. This is not an unbounded retry loop.

Evidence bounds: eight1280×800 viewport PNGs,2MiB each; one16MiB opaque trace ZIP;512events/256KiB; total24MiB and receipt64KiB. Artifact excess, bad dimensions, missing files or incomplete transport cannot pass. Diagnostics retain a bounded tail. One pair owns the store lease. The512MiB store reserves64MiB staging headroom and refuses new work after16results, without eviction. Transport spool plus extracted artifacts and copied inputs remain below reserved disk headroom; container tmpfs has separate limits.

## Recovery and interpretation

```sh
python3 -m gflo browser cleanup
```

Explicit recovery uses this store's labels and verified IDs, removes browser before app, successfully queries the daemon for absence, then removes unfinished staging and recovery fences. A daemon failure is not proof of absence. A timed-out or failed create without a returned ID is additionally ambiguous: the daemon could create a dormant container after an absence query. Ordinary cleanup retains that fence even when no container is currently listed. After the controller independently confirms the daemon has settled, exceptional recovery is `browser cleanup --acknowledge-create-uncertainty`. An immutable recovery receipt preserves the original failure/guardian evidence and records this operator acknowledgement separately from current absence; it does not claim measured completion of the uncertain create. Previously completed results remain. Publication validates/syncs private staging and ends with atomic rename; no fallible preparation follows commit. Sudden-power-loss durability is not certified.

A pass means the frozen executable assertions passed with complete artifacts and confirmed cleanup. It does not establish that those assertions cover every product requirement. Independent acceptance uses the five public stock-reservation journeys plus negative/lifecycle controls; arbitrary public websites and full research/browser-stage acceptance remain separate.
