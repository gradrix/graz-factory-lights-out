# Define the autonomy and safety contract

Type: grilling
Status: resolved
Assignee: codex
Blocked by: 01, 02

## Question

Given the observed local-model envelope and available orchestration mechanisms, which actions may proceed unattended, which require deterministic evidence, which consume bounded recovery budgets, and which must escalate to a human?

## Comments

## Answer

### Resolution — 2026-09-02

A **Lights-out run** begins after a human accepts an Intent package and its Preauthorization envelope. From that point through Verified completion, routine planning, coding, dependency resolution, testing, local integration, recovery, and evidence-gate transitions proceed without human decisions or approvals. Isolation and gates are automated operating machinery, not HITL stages.

The autonomy and safety contract is:

1. **Unattended local authority.** Workers may read, plan, index, search the Internet, install dependencies, run downloaded or generated code, modify their isolated attempt checkout, test, and propose local integration. Passing mandatory evidence gates authorizes local commits and integration automatically. Publishing or deploying the produced product remains outside this map's Preauthorization unless a later policy explicitly grants it.
2. **Assumption authority.** The Factory may decide reversible questions inside the Intent package and must record the assumption. Material scope changes, contradictions, or authority absent from Preauthorization are terminal exceptions; they are not silently invented or used to weaken acceptance.
3. **General network access with least exposure.** Attempt workers may use outbound DNS and HTTP(S), including `curl`, public Git hosts, registries, documentation, and search APIs. Network profiles range from open Internet with disclosure-safe inputs, through restricted egress for private source, to offline work. Access to private/local ranges, host services, metadata endpoints, inbound listeners, and non-profile protocols is denied unless explicitly granted. Authenticated services use scoped, expiring, quota-controlled credentials brokered without exposing raw long-lived keys to the model.
4. **Untrusted evidence boundary.** Web pages, tool results, dependency metadata, and downloaded content are evidence, never Factory instructions. Consequential sources retain provenance and must be corroborated when they could change security, architecture, or acceptance behavior.
5. **Downloaded execution is allowed.** Network bytes must be saved and identified by digest before execution; stream-to-shell forms are forbidden. Installers, lifecycle hooks, scripts, dependencies, and generated binaries run only inside fresh unprivileged Attempt workers. Workers receive no runtime socket, host credentials, canonical-repository write access, or elevated capabilities. Declared outputs cross back through a validated artifact interface, and the worker is destroyed after the attempt.
6. **Deterministic authority.** Required deterministic checks, product scenarios, architecture conformance, and policy validators author gate truth. Model reviews may contribute findings but cannot waive a check or mark an otherwise unverifiable mandatory requirement verified. A legitimate contract change is a separate traceable Work atom; repair attempts may not weaken, delete, skip, or reinterpret their own acceptance criteria.
7. **Ten-attempt circuit breaker.** A Work atom has at most ten append-only attempts. No more than two consecutive attempts may repeat the same failure signature. Every retry must add evidence, revise context, decompose the task, or materially change strategy; attempts seven through ten require an explicit autonomous re-plan. Exhaustion quarantines the atom without deleting evidence or relaxing gates.
8. **Run-level persistence.** Atom exhaustion does not summon a human or stop unrelated work. The supervisor autonomously re-plans the blocked objective, changes decomposition or Capability profile, and materializes a new Work graph. A run stops only at Verified completion, a mechanically demonstrated requirement contradiction, missing preauthorized authority or credentials, a violated host-safety invariant, or exhaustion of an enabled run-wide budget.
9. **Configurable resources, invariant host survival.** Token, wall-time, tool-call, download, ordinary memory, and monetary budgets are configurable and may be explicitly disabled. External emergency cancellation, minimum host disk/availability reserves, privilege boundaries, and protection of the Control plane remain non-disableable by an Attempt worker.
10. **Failure containment.** Recovery may restart processes, expire leases, rebuild disposable environments, revert isolated attempts, refresh derived context, and quarantine evidence. It may not erase history, alter accepted evidence, weaken policy, directly mutate the canonical branch, or conceal failure. A blocked dependency subgraph does not stop independent work.
11. **Structured exceptional escalation.** When execution cannot continue within Preauthorization, the Factory produces an Escalation packet describing the required authority or contradiction, attempts, evidence, affected modules, options, and recommendation. Escalation is a terminal exception, not a normal approval gate.
12. **Verified completion.** Completion requires every mandatory requirement to link to passing evidence, declared and observed Product graphs to conform, required tests and scenarios to pass, no unresolved terminal exception, and a reproducibly buildable accepted local revision.
13. **Autonomous self-growth by replacement.** The active Generation never rewrites itself in place. It builds and tests an immutable candidate Generation, rehearses migrations on copied state, runs shadow/canary checks, and asks an external non-model launcher to promote it. A preauthorized self-update channel may promote without human approval and must roll back automatically on failed health checks. Root-policy, launcher, credential-boundary, sandbox, and self-approval changes require a distinct higher-trust Preauthorization class.

The later implementation-foundation decision must evaluate a **reuse-first hypothesis**: prototype Gas City as the durable orchestration substrate, apply SFLO-derived workflow/gate policy, and add only the local-Qwen atomic-context, inference-admission, Product-graph, and deterministic-evidence layers that are missing. A custom core is the fallback if that bounded prototype fails explicit simplicity, reliability, or atomicity criteria; this resolution does not pre-decide that later ticket.

Supporting research: [Sandboxed execution and safe self-update](../research/sandboxed-execution-and-self-update.md)

### Subsequent clarification

The reuse-first implementation hypothesis above was superseded by [Choose the durable orchestration architecture](05-choose-durable-orchestration-architecture.md). SFLO and Gas City are design references only; GFLO will not depend on or preserve runtime compatibility with either.
