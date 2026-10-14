# 13 — Objective-derived checks (prototype)

Owner: Claude Code coordinator. Decision: [015](../../../docs/decisions/architecture/015-objective-checks.md). User go-ahead 2026-10-14 (route option 3 after phase 4).

## Acceptance

- A generator task writes checks from the objective alone and is accepted only if they are new check files that all fail on the base (`ops/delivery/objective_check.py`, `ops/delivery/objcheck.py build`).
- Check sets for the phase 1 and phase 4 objectives are scored on base, reference and every accepted delivered tree (`objcheck.py evaluate`). The run note records catch rate, false-reject rate, wrong checks, generator rate and time.

## State

- 2026-10-14: tooling at ec432b8 (`tests/test_objcheck.py`); smoke run accepted.
- 2026-10-14: measured. 11/20 generators accepted; 3 of 4 covered false accepts caught (3/7 overall); 8/9 correct deliveries pass; 3 of 11 sets hold wrong checks. Not a hard gate (decision 015). Unit closed. Round 2 (repair feedback plus a human-review flag, opt-in) deferred by maintenance mode (decision 016).
