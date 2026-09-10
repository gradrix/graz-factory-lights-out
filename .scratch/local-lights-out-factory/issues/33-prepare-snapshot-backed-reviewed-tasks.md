# Prepare snapshot-backed reviewed tasks

Type: task
Status: resolved

## Requirement

Bridge reviewed feature proposals to bounded executable RunPlans without embedding
whole repositories or interpreting model acceptance prose as trusted gates. Preserve
legacy records. Bind review to request/proposal and exact repository identity;
separate explicit execution inputs from model context and report dependency blockers.
Reject unresolved questions, stale sources, incomplete inputs, and mismatched review.
Retain omitted repository files when lifting a task candidate to a proposed snapshot.

This slice prepares independent root tasks only. Dependent tasks require later
accepted-base progression; do not silently prepare them against the original base.
Product intake and hierarchical delegation must use explicit requirements, owned
interfaces, bounded work, and independent combined validation. Recursive managers,
autonomous intake, and whole-product acceptance remain unqualified.

## Answer

Added versioned repository feature requests, controller-authored plan reviews, and
prepared task packages in `gflo/preparation.py`, exposed through `gflo prepare-task`.
Structural graph checks now operate on path inventories without loading source bytes.
Legacy request/run identities are unchanged. Root tasks carry relevant requirements,
exact snapshot binding, bounded selections, and independently supplied ProcessGates.
Review changes produce new work identities. Candidate lifting preserves omitted
files and rejects stale sources, missing original evidence, and scope escapes.

16 tests cover controller submission, larger-than-bundle source, missing/over-budget
inputs, questions, dependencies, review mismatch, stale lifting, and CLI behavior.
Full suite: 337 passed, eight optional skips, 25 subtests. Docker fixture matched
correct output and rejected faulty output; no LLM or ledger acceptance was exercised.
See [results](../preparation-results.json).

Dependent-task progression and snapshot-backed model drafting remain future work.
[Product intake](../../../docs/product-intake.md) describes the intended hierarchy
and implemented limits. Next: accepted-base progression, independent combined gates,
and repeated multi-task feature qualification.
