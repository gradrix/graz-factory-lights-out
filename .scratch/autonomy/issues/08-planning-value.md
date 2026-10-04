# Does a small local plan improve complete increments?

Type: prototype
Status: resolved; keep planning advisory
Blocked by: none; four-arm experiment and independent checks complete
Owner: /root coordinator

Question: does a local planner plus two serial worker assignments improve delivery of a realistic multi-file increment, compared with one direct assignment under the same request and wall-time ceilings?

The user wants progressively autonomous, modular local work with acceptance and repair. Agent chooses a two-case disposable comparison before adding permanent parent-plan state. [Route](../planning-prototype-route.md) refines the larger [planning frontier](../planning-frontier.md). This is not Stage5 acceptance or a claim that decomposition is superior.

Mechanism is quarantined in worktree `/home/gradrix/repos/gflo-planning-prototype`, branch `prototype/planning-pilot-20261004`, based on accepted `c81429b` (runtime92deaab). It imports the existing Factory/worker/reviewer; maintained product files stay unchanged. Main retains the contract, evidence, result and branch pointer. [Experiment delivery](../delivery/08-planning-pilot.md) binds execution.

Two independently authored fresh increments, frozen baseline/reference controls and full acceptance are required. Four arms alternate order. Each uses one shared request/deadline pool; planning, review and clarification consume it. Two-task handoff copies an accepted full workspace to a verified private checkpoint. No original-repository writeback, parent resume, arbitrary DAG or automatic conflict resolution is claimed.

Decision follows complete outcomes, missed requirements, interventions and costs. A zero-benefit or failed result is retained. Shared durable budget support may be useful independently; permanent planning structure must earn its scope from evidence.

## Resolution

[Decision008](../../../docs/decisions/architecture/008-planning-pilot-outcome.md) retains direct execution. Two-task planning added manifest overhead and neither API approach finished within the fixed budget; both manifest Factory passes missed A6. [Completed evidence](../../.sflo/08-autonomy-planning-pilot/acceptance.md). Next [question09](09-executable-review.md) tests executable local review; no permanent parent framework is justified.
