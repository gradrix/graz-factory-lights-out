# Repair newly created file drafts without protocol confusion

Type: task
Status: resolved

## Evidence

Test-decomposition solo-2 created a new test file with a missing colon. Development
checks reported the syntax error. The worker then submitted whole-file candidates
rather than window repairs, exhausting both attempts despite leaving response budget
unused. This is a generic draft-state/protocol boundary, not a clamp-specific bug.

## Scope

Make the distinction between immutable input files and files created in the current
work explicit in worker edit authority. Investigate allowing bounded complete replacement
of newly created files while keeping original existing-file edits range-bound; alternatively
provide a clearer typed repair action/result. Do not accept partial output, grant writes
outside scope, discard unseen original bytes, or add retries. Preserve historical replay
and qualify against the retained failure plus original-file rejection tests. Prefer
state/protocol design to task-specific prompting. Do not hardcode test file names.

## Answer

Window parsing now binds immutable input identity and permits complete replacement only
for task-created files. Scope and complete-draft checks remain enforced. The unedited
retained repair passes all fault gates; three fresh GPU trials accepted, including one
two-response draft repair. 499 tests and 25 subtests pass; historical replay unchanged.
[Evidence and reproduction](../draft-repair/README.md).
