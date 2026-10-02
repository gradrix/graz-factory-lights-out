# Proposed next unit: supervised owned-local-application journeys

2026-10-02. **Design only; activation follows document acceptance and a separately frozen browser contract.** This proposal reads existing prototype artifacts, reports and roadmap. It performs no runtime, test, model, browser or prototype execution and changes no maintained source.

## Smallest useful capability

Run one controller-approved browser journey against one disposable owned application, retain bounded screenshots/trace/failure facts, and terminate both processes on completion, cancellation or owner loss. Use a fresh application and browser context for each journey. Start with one CommonJS Node application profile using the already tested app image and a fixed `node server.cjs` entry point. No multi-service topology, arbitrary Docker options, browser agent loop, new scheduler or role hierarchy.

Suggested public seam:

```text
browser check APPROVED_REQUEST.json  -> immutable result ID, pass/fail and evidence
browser inspect RESULT_ID           -> offline verified receipt/artifact inventory
browser cleanup STORE               -> explicit recovery of owned interrupted work
```

The approved request binds a clean immutable application snapshot, exact application image, controller-reviewed journey bundle hash, fixture seed hash, case ID and fixed profile/budgets. Paths are inputs to the controller, not page/model output. The app gets only its frozen application files and bounded ephemeral state; the browser gets only pinned Playwright, the approved test bundle and fixed helper. Neither gets factory credentials, model keys, Docker socket, GPU devices, a writable project tree or authority to choose another target. Initial service address is fixed `http://127.0.0.1:3210`; readiness is bounded and distinct from journey success.

Use ordinary Playwright assertions in the frozen journey bundle rather than inventing a browser-action language. A generated test is a proposed check: the qualification oracle and acceptance criteria remain independently authored. This seam can later be called by the existing verification path, but the first unit should prove the explicit CLI path before adding automatic dispatch. No inference is needed to operate a frozen journey.

## Preserve the demonstrated boundary

Create the app with `--network none`, binding loopback. Create the browser with `--network container:<exact owned app ID>`. The existing prototype observed only loopback, no IPv4 route, app access and denied gateway/LAN/publicIPv4/publicIPv6 connections. Do not replace this with an internal bridge. Publish no ports. Block service workers; disallow unexpected popups, external navigation, downloads and file uploads in this initial profile. Network isolation remains authoritative even if routing hooks are bypassed. Local redirects may be exercised, but cannot introduce another approved origin.

Retain explicit runc, nonroot UID1000, read-only root, dropped capabilities, no-new-privileges, private IPC/init and `chromiumSandbox:true`. Fail closed on missing/mismatched pins or sandbox startup; no `--no-sandbox`, added capability, profile relaxation, package download or image-pull fallback. Controller approval covers this owned disposable app only. Page text cannot alter tests, launch options, budgets or retention.

### Exact previously tested pins

These are historical measurements from the preserved rig prototype, not a claim of current availability or a new execution result.

| Item | Tested identity |
| --- | --- |
| Playwright image index | `sha256:eff16c30e6f3f4af0a03fa4b706120d5e9b0891c344a27d64559aff5900a4a27` |
| Linux amd64 browser manifest | `sha256:bc6ab0d6d44ff4826e4cb8c1e6d801e185bfc42bb0753f8e2a30efc70db054c7` |
| Actual browser image ID | `sha256:2c1f4e0fd6450f43ddb46d60c2a6df30855a8588e165b1f2559fb0eda8d7ff35` |
| App image ID | `sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0` |
| Playwright / playwright-core | Both `1.63.0` |
| Playwright tarball SHA256 | `195a5ee9bfed7c6e9c03965950e32e5e4dbedaa02e740e5a530eb4b87dae050c` |
| Core tarball SHA256 | `208593d4e1bcd8f8fe5f869cad1cc332dc7f1d70dc1d58c102dc3ac36e30f26c` |
| Browser-container Node | `v24.20.0` |
| Chromium headless shell | `153.0.8010.12`, revision `1243` |
| Official seccomp SHA256 | `cc3e61cabda6bbc1e53e54d27ba4d55a9d3be829b6dd1a596f4a7b31b1cc7849` |
| Tested local chroot-only profile SHA256 | `322b86b4f7f5b597ed6a9c2cfd6193a4b249a51c8bc9cfba8ff1a485070b24e8` |

The package SHA512 integrity strings are preserved in the prototype receipt; freeze both package integrity and tree identity when preparing the maintained profile. The Node version above belongs to the browser reporter, not an independently measured app Node version. Read back both actual runtimes during qualification.

The profile change removes the outer-capability condition from only the `chroot` allow rule. It permits that syscall for every process under the profile, subject to kernel namespace privilege checks; it is not Chromium-only or path-specific. Independent assessment supported this bounded experiment. Existing renderer evidence shows separate user/PID/network namespaces, zero effective capabilities and one extra seccomp filter. It does not establish identical isolation for the network utility or software GPU process.

## Five meaningful application journeys

Use one small owned stock-reservation application with a browser UI, HTTP domain API and ephemeral server-side state. Seed each case independently. Freeze public behavior and external assertions before implementation/model exposure. Each journey asserts final visible state plus an independent HTTP state read where relevant, with a screenshot and trace.

