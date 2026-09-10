# Index revision-bound Python definitions

Type: task
Status: resolved

## Requirement

Implement the next ADR 0001 navigation slice: bounded Python definition indexing,
exact snapshot-bound lookup, explicit analyzer/coverage, and reuse of unchanged
file analysis. Expose it through repository CLI. No source execution, scope expansion,
caller-absence claims, or acceptance authority. Keep graph/index storage out of the
scheduler contract.

## Qualification

Check nested/async/duplicate definitions, unsupported/syntax-error coverage, limits,
stale index and hit rejection, scope isolation, changed-file invalidation and unchanged
reuse. Measure on GFLO itself, verify source reads from located definitions, and
record prospective navigation probes before broader model feature trials.

## Answer

Implemented `gflo.symbols` and repository `index-symbols`/`symbols` commands.
Definitions and reusable file shards bind source hashes and Python analyzer version;
query coverage includes omissions and truncation. Nine regression tests passed.
Real GFLO scope: 27 files indexed in 0.332 s, reused in 0.007 s; five known-definition
queries and source reads passed. See [results](../symbol-navigation-results.json)
and [guide](../../../docs/product-intake.md). No automatic planner navigation,
caller graph, or million-line claim follows from this qualification.
