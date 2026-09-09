# Draft bounded feature plans from repository context

Type: task
Status: resolved

## Scope

Accept an immutable source snapshot, feature requirements, allowed paths, and a
trusted pinned environment catalog. Ask the local model to propose tasks,
dependencies, interface contracts, acceptance checks, and unresolved questions.
Validate structural coverage, scope, environment selection, source references,
and dependency order. Reject unordered overlapping writable scopes.

Plans remain reviewable proposals. Generated test descriptions do not become
trusted acceptance gates, and structurally valid plans never authorize execution.
Use two attempts, at most three model turns each, fixed 8K/2K context/output,
retained model evidence, no implicit resume or retry after transport failure.

Trial on a broader compact history-summary feature without supplying the task
breakdown. Inspect semantic quality separately from structural validation.
Do not claim autonomous sprint planning or environment provisioning from a draft.

## Answer

Implemented `plan-feature` and `check-plan`. Structural validation checks request
binding, scope, existing read references, trusted environment selection, requirement
coverage, DAG order, and unordered overlapping writes. Drafts never authorize work.

Live exploration exposed missing deployment provenance, accumulated-source context
overflow, output truncation, and excessive routine questions. Fixed provenance
validation, added a bounded interface index/two-file reading window, compacted
schema presentation, and introduced a prospective planning-v2 budget (12K/4K,
non-thinking, two attempts/three turns). Earlier failed runs remain recorded.
The final trial produced renderer, CLI, tests, and docs tasks, with matching proposed
interfaces and no blocking questions. Reviewer checked scope and semantic coverage.
This is one explored feature, not a frozen planning benchmark; tasks not executed.

[Portable results](../planning-trial-results.json) retain proposal content, costs,
request/source identities and all earlier failures. Next engineering milestone is
reviewed-plan materialization with trusted gates and dependency-aware execution.
