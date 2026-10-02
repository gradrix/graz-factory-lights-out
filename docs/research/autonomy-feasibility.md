# GFLO autonomy: feasible extensions and remaining evidence

Checked: 2026-10-02. Scope: one RTX 5090 with 32 GB VRAM, local inference, one durable factory. Recommendations below are engineering proposals, not implemented capabilities or proof of autonomous software delivery.

## Conclusion

Automatic environment preparation, external progress visibility, web research and headless browser testing are practical extensions of the existing runner. End-to-end autonomous delivery remains an empirical question for the actual local model, task distribution and acceptance process. Build these capabilities around the existing execution loop, then measure whether planning and integration work reliably enough to remove particular human interventions.

The current [architecture](../architecture.md) documents SQLite state, offline Docker execution, independent acceptance checks, bounded repair, and manual patch review. It explicitly defers automatic planning. Preserve that durable core while adding narrow interfaces. Historical architecture and model assumptions should not override the current checkout.

## Small coherent reasoning tasks

Represent each proposed work item with an objective, input artifact revisions, affected interfaces, dependencies, permitted tools, acceptance evidence and resource budget. A task is small enough when its inputs and outcome can be understood and verified together; arbitrary line counts or one-function tasks can hide necessary context.

Use successive bounded roles: clarify requirements, propose acceptance, investigate, plan one increment, implement, review evidence, integrate. Initially these can be serialized calls to one model with separate context, rather than simultaneous resident models. Keep scheduling, permissions, retries and state transitions deterministic. Store explicit assumptions and unresolved questions so later tasks cannot silently promote guesses to facts.

Splitting work does not establish reasoning quality. A controlled study across 180 configurations found that coordination effects depended strongly on task structure, including degradation for sequential planning and error propagation between agents. Its models and benchmarks do not establish outcomes for GFLO's quantized local model. [Primary study](https://arxiv.org/abs/2512.08296).

