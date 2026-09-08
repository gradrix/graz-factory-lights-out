# Local Lights-Out Software Factory

Label: wayfinder:map

## Destination

Produce a research-backed feasibility verdict, architecture specification, and staged implementation plan for a Linux software Factory running Qwen3.8-27B on one RTX 5090 with 64 GB system RAM. The design must attempt autonomous end-to-end product creation, fall back safely to bounded Work atoms, and generate modular products whose structure remains comprehensible through authoritative graphs and small retrieved contexts.

## Notes

- Use the `research`, `grilling`, `domain-modeling`, and `prototype` skills as named by each ticket.
- Planning only: this map ends at an implementation-ready plan and validation strategy, not a production implementation.
- Optimize Work atoms and Product modules for the smallest context that preserves correctness; extra local inference time and token use are acceptable.
- Start validation with greenfield products, then controlled changes to existing repositories.
- The core is stack-neutral; technology support is explicit through Capability profiles.
- Source code, contracts, tests, and validated structural manifests are authoritative. Summaries and semantic indexes are navigation aids.
- Deterministic evidence is the primary approval authority. Isolated model reviews may add evidence but may not waive executable criteria.
- Autonomous recovery is bounded. Failed work is quarantined with evidence before escalation.
- The Factory may create local branches and commits. Publishing and deployment require human approval.
- Prefer primary sources, reproducible measurements, and explicit separation between vendor claims and independently observed results.
- Large greenfield and existing applications remain the target; internal modules do not require microservice deployment. Time and energy costs are acceptable, with correctness and recoverable progress taking priority over throughput. Future local models require fresh calibration.

## Decisions so far

- [Establish the single-GPU feasibility envelope](issues/01-establish-single-gpu-feasibility-envelope.md): Qwen3.8-27B is viable as one serialized NVFP4 inference worker, with 8K routine contexts, 16K justified contexts, and a provisional 32K ceiling pending exact-machine benchmarks.
- [Compare factory orchestration foundations](issues/02-compare-factory-orchestration-foundations.md): Primary-source comparison favors a minimal durable core informed by Gas City graph/reconciliation semantics and SFLO evidence-gate policy, with coding harnesses kept behind a replaceable boundary.
- [Research atomic context and code structures](issues/03-research-atomic-context-and-code-structures.md): Evidence supports separate Work and Product graphs, progressive authoritative retrieval, content-addressed invalidation, and deterministic conformance; minimal context and long-horizon modularity remain empirical hypotheses.
- [Define the autonomy and safety contract](issues/04-define-autonomy-and-safety-contract.md): A preauthorized Lights-out run has no routine human gates; automated isolation, deterministic evidence, ten-attempt atom circuit breakers, autonomous re-planning, broad sandboxed execution, and generational self-upgrades carry it to verified local completion or a terminal exception.
- [Choose the durable orchestration architecture](issues/05-choose-durable-orchestration-architecture.md): GFLO owns a reconciliation-driven Work ledger and deep orchestration modules, uses SFLO/Gas City only as design references, and must grow empirically from a thin real-Qwen walking skeleton rather than a one-shot implementation.
- [Define the Work atom and context contract](issues/06-define-work-atom-and-context-contract.md): Rich durable atom records project into minimal role-specific Worker views; adaptive 4K–32K Context policies, typed expansion, broad sandboxed tool discovery, evidence-derived retries, and ledger-owned acceptance keep weak-model work small and empirically tunable.

- [Define the Product graph and module contract](issues/07-define-product-graph-and-module-contract.md): Nested scopes with cross-scope dependency edges support compact steward views and coordinated provider/consumer migrations; large greenfield and maintenance workloads are targets, with scaling and future models calibrated experimentally.

- [Design verification and recovery gates](issues/08-design-verification-and-recovery-gates.md): Factory code owns evidence and acceptance; narrow model jobs support independent checks and autonomous repair, with small-model suitability to be measured before adding QA or hierarchy layers.

- [Select the implementation foundation](issues/09-select-the-implementation-foundation.md): Typed Python core, local SQLite/artifacts, isolated containers, and a GFLO-owned model loop start the experiment; product technologies remain profile-driven, with second-language and mixed-stack validation before support claims.

- [Set feasibility and evaluation thresholds](issues/10-set-feasibility-and-evaluation-thresholds.md): Versioned local-model campaigns measure completion, small-context fit, acceptance integrity, recovery, and scale; profile-owned quality checks include calibrated CRAP hotspots without weakening mandatory correctness.

- [Prototype the reference architecture](issues/11-prototype-the-reference-architecture.md): The walkthrough separates small worker views, checked candidates, and integrated completion; tests drive scheduler-owned diagnosis/repair, with scope planning on demand and runtime behavior still unverified.

## Not yet specified



- Operational production-readiness details—model-server tuning, observability retention, storage sizing, and the exact soak workload—will become precise only after the reference architecture and evaluation thresholds are settled.

## Out of scope

- Autonomous publication or production deployment; the destination ends with locally validated code, local branches/commits, and an implementation-ready plan.
- Training a foundation model or depending on a proprietary cloud model for core Factory operation.
- Claiming support for a technology stack without an explicit Capability profile and validation evidence.
