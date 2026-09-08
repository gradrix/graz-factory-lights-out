# Prototype the reference architecture

Type: prototype
Status: resolved
Assignee: codex
Blocked by: 04, 05, 06, 07, 08, 09, 10

## Question

Does a concrete low-fidelity architecture—component diagram, durable state transitions, artifact schemas, Work atom lifecycle, Product graph lifecycle, and one end-to-end example—faithfully embody the decisions and expose any missing or contradictory contracts?

## Comments

### Reference architecture discussion prototype

Created a [reference walkthrough](../prototypes/reference-architecture.prototype.md) and [single-file interactive lifecycle demo](../prototypes/factory-lifecycle.prototype.html). Both are explicitly throwaway, unvalidated design artifacts. The demo covers coordinated provider/consumer work, no self-approval, skipped checks, stale evidence, interrupted attempts, and advisory quality findings. It performs no model calls or real persistence and cannot count toward evaluation thresholds.

Pending user review; this ticket is not resolved. No prototype code has been promoted to implementation or committed. Branch capture is deferred until a decision is validated and a commit is explicitly authorized.

### Accepted dependency-recovery simplification

The user accepted checks-first recovery rather than automatic manager invocations throughout the hierarchy. Keep explicit dependency edges, pinned contracts, and vertical requirement/evidence projections; use deterministic test selection and dynamically materialized diagnosis/repair work by default. Failure location does not establish defect ownership. The scheduler owns task creation, deduplication, dependency ordering, and cumulative accounting; workers propose findings. Intentional breaking changes still plan known migrations upfront. Invoke scope planning only for ambiguous or coordinated changes and failed local recovery. Incomplete coverage requires broader verification, not assumed compatibility.

The reference walkthrough and demo have been updated with this direction. The refinement is accepted; real-model feasibility and full prototype review are not implied.

### Walking-skeleton constraint

The reference architecture must show an evidence-led vertical growth path: walking skeleton, real local-model worker experiment, measured revision point, then conditional higher layers. It must not imply a one-shot build of the final architecture.

Show the distinction between the rich durable Work-atom record, purpose-specific Worker views, immutable Context-manifest revisions, typed expansion, capability discovery, evidence-derived retry context, and Work-ledger-owned acceptance.

## Answer

Following discussion of the prototype, the user accepted the checks-first dependency-recovery recommendation and requested continuation. Adopt the reference walkthrough with that refinement as the planning reference: small worker views, explicit dependency/contract records, trusted gate evidence, candidate-versus-product acceptance, and scheduler-owned dynamic diagnosis/repair. Scope planning is on demand, not a mandatory manager cascade.

The prototype exposes design cases, not proven execution. Its browser behavior, real persistence, failure localization, vertical impact containment, and local-model performance remain unverified. These are implementation experiments, not claims established by resolving this design ticket. Preserve the HTML as a throwaway discussion artifact; no code promotion, branch switch, or commit is performed by this resolution.
