# Qualify bounded failed-call definition context

Type: task
Status: ready-for-agent
Blocked by: 68

## Evidence

[Ground repair calls in revision-bound definitions](68-ground-repair-calls-in-visible-definitions.md)
established that helper definitions were indexed but never requested or shown.
A CPU experiment supplies the failed callee through existing symbol/source access
for 594 additional source bytes, while leaving the next bad helper call unseen.
[Portable audit and experiment](../definition-grounding/README.md).

## Scope

Introduce and qualify an opt-in, explicitly versioned failed-call context policy.
Use diagnostic qualified names only as untrusted navigation hints, resolve through
the existing authoritative repository seam, and distinguish ambiguous, partial,
missing and omitted results. Do not infer dynamic receiver bindings from bare names.
Preserve read authority, exact-edit/source identity, finite model turns, source-window
count/byte bounds and tokenizer-enforced context/output budgets. Specify automatic
hint precedence against failure-local and explicitly requested windows; retain clear
omission evidence. Historical profiles and replay semantics remain unchanged.

First exercise CPU regressions for the retained missing definition, generic names,
multiple calls, conflicting names, stale source, incomplete indexes, prohibited
paths, missing read authority and exhausted window/byte budgets. Then freeze fresh
finite paired work with the same model/deployment, original requirements and
independent gates. Preserve all failures and audit accepted results and unchanged
replay. Report missing source supplied separately from repair success; do not claim
that fixing the first call also grounds later calls. No manual candidate repair,
domain-specific prompting, extra retries or default policy upgrade.
