# Role-ensemble executable review qualifies on a fresh holdout

Status: accepted direction, 2026-10-08. Decision makers: user chose the per-requirement route and asked for maximum autonomy, scalability and robustness, with tokens, time and many role agents treated as free (2026-10-07); the design and this record are agent-authored under that direction.

Adopt the role-ensemble design as the qualified approach for local executable review, still as an isolated prototype. It is the first design to find the known README defect (k04) that every earlier single-model variant missed, and the first to pass an untuned holdout.

## Design

Per case, all local on the RTX5090 with the unchanged flash-next-coder 96K/Q4 one-slot service:

1. Deterministic evidence battery: project tests from a writable copy of the root; every documented shell command run in one session per block with project-path substitution, documented versus actual output and exit recorded.
2. Three role explorers on the unchanged sandboxed exploration loop (requirement tester, adversarial edge-case hunter, documentation verifier); their verdicts are advisory, their attested commands become evidence.
3. One union catalog of attested commands, each command's output segments nested under it.
4. Objective split mechanically into sentence statements, grouped into units of up to 400 characters.
5. Per unit: auditors classify every command (supports / contradicts / unrelated) in chunks of 8 commands; a prosecutor seeks a grounded blocking violation; a judge decides when either raises one, from controller-expanded exact excerpts.
6. Fail-closed robustness: reasoning tokens metered per request; an exhausted role gets one fresh attempt at 3x the cap; a rejected answer gets up to two fresh attempts quoting the controller's exact rejection; anything else leaves the unit, and so the case, incomplete. Every decision is recomputed from durable files before acceptance.

## Evidence

Review cohort 2 (16 cases): the four cohort-1 known cases plus twelve coding-d reference projects, six with one seeded objective violation verified by private acceptance checks. Dev went 4/8 → 7/8 → 8/8 over two repairs found on dev only (auditor citation format; auditor workload). The frozen candidate then scored the holdout once: 8/8, every seeded defect cited at its exact line with captured observations, no blocking finding on any control. Cost: 17–31 minutes per case and roughly 0.4M tokens per case.

## Limits and remaining assumptions

- 16 cases, one run each: a qualification signal, not a reliability estimate. Seeds were written by the same agent that designed the pipeline; holdout-once scoring limits but does not remove that bias.
- The judge ruled inconsistently on a test-coverage requirement (d09 flagged, identical-shape controls not). This is the main false-repair risk.
- Defect types covered: CLI error contract, deduplication order, tie-break, documentation invocation, output ordering, input mutation, test-path and README-example defects. Not covered: performance, security, multi-file architectural requirements, non-Python stacks.
- Throughput is bound by one serving slot; units are independent and could run in parallel with more slots, which is a separate serving decision.

## Consequences

Next steps, each needing its own contract: a broader fresh qualification (more defect classes, projects and repeated runs for stability), a consistency mechanism for requirement interpretation (e.g. independent judges with agreement), and only then a maintained-factory integration unit. Maintained runtime 92deaab is unchanged.

Evidence: [run record](../../../.scratch/.sflo/09-autonomy-review-ensemble/run.md), [contract](../../../.scratch/.sflo/09-autonomy-review-ensemble/contract.md), predecessors [units](../../../.scratch/.sflo/09-autonomy-review-units/run.md) and [evidence finalization](../../../.scratch/.sflo/09-autonomy-review-evidence/run.md). Prototype `prototype/review-evidence-20261004` at 80b4956; fixtures 2f5eae7.
