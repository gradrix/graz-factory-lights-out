# Toward an autonomous local factory

Status: proposed implementation stages, accepted destination. Updated 2026-10-02.

## Destination and feasibility

A person provides a product brief, constraints, access and an execution budget. GFLO turns that into accepted requirements, prepared environments, a work plan, changes, independent checks, repairs, integration and a reproducible release. A preauthorized target can also receive a tested deployment with rollback. Unresolved product choices and exhausted recovery produce an explicit stop with evidence.

**The engineering route is feasible. Reliable end-to-end delivery by the actual local models is not yet demonstrated.** The current first version proves bounded execution, repair and recovery. Its pilot also proved that passing tests can miss real defects and unnecessary code. The [research](research/autonomy-feasibility.md) supports the tool choices and identifies the remaining experiments.

All reasoning stays on local models. Prepared coding and verification can run offline. Acquiring dependencies, searching the live web and browsing external sites require a network; offline operation uses cached environments and documentation. Local inference does not make an upstream search engine or website locally available.

## Build from the existing core

Keep one application and durable task state. Add one evidenced capability at a time through the runner, worker and verification interfaces. Start with one active GPU inference request. Browser execution, builds and tests use CPU/RAM and need measured admission limits because model lookup data already uses host memory.

```text
brief + policy
      ↓
requirements and acceptance proposal
      ↓
work plan → prepared environment
      ↓
ready task → implementation → executable checks + separate review
                 ↑                          │
                 └──── bounded repair ─────┘
                                            ↓
                             integration → product journey
                                            ↓
                                release / authorized deployment

Durable events, artifacts and progress describe every transition.
```

The controller owns scheduling, permissions, budgets and state transitions. Model output is a proposal or artifact. It cannot grant capabilities, relax acceptance or silently turn a failed check into a pass. A reviewer can request repair; positive model judgment alone cannot establish executable correctness.

## Small reasoning tasks ("brain atoms")

Use coherent assignments such as “find the cause of duplicate reservations,” “implement the approved reservation contract,” or “review this patch against these requirements.” A task should fit one understandable purpose and one verifiable result. Do not split by a fixed number of lines or force every function into a separate agent.

Each task needs:

- Objective and explicit completion criteria.
- Pinned input revisions, relevant interfaces and dependencies.
- Expected output: findings, a plan, a patch, tests or an environment request.
- Permitted tools and an execution/recovery budget.
- Evidence references and a clear failure/escalation result.

These are extensions of the current task record as their stages need them, not a new schema/framework to implement all at once. Each assignment gets fresh role context plus referenced project facts. Shared durable state stores requirements, decisions and evidence; conversations are not the project memory.

Start qualification around coherent tasks whose useful context is roughly 8K–32K tokens, an agent-chosen experiment range rather than a hard product limit. Expand when evidence requires more surrounding code. The installed 128K capacity is available, but maximum context is not the default amount to fill. Measure correctness, useful progress, latency and context omissions. Task size can grow when reliable completion improves.

Use Flash Coder for the first implementation trials. Compare fresh-context Flash review against tuned dense Qwen on the same known-defect and clean patches before choosing a reviewer. Bonsai is a candidate for document processing after its tool-loop behavior is qualified. Model switching is explicit and serialized on this GPU; several resident models are not assumed to fit.

## Stages and acceptance

All thresholds below are proposed qualification gates, not measured success rates or user-imposed guarantees. Freeze cases and budgets before running; keep failures and distinguish held-out tasks from repeated trials. Passing a small suite permits the next bounded experiment, not a claim of universal reliability.

### 1. Visibility and controlled operation

**Deliver:** durable structured events, run/task/attempt IDs, timestamps, phase, last useful action, heartbeat and model/container state. Add `watch` and a read-only HTTP view with a simple browser page. Start with polling; add streaming only when it earns its cost. Expose through loopback/SSH initially, or authenticated private-network access. Keep logs bounded and redact credentials.

**Accept:** a second client can observe three runs and reconnect after process death without inventing progress. A model stall is distinguishable from a completed or interrupted task. Cancellation/resume initially remain explicit CLI controls, separate from the read-only HTTP view; they target one run and leave no orphan writer. The UI links to patches and check evidence and does not call a changing task plan “80% complete” without explaining its denominator.

Dependency: current core. First implementation frontier.

### 2. Independent local review and honest acceptance

**Deliver:** a fresh-context, read-only review assignment covering requirement omissions, incorrect assumptions, test adequacy and unjustified complexity. Findings carry source locations, evidence, severity and a requested repair. The controller reconciles findings with executable checks and records review → repair → recheck. Freeze requirements outside the coder context; generated tests supplement independent acceptance.

**Accept:** on a frozen set of ten known-defect patches and ten clean controls, catch every seeded critical defect, catch at least eight defect cases overall, and falsely block no more than two clean controls. Then complete at least ten of twelve held-out bounded coding tasks within a fixed budget, with no outcome labeled successful when independent evaluation finds a critical missed requirement. A separate ambiguous task must stop with a useful question instead of inventing a product decision. These small gates do not prove low production failure rates.

Compare Flash and dense Qwen reviewers under equal wall-time budgets; account for switching cost and correlated mistakes. Track accepted changes, rework, false acceptance/rejection and human minutes, not token speed alone. Keep manual semantic evaluation during qualification.

