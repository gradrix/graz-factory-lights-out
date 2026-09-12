# Build and qualify a reusable import-service POC

Type: task
Status: needs-info
Blocked by: 74

## Scope

Owner selected the CSV inventory import service and explicitly requested scalability
and reuse. Build through the pinned local-model factory with independent checks.
Resolve dependencies into a reproducible pinned image; freeze three original builds,
record all failed attempts and assistance. Independently check streaming input,
idempotent submissions, fenced lease ownership, crash recovery, multiple worker
processes, HTTP behavior, packaging and generated tests. Demonstrate reuse with a
second job handler added through factory work to an accepted project.

Use a bounded single-host SQLite baseline with explicit limits and actual load
measurements. Separate parser, immutable payload storage, durable job state and
HTTP/worker entry points. Avoid promises of multi-host throughput without qualifying
shared storage and database behavior. Preserve raw evidence in .gflo and portable
requests/checks/reports in .scratch. Never manually fix delivered model candidates.
Factory campaign setup and checking should be reusable across these modules/jobs;
larger execution admission remains a separately versioned runtime requirement.

## Progress and blocking decision

Reference implementation and independent correctness/runtime harnesses are concrete
and passing on the corrected SQLite image. Three model builds plus a bounded
continuation failed before completion; no application delivery or second built-in
handler feature is complete. [Evidence](../importflow/README.md). The next decision
is whether direct Codex implementation may supply the application, or whether to
continue local-model-only reliability work. That authorship distinction materially
changes what the POC demonstrates; no answer has been assumed.
