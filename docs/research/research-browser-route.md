# Stage 4 research and browser route

Verified 2026-10-02. **Discovery only:** Stage 3 remains the sole active implementation unit. This report neither qualifies a browser sandbox nor accepts Stage 4. Scope follows [the roadmap](../roadmap.md); no packages, images, services, or local SearXNG settings were changed or tested.

## Recommendation: start with one known document

The smallest first vertical slice is **approved official URL → bounded fetch → immutable documentation receipt → cited answer → offline replay**. It can establish evidence and failure semantics before adding search or executable pages. Proposed initial contract:

- Controller approves exact HTTPS origin/path. Use fixed fetch code, no ambient credentials, cookies, project mounts, or browser. Validate DNS/address policy and every redirect; initially refusing redirects is an acceptable narrower contract.
- Initial, unmeasured limits: one document, 2 MiB decoded body, 15-second total deadline, HTML/plain text only, bounded text extraction with no script execution. Oversize, unsupported content, cancellation, and extraction failure produce explicit failure.
- Receipt records requested/final URL, UTC retrieval time, document version, response/cache metadata, raw SHA-256, extracted-text SHA-256, extractor version, and bounded cited excerpts. Preserve provenance separately from model conclusions. Retrieved instructions have no tool authority.
- Offline reads select a receipt explicitly, report retrieval age/version, and never silently fetch. Missing evidence remains missing. Verify one sourced answer online and the same answer from its frozen receipt with networking unavailable; add changed-content, private redirect, oversize, cancellation, and embedded-instruction controls.

