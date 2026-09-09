---
status: accepted
---

# Separate repository identity from bounded task inputs

GFLO currently embeds source bundles in requests, run plans, and candidates, which
couples repository size to worker-input limits. Future source contracts will identify
an immutable repository snapshot separately from context selections, execution inputs,
and proposed edits. This preserves bounded workers while allowing revision-bound
search, symbol indexes, and dependency graphs behind a repository access module.

## Consequences

This is an accepted migration direction, not an implemented indexing capability.
The existing SourceBundle path remains the first adapter and historical records
retain their exact meaning and digests. New source contracts must be explicitly
versioned; never reinterpret an old bundle digest as a repository identity.

Before extending plan materialization to general repositories, put source access and
input preparation behind this module. Planners and schedulers should consume source
references and bounded query results, rather than scanning an entire file dictionary
or requiring a particular index engine. Introduce the executable interface with a
real snapshot-backed adapter and parity tests, not an unused generic framework.

Repository source is authoritative. Indexes are derived, revision-bound data with
recorded coverage and analyzer versions; stale or incomplete results cannot prove
that a symbol has no callers. Missing context must remain distinguishable from a
missing file. Index results never expand writable scope or authorize acceptance.

Model context and execution inputs are separate selections. A task may need a small
model view but a larger build/test environment. Larger execution inputs need their
own isolated materialization and qualification; raising prompt or SourceBundle
limits does not solve that problem. Edits bind to their snapshot and original file
content, so omitted files survive candidate assembly and unrelated code need not
be copied into every candidate. Acceptance still depends on current inputs and
independent gates, not graph confidence.
