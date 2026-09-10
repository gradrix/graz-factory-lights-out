# Preserve opaque files in repository snapshots

Type: task
Status: resolved

## Observed blocker

Capturing ai-gamer fails on tracked console_client/db/game_records.db (24,576 bytes).
A whole repository identity must preserve this existing database even though the
rule worker does not read or execute it. Excluding it would invalidate the intended
unchanged-file qualification.

## Requirement

Allow bounded opaque bytes in captured snapshot blobs without changing existing
snapshot records or hashes. Keep source reads, text search, text edits and worker
execution selections explicitly text-only. Preserve opaque identities through
unrelated text edits; corrupted omitted blobs must still stop candidate lifting.
Retain all existing capture limits and symlink/submodule protections.

## Answer

Capture retains bounded opaque blobs with existing identities and limits; text APIs
continue to reject unsupported content. Regression checks cover NUL/non-UTF-8 data,
unchanged identities after text edits, and missing omitted blobs. The full 87-file
ai-gamer snapshot, including its SQLite database, reconstructs with the exact digest
in a fresh ledger. No binary execution/edit support was added.
