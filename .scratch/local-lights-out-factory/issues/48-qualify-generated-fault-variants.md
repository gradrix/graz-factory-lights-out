# Generate bounded Python fault variants and qualify against trusted tests

Type: task
Status: resolved

## Scope

Deterministically generate limited AST mutations within a named function; no product
names or runtime host execution. Qualify each through the existing sandboxed pytest
adequacy gate using operator-owned reference tests. Preserve all outcomes and source,
test-bundle, gate and execution identities. Only demonstrated behavioral faults may
be selected; do not infer equivalence from survival or correctness from mutation score.
Exercise parser and independent numeric examples. Keep model and serving unchanged.

## Answer

Implemented propose_faults and qualify_faults in gflo/mutations.py, plus portable
scripts/qualify_python_faults.py. Eight parser proposals yielded six assertion-proven
faults and two excluded error-producing variants. Automatically selected faults
reject retained weak tests and accept repaired tests. Numeric qualification selects
two generated faults and excludes unchanged/crashing controls. No model calls.

The first reference-wrapper preparation had a NameError; no faults were selected.
Corrected reference wrapper and retained failure identity in results. Trusted oracle
and function selection remain necessary; no automatic correctness-discovery claim.

[Results](../generated-faults-results.json) and [fixture](../generated-faults-fixture.json)
are portable. Fresh-store reconstruction verified. All 445 tests and 25 subtests
passed with Docker enabled; ruff and mypy pass. No product changes were published.
