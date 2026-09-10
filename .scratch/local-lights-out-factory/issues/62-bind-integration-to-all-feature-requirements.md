# Bind integration provenance to all feature requirements

Type: task
Status: ready-for-agent

## Evidence

The split-test campaign's final integration atom inherited requirement_ids from the
last completed task (values), although the request and combined gates cover values
and types. gflo/progression.py copies completed[-1].run.atom before overriding final
fields. Combined checks were executed, so this is incomplete provenance metadata,
not evidence that the types gate was bypassed.

## Scope

Give new integration records explicit whole-feature requirement provenance and review
other inherited task-local metadata. Preserve the exact meaning and replay identities
of old accepted records through an explicit versioned path; do not rewrite history.
Test disjoint requirements across multiple tasks, combined acceptance and legacy replay.
