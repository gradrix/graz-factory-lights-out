# Qualify atomic move batches on ai-gamer

Type: task
Status: resolved

## Frozen scope

Pinned ai-gamer main 9a0a4384b9b727c02f0f2c168c7abc43a4e076bf. RecorderDb.addMoves
currently returns -1 after a later NOT NULL failure but leaves earlier inserted rows
pending; createPlayer then commits them. The minimized real-SQLite reproducer is
atomic-moves/reproduce.py. Explicit rollback prevents the leak; a separate connection
sees no row before that commit, ruling out an earlier commit or stale reader.

Let the pinned local model plan, implement and test atomic batches. Preserve success
return True, SQLite Error return -1, enumeration-based idx, supplied move/date values,
committed existing rows, empty batches, and subsequent writes. Rollback must finish
while the writer lock is held. Restrict implementation edits to addMoves and generated
tests to one new test file. No dependency, schema or unrelated method changes.

Preflight independent real-SQLite checks and wrong implementations before inference;
freeze three same-policy trials with existing two-attempt/three-turn worker budgets.
Audit accepted results for old behavior preservation and earlier factory winner tests.
Retain all failures and no manual candidate repair. Publish an accepted target change
only after review. This is supervised task and validator design, not autonomous bug
selection or unrestricted database qualification.

## Answer

Merged [ai-gamer PR 2](https://github.com/gradrix/ai-gamer/pull/2) at
`d278d7c7f59da72ea48d4b106ba4d41e67949c0a`. The local model wrote the implementation
and five tests; published bytes match accepted trial v4/trial-2 without manual correction.
All 22 new/existing winner tests, independent insertion/commit/lock checks, four test
faults, held-out deferred-commit recovery and acceptance replay pass. 87 original files
remain unchanged. The original reproducer no longer leaks failed rows.

Baseline v2 accepted 0/3 complete builds. After issue 65, identical requests/policies
on fresh ledgers accepted 1/3. All six implementation workers accepted; five test workers
failed. Missing context was confirmed and repaired, but no general reliability gain is
established; wrong SQLite/index assumptions remain. No model/deployment/budget change.
[Portable source, validators, all responses and delivery proof](../atomic-moves/README.md).
