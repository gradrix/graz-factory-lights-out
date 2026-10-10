# Phase 1 — delivery rate on real tasks

Owner: Claude Code coordinator. Decision: [011](../../../docs/decisions/architecture/011-delivery-rate-route.md).

## Acceptance

1. `python-project` profile prepares a real dependency set (first target: `home-lab/services/running-coach`, pytest + pandas + SQLAlchemy) online, then runs its tests offline in the worker sandbox; existing profiles and tests unchanged.
2. Task miner produces validated tasks: hidden fail-to-pass tests fail on the base and pass on the original commit, in the prepared environment.
3. 20 validated tasks from at least two repositories, each with an operator-style objective that names the public interfaces the hidden tests use.
4. Scoring harness runs the factory per task and arm (default reviewer, ensemble reviewer), applies hidden tests to the patch and records delivered / failed / stopped, wall time, attempts and failure category.
5. Result recorded in the run note and summarised in `docs/evidence/autonomy-stages.md`; the phase-2 decision follows from the number.

## Not in scope

Changing worker prompts or models (phase 2), tuning to the mined tasks.