A reviewer using the same model and evidence can repeat the implementer's misconception; treat independence as something to test. Integration checks and acceptance authored outside the implementation context are necessary. Larger context windows alone do not demonstrate better decomposition, judgment or repair. METR's task horizon measures success at a specified probability against human task duration, not uninterrupted autonomous operating time; frontier results cannot be imported as a local-model guarantee. [METR methodology](https://metr.org/time-horizons/).

## Prepare environments before offline execution

Add an environment preparer with a small request schema: stack, locked dependencies, required tools, browser requirement and resource profile. Prefer a catalog of known templates. It returns an immutable image digest, dependency manifest and smoke-test evidence. Missing dependencies produce a new preparation request and image revision, with a bounded retry budget.

Use a separate preparation boundary with explicit network access. The coding worker receives neither the Docker socket nor build credentials. Docker's daemon API can grant host-level control; rootless Docker reduces daemon/runtime privilege but remains an isolation layer requiring validation on the actual host. [Docker security](https://docs.docker.com/engine/security/), [rootless mode](https://docs.docker.com/engine/security/rootless/).

Pin base image digests and dependency versions/hashes; retain fetched packages and record provenance. Tags can move. A digest freezes image identity but does not make every subsequent build deterministic or install security updates automatically. [Docker build guidance](https://docs.docker.com/build/building/best-practices/#pin-base-image-versions).

After preparation, run the candidate and verifier with no network and no pulling, using the recorded image. `RUN --network=none` isolates that build instruction; it does not prove the whole build avoids registry pulls, remote contexts or other retrieval. A strict offline rebuild needs all inputs already available and network isolation of the build service itself. [Dockerfile network semantics](https://docs.docker.com/reference/dockerfile/#run---network).

Treat package install hooks and generated Dockerfiles as executable code. Start with constrained templates; an arbitrary repository build belongs in an isolated builder with no private mounts. Distinguish reproducible execution from bit-identical image rebuilding and test the property actually promised.

## Browser and research are separate capabilities

**Application testing:** add a browser harness against the candidate in a disposable private network, with no internet route or production credentials. Pin the Playwright package to the matching browser image version and pin that image digest. The image includes browsers and system dependencies, but the Python package must be installed separately. Mismatched versions can prevent browser discovery. [Playwright Docker documentation](https://playwright.dev/python/docs/docker).

**Internet research:** use a distinct browser/fetch service with controlled egress. Playwright warns its standard image is not recommended for untrusted websites; root disables Chromium's sandbox. Non-root execution and its documented seccomp profile are a starting point, not a complete hostile-content boundary. Do not inherit examples granting host IPC or extra administration capabilities without validating the isolation tradeoff. Test sandbox startup and shared-memory needs explicitly. [Playwright container guidance](https://playwright.dev/python/docs/docker).

Research outputs should be bounded text, URLs, timestamps, hashes and optional screenshots. Page content is evidence, never authority to change permissions, reveal secrets or issue unrelated tool calls. Enforce private-address and metadata-endpoint restrictions at the service network boundary, including redirects and DNS changes. Keep browser downloads outside executable workspaces and reset sessions between tasks. A disposable VM is a stronger option when arbitrary hostile browsing is in scope.

Prefer fetching known official documentation first. Add search when source discovery is necessary. Self-hosted SearXNG is a metasearch service, not a local web index: it queries external services. Its documentation explicitly describes upstream CAPTCHA/blocking and an instance limiter; disabling the local limiter does not remove upstream restrictions. [SearXNG overview](https://docs.searxng.org/), [limiter](https://docs.searxng.org/admin/searx.limiter).

Use a bounded search adapter with caching, backoff, per-engine health and explicit partial-result reporting. Enable JSON output deliberately; public instances may disable it. An independently indexed local documentation corpus can work offline but requires refresh/provenance management and cannot discover arbitrary new web pages. [Search API](https://docs.searxng.org/dev/search_api.html). Local inference remains local, but external search queries and page requests still disclose their contents to upstream services; avoid sending private source code as queries.

## External visibility without a fleet platform

Start with versioned events and a read-only local HTTP API over existing state and artifacts. Expose run/task/attempt identifiers, current phase, latest event, heartbeat, budgets, container/model status, acceptance evidence and bounded log tails. A simple page can poll initially; cursor-based streaming can follow when useful. Show completed/planned tasks plus plan revisions, rather than presenting a changing plan as a trustworthy percentage.

Keep the ledger authoritative. Monitoring failure must not corrupt task transitions, and a heartbeat must not be presented as proof of useful progress. Redact secrets, cap logs, show truncation and preserve artifact references. Separate later cancel/resume controls from read-only endpoints and scope them to explicit runs.

OpenTelemetry supplies traces, metrics and logs, not a workflow ledger or dashboard. Map existing run IDs into telemetry correlation fields and optionally export to a local Collector/backend later. Begin with structured events so GFLO need not adopt a distributed monitoring stack merely to observe one runner. [Signals](https://opentelemetry.io/docs/concepts/signals/), [log correlation](https://opentelemetry.io/docs/concepts/signals/logs/).

## Staged falsifiable experiments

These are proposed gates, not measured results. Freeze cases and budgets before trials, retain failures, and report repeated trials separately from distinct tasks.

| Stage | Experiment | Advance only if |
| --- | --- | --- |
| 1: local baseline | Run 12 held-out coherent tasks across fixes, feature increments and refactors on the actual pinned model/runtime. Include ambiguity, incomplete tests and a task requiring refusal/escalation. Record VRAM, tokens, time, repairs, semantic defects and human minutes. | At least 10/12 meet independent acceptance and review within budget; no false claim of success. This is a pilot gate, not statistical proof of reliability. |
| 2: environments | Prepare three representative stacks from empty caches, then execute offline twice. Inject missing dependencies, a moving tag, package-download failure and disk exhaustion. | Every accepted environment is identified by digest and manifest, both offline executions pass, and failures leave no privileged worker access or ambiguous image state. |
| 3: visibility/recovery | Observe from another process; kill the runner/model, reconnect clients, overflow log limits and resume. | The API distinguishes running, stalled and interrupted states within a declared timeout; no duplicate committed transition or misleading accepted status occurs. |
| 4: research/browser | Compare known-doc fetching with search on ten source questions; run five browser journeys. Inject CAPTCHA, redirect to private IP, hostile page instructions and browser version mismatch. | Evidence includes sources, partial failures are explicit, boundary probes fail safely, and all intended journeys produce inspectable results. |
| 5: planning | Compare direct execution against 2–5 generated work items on the same six product changes, with identical total budgets. Hide integration acceptance from implementation. | Decomposition improves accepted outcomes or reduces human effort without increasing missed requirements; otherwise keep it advisory. |
| 6: bounded autonomy | Run one small product increment from written intent through integration and a disposable preview, including cancellation and restart. | Requirements, evidence and artifact revisions reconcile; independent review finds no material omission. Broaden scope only after repeated successes. |

Deployment, credentials and external writes need explicit authority and separate evidence. A successful preview does not establish autonomous production operations. Retain manual semantic review until experiments specifically demonstrate which judgments can be delegated safely.
