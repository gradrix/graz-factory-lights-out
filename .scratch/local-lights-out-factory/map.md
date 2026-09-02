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

## Decisions so far

- [Establish the single-GPU feasibility envelope](issues/01-establish-single-gpu-feasibility-envelope.md): Qwen3.8-27B is viable as one serialized NVFP4 inference worker, with 8K routine contexts, 16K justified contexts, and a provisional 32K ceiling pending exact-machine benchmarks.
- [Compare factory orchestration foundations](issues/02-compare-factory-orchestration-foundations.md): Primary-source comparison favors a minimal durable core informed by Gas City graph/reconciliation semantics and SFLO evidence-gate policy, with coding harnesses kept behind a replaceable boundary.
- [Research atomic context and code structures](issues/03-research-atomic-context-and-code-structures.md): Evidence supports separate Work and Product graphs, progressive authoritative retrieval, content-addressed invalidation, and deterministic conformance; minimal context and long-horizon modularity remain empirical hypotheses.

## Not yet specified

- Operational production-readiness details—model-server tuning, observability retention, storage sizing, and the exact soak workload—will become precise only after the reference architecture and evaluation thresholds are settled.

## Out of scope

- Autonomous publication or production deployment; the destination ends with locally validated code, local branches/commits, and an implementation-ready plan.
- Training a foundation model or depending on a proprietary cloud model for core Factory operation.
- Claiming support for a technology stack without an explicit Capability profile and validation evidence.
