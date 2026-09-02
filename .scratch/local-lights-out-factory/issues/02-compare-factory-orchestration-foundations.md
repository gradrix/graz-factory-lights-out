# Compare factory orchestration foundations

Type: research
Status: resolved
Assignee: orchestration_foundations
Blocked by:

## Question

Which reusable mechanisms, contracts, and limitations in SFLO, Gas City, and other primary-source autonomous coding systems are relevant to a fully local Factory, and should the plan adapt an existing foundation, compose several, or build a minimal purpose-specific core?

## Comments

### Resolution

Build a minimal purpose-specific orchestration core rather than adopting SFLO
or Gas City wholesale. Carry forward Gas City's materialized durable DAG,
append-attempt retry, reconciliation, event, and provider contracts; layer
SFLO's artifact-producing product gates and bounded review/escalation policy on
top as versioned workflow profiles. Use an existing coding-agent harness only
behind a replaceable WorkerRuntime boundary. The first local core should use a
single inference admission token, SQLite plus hashed artifacts as the durable
authority, isolated attempt workspaces, and deterministic evidence as gate
truth. Preserve an adapter seam for later Gas City integration if fleet/multi-
project operations become necessary.

Report: [Orchestration foundations for a local lights-out software factory](../research/orchestration-foundations.md)
