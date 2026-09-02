# Research atomic context and code structures

Type: research
Status: resolved
Assignee: atomic_context
Blocked by:

## Question

What primary-source evidence and proven techniques support decomposing agent work and generated software into small contract-bound units, navigating repositories through maps or graphs, retrieving minimal authoritative context, and detecting architectural drift without requiring the model to ingest the whole repository?

## Comments

### Resolution — 2026-09-02

Primary evidence supports a hybrid architecture: narrow typed Work atoms, authoritative source/contracts/tests and compiler/build facts, graph-first progressive retrieval, explicit context expansion, content-addressed dependency invalidation, and deterministic architectural conformance. It does **not** support treating summaries/vector indexes as truth, equating tiny prompts with tiny Product modules, or claiming arbitrary lights-out construction is solved. Qwen3.8-27B and single-RTX-5090 results make bounded local coding plausible, while long-horizon studies show structural erosion remains a serious unsolved risk. “Minimal sufficient context” cannot be proven generally; it must be evaluated per Capability profile with retrieval-recall, context-precision, expansion, stale-context, ablation, and sequential-extension tests.

Full cited report: [Atomic context and code structures for a local software Factory](../research/atomic-context-and-code-structures.md)