| Journey | User behavior and independent acceptance | Defect it should reject |
| --- | --- | --- |
| Create and reload | Reserve2 of5 units with a customer reference; see remaining3 and one reservation; reload and see the same server state. | UI-only optimistic success, lost persistence, duplicate submit. |
| Validation without mutation | Submit blank reference, fractional quantity, zero and overstock; accessible field errors explain each; valid submission then works; stock/reservation state is unchanged by every invalid attempt. | Coercive types, hidden state mutation, a form permanently disabled after error. |
| Edit and cancel | Change an existing reservation from2 to3; verify only the delta is consumed; cancel through confirmation and restore all5 units; cancelled record disappears from active list. | Double subtraction, stale detail/list state, wrong stock restoration. |
| Conflicting browser sessions | Two contexts load stock2; each attempts to reserve2. Exactly one succeeds; the other receives a clear conflict and refreshes to0 remaining; exactly one reservation exists. | Stale optimistic concurrency, negative stock, two successful claims for one item. |
| Recovery from failed save | A frozen app fault mode returns one503 before mutation. UI reports failure and retains entered fields; explicit retry creates exactly one reservation; keyboard navigation reaches form errors, retry and success. | False success on server failure, unintended automatic duplicate retry, unrecoverable UI state. |

This is five coherent flows, not five repetitions of the prototype counter. It qualifies a bounded application class, not arbitrary web products or complete accessibility. Seed/fault setup is controller-owned and isolated from production; fault injection is labeled in receipts. Known-good control must pass all five; focused mutants must fail the relevant independent assertion. A screenshot alone never establishes behavior.

## Bounds to freeze before implementation

Start from measured container settings: browser1GiB memory/swap,2CPUs,256PIDs, private256MiB shm and256MiB temporary storage; app128MiB memory,0.25CPU,64PIDs,private16MiB shm. Prototype app swap limit was256MiB; specify it explicitly rather than claiming memory=swap128MiB was tested. App mutable state should receive a separate bounded tmpfs; its size is a new proposed value to freeze.

Proposed new limits, **not measured capacities**: one concurrent app/browser pair;15s readiness,20s browser launch,60s journey,15s artifact finalization, then a separate bounded cleanup allowance covering both containers. Per-action5s, navigation10s, maximum20asserted/action steps per journey. Browser-wide total work ceiling110s. Reuse existing guardian mechanics only after verifying ownership of the pair and exact cleanup deadlines; do not copy prototype shell traps that swallow cleanup errors.

Proposed artifacts: maximum8 viewport PNGs at fixed1280×800,2MiB each; one trace up to16MiB; console/request/page-error events up to512 entries/256KiB; total run artifacts24MiB and one receipt64KiB. Larger artifacts fail evidence completeness, not silently pass after truncation. Record bounded diagnostic truncation separately. No video, downloads or full response-body archive in this first profile. Keep trace/screenshot private; use synthetic data and no secrets. Trace ZIP is opaque downloadable evidence, never automatically extracted into the host or rendered from an untrusted HTML report.

Artifact generation stays in bounded container temporary storage. A fixed trusted collection step exports only the finite named result files through a bounded transport into private staging; reject extra paths, links, special files, declared oversize or incomplete transport. It must finish before container teardown. Do not let the browser write an arbitrary host directory. Failed/incomplete capture produces a failure receipt with missing-artifact reasons; it cannot satisfy the screenshot/trace success gate.

The prototype used `--disable-dev-shm-usage`, so its private shm allocation does **not** prove shared-memory adequacy. The new contract must explicitly choose either a separately qualified launch omitting that default flag and measure `/dev/shm`, or report the retained `/tmp` behavior and leave the roadmap's shared-memory requirement pending. Do not silently alter launch arguments or claim the existing counter measurement satisfies realistic sizing.

## Lifecycle, evidence and acceptance

One owner supervises both containers by fresh names/labels and recorded IDs. Install an in-flight recovery fence before launching either. On every terminal path remove browser first, then app, and independently confirm absence. Owner EOF, SIGKILL, partial startup, app death, hung navigation, memory/PID exhaustion, cancellation during trace capture and cleanup timeout need actual local and rig fault checks. If cleanup cannot be established, retain an explicit recovery fence and failure; never promote a pass or reuse that run. Recovery removes only the recorded owned pair and unfinished staging.

Receipt binds application snapshot, journey/fixture/profile/helper/package hashes, actual image/runtime/browser identities, complete launch settings, UTC phase timing, readiness, per-step assertion outcomes, browser/console/network errors, artifact hashes/sizes, terminal reason and cleanup readback. Save the frozen test source and report alongside artifacts. Distinguish startup failure, assertion failure, app failure, deadline/cancel, artifact failure and cleanup uncertainty. Publish only after cleanup, validated output and staged metadata are ready; commit once, with no fallible postcommit preparation. Offline inspect verifies hashes and never reruns a journey. A rerun gets a new identity.

Additional qualification controls: version mismatch; original seccomp startup rejection; attempted external/private redirect; hostile page instructions; denied download/file chooser; log/artifact flooding; corrupted artifact hash; out-of-bounds collection; owner death at each startup/publication boundary; prior valid result surviving failed new publication. Preserve failures and inputs. The five successful flows, negative controls, renderer/network facts, bounded artifacts and measured memory behavior all belong to independent QA/security acceptance, not the builder's self-report.

## Decision and remaining boundary

Recommend this as the next cohesive unit after document acceptance, with the shared-memory choice resolved in its frozen contract. The read-only prototype/report are sufficient design inputs but not product acceptance. Public browsing, search, CAPTCHA handling, remote downloads, upstream query disclosure, ten-document research acceptance and broader Stage4 completion remain separate. No inference, public browsing permission or production-write authorization follows from this proposal.

Sources inspected: `browser-boundary-prototype.md`; prototype `receipt.json`, `run-chroot.sh`, `probe.cjs`, `app.cjs`; `browser-boundary-prototype/security-assessment.md`; `issues/06-local-browser-boundary.md`; repository `docs/roadmap.md` and `docs/research/research-browser-route.md`.
