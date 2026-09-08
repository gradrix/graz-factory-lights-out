# Build the durable Work ledger

Type: task
Status: resolved
Assignee: codex

## Scope

Build typed, versioned Work-atom inputs and append-only Attempt events with SQLite transactions, foreign keys, WAL and explicit durability. Implement submission, status and reconciliation primitives with CLI access. Start from the accepted Work-atom contract; keep runtime I/O outside transactions.

## Acceptance

Tests demonstrate reopening durable state, atomic claims under competing connections, stale/expired Lease rejection, finite retries preserving failed Attempts, and conditional exactly-once acceptance. Acceptance requires trusted gate evidence and current preconditions; a WorkerResult cannot accept itself. Contract validation rejects malformed records before persistence. Full artifact and gate integration follows in dependent tasks.

## Comments

2026-09-08: Implemented the prepared-task ledger slice after the user's instruction to proceed. The package uses strict frozen Pydantic contracts and standard-library SQLite; launcher scripts retain their independent standard-library environment.

## Answer

Implemented [WorkLedger](../../../gflo/ledger.py), [versioned records](../../../gflo/records.py) and the `gflo submit/status/resume` CLI. Contracts, Attempts, events, gate receipts and acceptances are immutable; state changes commit atomically with events using WAL, FULL synchronous durability and foreign keys. Claims serialize across connections, leases fence stale results, retries require the latest failure plus a changed strategy or new evidence, and the finite budget quarantines exhausted work. Acceptance requires matching current inputs and all pinned passing gate receipts, and repeated acceptance returns the original result.

[Usage and authority boundaries](../../../docs/ledger.md) describe the trusted-only API, pinned environment and sample contract. Gate receipt ingestion is a controller seam, not a WorkerResult capability. Actual artifact existence/output conformance and validator execution remain explicitly in the dependent artifact/broker tasks. Reconciliation fences expiry but does not kill old worker processes or dispatch new ones.

Validation: 36 ledger tests plus the existing 29 launcher/target tests pass (65 total; pytest also reports 12 unittest subtests). Real SQLite and subprocess tests cover competing claims and acceptance, forced process death mid-transition, reopen recovery, stale leases, malformed inputs, missing/failing/inconclusive/mismatched evidence, immutable history and retry exhaustion. Ruff check/format and strict mypy pass; editable package installation and `gflo --help` work; pip reports no broken requirements. No model or GPU service was started for this slice.

Next: [Publish and reconcile immutable artifacts](15-publish-and-reconcile-artifacts.md). Target serving qualification remains independently incomplete.
