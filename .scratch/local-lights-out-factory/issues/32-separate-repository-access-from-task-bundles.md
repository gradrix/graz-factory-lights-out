# Separate repository access from bounded task bundles

Type: task
Status: ready-for-agent

## Requirement

The owner requires a path to large repositories without a rewrite of planning and
execution around demo-only assumptions. Follow [ADR 0001](../../../docs/adr/0001-repository-snapshots-and-bounded-task-inputs.md).
Do not add a speculative graph framework or merely increase existing bundle limits.

## First implementation slice

Introduce a versioned immutable repository snapshot manifest and a repository access
module with real bundle-backed and snapshot-backed implementations. Define the
small interface against those implementations: bounded listing/text search, exact
file or range reads, context selection, and execution-input preparation. Results
carry source identity, file digest, location, and explicit omissions/coverage.
Snapshot capture must handle a dirty checkout by content identity, not label mutable
files with HEAD. Refuse unsupported symlinks/submodules/binaries explicitly until
their semantics are implemented; do not silently flatten or omit them.

Preserve all historical WorkAtom, RunPlan, candidate, and acceptance identities.
Version new records; retain the old adapter. Plan materialization should route
source preparation through this module before it grows into a general scheduler.
Keep task dependencies independent of the chosen repository index implementation.

Represent proposed changes against original file identities and preserve every
unselected file during assembly. Do not interpret a bounded selection as the full
repository. Model-visible context and build/test inputs have separate budgets.
Retain existing broker restrictions until a larger isolated materializer is tested.

## Acceptance criteria

- Equivalent old-bundle and new-snapshot reads/selections produce identical source
  bytes, while historical records retain their original digests and replay behavior.
- A repository larger than 256 KiB can yield a bounded task selection without
  serializing all repository contents into its WorkAtom or model prompt.
- Changed source, stale index results, missing selected content, and ambiguous base
  identity are rejected or explicitly reported; stale lookup is never a clean result.
- Empty search with complete coverage is distinguishable from truncated, unsupported,
  or unindexed search. Queries cannot escape scope, even through path aliases.
- Applying a selected-file edit preserves untouched/omitted files; mismatched
  original file content prevents assembly and reuse.
- Bounded selection does not pretend that a full repository build was validated.
  Retain independent integration checks and report execution-input coverage.

## Later slices

Add revision-bound symbol definitions/references/imports, then dependency/impact
queries and incremental updates. Pin analyzer/config identities and measure coverage.
Choose storage/index technologies against measured workloads, keeping derived data
rebuildable. Qualify on a representative larger repository: navigation accuracy,
selection sufficiency, stale-data rejection, index time/memory/disk, model cost,
and repeated whole-feature success. Set numerical targets before each trial.
A synthetic million-line lookup exercise is a performance probe, not software-build
qualification. No million-line capability claim until real work is demonstrated.