Dependency: stage 1 evidence. Automatic integration remains gated until this stage has useful evidence.

### 3. Automatic environment preparation

**Deliver:** a trusted environment preparer taking a constrained stack/dependency/tool request and returning a receipt binding an immutable base image, hashed read-only dependency snapshot, lock/manifest and smoke-test evidence. Begin with Python stdlib, packaged Python service and Node/TypeScript profiles. Infer proposals from repository manifests; use approved profile recipes. The [snapshot decision](decisions/architecture/004-environment-snapshots.md) refines the initial baked-image proposal. Separate network-enabled build/fetch from offline worker execution.

**Accept:** prepare each profile from cold package caches and no existing profile snapshot, explicitly record shared base images and all inputs, and run its checks offline twice with no pulls or package downloads. Missing packages, unavailable registries, invalid locks, resource exhaustion and cancellation must produce bounded actionable failures. The coding worker never gains the Docker socket, host credentials or build secrets. Retain known-good image revisions; rebuilding and bit-identical output are distinct claims.

Dependency: stage 1 lifecycle; stage 2 reviews proposed environment changes. Broader language support is added through a working profile and its real scenario, not a capability label.

### 4. Research and browser tools

**Deliver:** separate capabilities for known-document fetch, search and public-page browsing. Prefer official documentation URLs, then search when discovery is needed. Store URL, retrieval time, content hash, excerpts and cited findings. A local SearXNG instance is one search candidate; it still depends on upstream engines and may receive blocks or partial results.

Add Playwright for application journeys, screenshots, console/network failures and trace artifacts. Use a matching pinned Playwright/browser image. Application tests use a private network containing only disposable candidate services. Internet browsing uses a separate restricted service/session with no project secrets or writable code mount. Require non-root execution, a validated browser sandbox/seccomp configuration and measured shared-memory limits; use stronger isolation if arbitrary hostile browsing exceeds that boundary.

**Accept:** ten research questions with source-backed answers and explicit failures for unavailable sources; five application journeys with screenshots/traces and independently asserted behavior. Exercise redirects to private addresses, hostile page instructions, CAPTCHA, broken downloads, browser/package version mismatch, failed sandbox startup and cancellation. Retrieved text cannot authorize tool actions. A research outage cannot silently become “no evidence of a problem.”

Dependency: stage 3 environments and stage 1 visibility. Search queries may disclose their text upstream; private code stays out of them. Offline mode uses a pinned documentation cache and reports its age.

### 5. Planning, delegation and integration

**Deliver:** a planner proposes two to five dependent tasks for one product increment. Separate acceptance proposal/review from implementation. Persist the approved plan before dispatch. The controller schedules ready tasks, owns repair limits and integrates candidates against the expected base revision. Replanning creates a new plan revision and preserves completed evidence.

**Accept:** compare direct execution and decomposed execution on six unseen multi-file changes with equal total budgets. Decomposition must improve accepted outcomes or reduce human effort without increasing missed requirements. Inject stale inputs, conflicting changes, a bad dependency, cancellation and a passing-unit/failing-integration case. Failed integration returns concrete evidence to the responsible task. Repeated identical failures stop within budget.

Dependency: stages 2–4 where the project needs those tools. If decomposition does not help, keep planning advisory and adjust the task boundary rather than increasing agent count.

### 6. Bounded end-to-end delivery

**Deliver:** brief → accepted requirements → environment → plan → implementation/review → integration → full product journey → versioned release and local preview. Supported deployment profiles can promote to a preauthorized target after readiness checks, with rollback on failure. Record the source/image/version actually running.

**Accept:** three different small projects—CLI/data tool, API with persistent storage, and browser-facing application—each complete in three separate runs without routine human intervention after the brief/policy is frozen. The nine runs must meet independent product acceptance, preserve evidence and recover from an injected interruption. Failed readiness must roll back the tested disposable target. Report escalated/failed runs, elapsed time, human intervention and regressions, including zero-success cases.

Only then trial bounded changes in a larger unfamiliar repository. Expand supported project classes and permitted deployment actions individually. A successful local preview does not qualify autonomous production operations or arbitrary business decisions.

Dependency: prior applicable stages. The exact production target, credentials and external-write policy are task-specific inputs, not blanket permission inferred from this roadmap.

## What "predictable" means

The system should expose its state, terminate within declared budgets, retain results, recover without repeating committed side effects, and refuse to label unverified work successful. Model success itself is probabilistic. An honest stopped run can be correct operation, but it is not counted as successful autonomous delivery.

No automatic self-modification of the factory, GPU fleet orchestration, paid/cloud LLM fallback or manager/CEO hierarchy is required for this route. Add specialist assignments when a measured failure shows their value. SFLO/Gas City remain inspirations for evidence-bearing stages and durable work; current primary-source guidance is in the research document.

## Ownership and next action

The user chose the autonomy destination, local inference, deletion/publication and requested capabilities. The agent proposes the stage order, initial stack profiles and numeric trial gates. The [decision map](../.scratch/autonomy/map.md) records unresolved questions; the [delivery map](../.scratch/autonomy/delivery.md) tracks the next executable unit. User authorized incremental implementation on 2026-10-02, with acceptance between stages and real 5090 trials. Current execution starts with stage 1; progress and evidence live in the delivery map.
