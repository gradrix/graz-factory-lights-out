# Publish and reconcile immutable artifacts

Type: task
Status: resolved
Blocked by: 14

## Scope

Implement content-addressed artifact publication before ledger references and crash reconciliation.

## Acceptance

Tests cover interrupted publication, duplicate writes, corrupt/missing content, orphan discovery, and reopen recovery. Never accept absent or unverified content. Retain failed-attempt evidence; do not garbage-collect live or accepted references.

## Answer

Implemented `gflo/artifacts.py` and ledger integration. Controller-owned content-addressed bytes publish through synchronized staging files and atomic no-replace hard links. The ledger verifies byte references before persistence and rechecks dependencies/candidate/evidence before acceptance. Read-only auditing includes failed/superseded attempt references and reports missing/corrupt objects, staging leftovers and publication-before-commit orphans. Nothing is garbage-collected or silently repaired.

Validation: 94 tests and 23 subtests pass across the suite; Ruff checks/format and strict mypy pass. Added real process-crash coverage before/after publication and between publication and SQLite commit, concurrent duplicates, reopen, missing/corrupt content, nonregular files, dependency admission, failed-evidence retention and accepted-content loss. See [artifact documentation](../../../../docs/artifacts.md) for API, storage assumptions and limits. Workers and validator execution remain tasks 16–18.

## Comments

2026-09-08: After a bounded serving-tuning review, the user’s preference to prioritize product implementation was applied. No engine configuration changes or new inference measurements were made; vLLM remains ready as the working default. Artifact implementation completes the next core slice.
