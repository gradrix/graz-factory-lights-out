# Choose the durable orchestration architecture

Type: grilling
Status: resolved
Assignee: codex
Blocked by: 01, 02, 03

## Question

What durable state machine, scheduler, artifact protocol, isolation model, and concurrency policy should coordinate Work atoms while remaining understandable, restartable, locally operable, and independent of any one agent harness?

## Comments

## Answer

### Resolution — 2026-09-02

GFLO will implement an independent, model-agnostic orchestration architecture designed specifically for small-context, comparatively weak local models. SFLO and Gas City are evidence-bearing design references, not dependencies, fallback runtimes, compatibility targets, or adapters. GFLO may reproduce useful semantics in its own domain model, but it owns its interfaces, implementation, persistence, and evolution.

The durable architecture is:

1. **One authority.** The Work ledger is the only authority for run, Graph revision, Work atom, Attempt, Lease, evidence-reference, gate, and acceptance state. Git state, worker conversations, sandboxes, model text, and reports are observations or artifacts; none may transition durable state directly.
2. **Reconciliation, not a scripted pipeline.** A persistent Orchestrator compares desired graph state with observed leases, workers, workspaces, artifacts, and validators, then performs the smallest admissible transition. Restarting the Orchestrator reconstructs work from the ledger and observation; in-memory sessions are disposable.
3. **Explicit lifecycle.** Work atoms move through `planned`, `ready`, `leased`, `running`, `validating`, and `accepted`, with `retry-ready`, `quarantined`, `superseded`, and `cancelled` terminal or recovery paths. Attempts are append-only; retry never reopens or rewrites an Attempt.
4. **At-least-once Attempts, exactly-once acceptance.** The architecture assumes a worker can perform side effects and crash before acknowledgement. Leases, idempotency keys, isolated workspaces, and reconciliation tolerate repeated Attempt execution. The ledger permits only one accepted result and one integration transition for the applicable Work-atom/Graph-revision preconditions.
5. **Dependency-aware scheduling.** Readiness comes from resolved dependency edges, then Capability-profile compatibility, priority, and age. The initial scheduler exposes one global inference admission token for Qwen while allowing bounded CPU-side indexing, workspace preparation, and deterministic validation in parallel. Concurrent writers may not target the same Product module; composition occurs through explicit Integration atoms.
6. **Disposable Attempt workers.** Each Attempt receives an immutable Context manifest plus a fresh isolated checkout/worktree and sandbox. It cannot write the canonical branch, Work ledger, accepted evidence, Control plane, or another Attempt's workspace. Accepted declared outputs cross a validated artifact seam; failed environments are destroyed or quarantined with evidence.
7. **Typed immutable artifacts.** Modules exchange versioned manifests referencing content-addressed blobs. Provenance includes the producer Attempt, all declared input digests, schema and policy versions, tool/model/runtime profile, timestamps, purpose, and output digests. Human-readable Markdown may render an artifact but never author a state transition.
8. **Append-only graph evolution.** Autonomous re-planning materializes a new Graph revision. Accepted history remains immutable; obsolete unfinished atoms become `superseded`; work with invalidated preconditions is cancelled or quarantined. A new revision cannot retroactively change the evidence under which earlier work was accepted.
9. **Deep modules and explicit seams.** The external architecture consists of:
   - `Orchestrator`: materialize runs, reconcile state, and expose pause/resume/cancel/observe behavior.
   - `WorkLedger`: atomically transition durable work and query readiness.
   - `WorkerRuntime`: execute one Work atom and return a typed observation/result.
   - `ExecutionBroker`: create, observe, and destroy isolated Attempt environments.
   - `ArtifactStore`: persist and retrieve immutable manifests and blobs.
   - `InferenceGateway`: admit and execute context-budgeted model requests.
   - `GateRunner`: execute deterministic validators and record evidence.
   - `ProductGraph`: manage declared structure and derive/compare observed structure.

   Each is a deep module with one small interface; internal helpers do not automatically become public seams. An Adapter is introduced only when at least two real implementations need to vary.
10. **Profiles above the core.** PM, developer, reviewer, and security roles are versioned workflow/Capability-profile concerns inspired where useful by SFLO. The core understands capabilities, dependencies, Attempts, artifacts, evidence, and gates—not organizational role names.
11. **Independent use of reference designs.** GFLO may adopt Gas City-inspired materialized graphs, append-only Attempts, leases, reconciliation, and disposable workers, plus SFLO-inspired artifact stages and bounded loops. It will not import, invoke, embed, emulate storage formats for, or provide fallback compatibility with either project. Any future source-code port is a separate explicit licensing and maintenance decision.
12. **Evidence-led staged growth.** Do not implement the full architecture in one pass. The staged plan must first build the thinnest durable walking skeleton and exercise a small set of logical workers against the real local Qwen3.8-27B/RTX 5090 service, serialized through the InferenceGateway. It must measure typed-result reliability, context sufficiency, retry/recovery behavior, and completion on tiny real tasks. Only then may it add Product-graph sophistication, broader workflows, more Capability profiles, self-growth, or operational layers. Every stage has explicit falsification thresholds and may revise schemas, seams, atom granularity, prompts, or planned layers when new evidence contradicts an assumption.

This resolution fixes the logical architecture, not the implementation language, database product, worker harness, or concrete class/package layout; those remain for [Select the implementation foundation](09-select-the-implementation-foundation.md).