For a seed corpus, Python publishes complete HTML and plain-text documentation bundles. The `/3.12/` download page currently identifies **3.12.15**, so that floating URL must not be presented as exact documentation for a different patch release. Begin with individual approved pages; importing ZIP/bzip2 bundles requires its own bounded extraction path. [Python 3.12 downloads](https://docs.python.org/3.12/download.html)

Keep HTTP reuse policy distinct from historical evidence: an HTTP cache must honor `no-store`; stale `must-revalidate` responses cannot be served while disconnected. The receipt should disclose historical retrieval rather than imply current HTTP freshness. Define retention eligibility before storing pages with restrictive directives. [RFC 9111, cache controls and application caches](https://www.rfc-editor.org/rfc/rfc9111.html)

## Browser candidate and supported setup

Current official release is **Playwright 1.63.0**. Proposed first browser target is bundled Chromium only; other engines can follow after the boundary works. [Release 1.63.0](https://github.com/microsoft/playwright/releases/tag/v1.63.0)

| Component | Verified candidate |
| --- | --- |
| Playwright package | `playwright` or `@playwright/test` exactly `1.63.0` |
| Official image | `mcr.microsoft.com/playwright:v1.63.0-noble` (Ubuntu 24.04) |
| Chromium / headless shell | `153.0.8010.12`, revision `1243` |
| Firefox | `155.0`, revision `1543` |
| WebKit, Linux | `26.6`, revision `2359` |

Browser versions/revisions come from the [release-pinned browser manifest](https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json). The image includes browsers and system dependencies, but the Playwright package must be installed separately with a matching version. Acquire and record the architecture-specific image digest and package lock before implementation; this research did not verify a registry digest or local availability. [Official Docker instructions](https://playwright.dev/docs/docker)

The documented Chromium sandbox recipe uses a nonroot user and a seccomp profile allowing user-namespace operations (`clone`, `setns`, `unshare`). Default root execution disables the sandbox. The official image is intended for testing/development and is explicitly not recommended for untrusted websites. Treat arbitrary public browsing as a separate qualification gate. [Docker sandbox guidance](https://playwright.dev/docs/docker), [release-pinned seccomp profile](https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/utils/docker/seccomp_profile.json)

**Explicitly set `chromiumSandbox: true`: its API default is false.** Nonroot plus seccomp is therefore insufficient as a launch specification. [Launch API](https://playwright.dev/docs/api/class-browsertype#browser-type-launch-option-chromium-sandbox)

Proposed GFLO browser contract: nonroot, pinned seccomp, init/reaping, no added broad capabilities, no host IPC, private bounded shared memory, fixed launch arguments, and capped processes/memory/CPU/output/runtime. Measure an adequate private shared-memory size on the actual host. Require observable sandbox startup and fail closed when unavailable; do not retry without sandboxing. These are qualification requirements, not a claim that the proposed combination already works.

Start with a disposable application journey on a private services network. Docker `--internal` still permits communication with the gateway and suitably configured host services, so it does not alone establish “candidate services only.” Verify explicit host/gateway/LAN/Internet denial and permitted application access. [Docker internal-network behavior](https://docs.docker.com/reference/cli/docker/network/create/#network-internal-mode---internal)

Playwright routing misses requests handled by service workers; use `serviceWorkers: 'block'` where request interception is required. Network isolation must enforce the boundary independently of page routing. [BrowserContext routing](https://playwright.dev/docs/api/class-browsercontext#browser-context-route)

Bound and privately retain screenshots/traces. Traces can expose DOM snapshots, source, logs, and network headers/bodies; artifact publication needs a deliberate retention/redaction policy. [Trace Viewer](https://playwright.dev/docs/trace-viewer)

## Bounded search through local SearXNG

Prefer the existing local service after read-only inspection. SearXNG offers GET/POST `/search`; JSON must be enabled in `search.formats`, otherwise that format returns 403. Query text is forwarded to external search services: local hosting does not make upstream queries private. Keep secrets and project source out of queries. [Search API](https://docs.searxng.org/dev/search_api.html)

Proposed controller adapter: at most 512 query characters, one page, ten retained results, 1 MiB response, one concurrent request, 10-second overall deadline, and no automatic retry initially. These are starting budgets to measure, not upstream guarantees. Set server-side `max_page`, disable autocomplete/favicon lookups, and bound upstream timeouts, retries, and redirects; per-engine timeouts can override global settings. [Search settings](https://docs.searxng.org/admin/settings/settings_search.html), [outgoing settings](https://docs.searxng.org/admin/settings/settings_outgoing.html)

Fix a small approved engine set. `disabled: true` only disables an engine by default; `inactive: true` removes it from settings. Reject user-selected engine/bang overrides at the adapter boundary. [Engine settings](https://docs.searxng.org/admin/settings/settings_engines.html)

Preserve partial/blocked/timeout results distinctly from “no evidence found.” Upstream CAPTCHA and blocking remain possible; SearXNG's limiter uses Valkey and does not ensure upstream availability. Inspect endpoint authentication, proxy trust, and limiter policy before enabling automation. [Limiter documentation](https://docs.searxng.org/admin/searx.limiter.html)

For offline search, a small local index over accepted receipts is the simplest initial proposal. SearXNG also supports offline engines without Internet access, but connecting one adds configuration and dependencies; defer until the cache needs it. [Offline engines](https://docs.searxng.org/dev/engines/offline_concept.html)

## Sequence and unresolved prerequisites

1. Finish the current Stage 3 gate. Specify the known-document receipt and implement its fetch/offline replay slice next.
2. Acquire immutable browser/package pins; validate nonroot sandbox startup, private shared memory, network isolation, bounded artifacts, cancellation/owner exit, and version-mismatch refusal on the target host. Then implement one disposable application journey.
3. Inspect the actual local SearXNG version, endpoint/authentication, enabled JSON format, approved engines, and limiter/deadline configuration; implement the bounded search adapter only after these are known.
4. Qualify public-page browsing separately, including redirect/DNS/private-address controls, downloads/CAPTCHA, hostile page instructions, cancellation and cleanup. Preserve the roadmap's full ten-answer/five-journey acceptance gate.

Decisions still needed: first documentation corpus and exact versions; retention/cache policy and extractor format; Python versus Node browser driver; image digest/architecture; enforceable host-network denial; measured resource budgets; and whether public browsing needs a separate service/isolation layer. None were resolved by running infrastructure in this discovery task.
