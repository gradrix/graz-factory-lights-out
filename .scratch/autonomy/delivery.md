# Local autonomy delivery

Route: [roadmap](../../docs/roadmap.md), [decision 011](../../docs/decisions/architecture/011-delivery-rate-route.md). Earlier stage units (01–10) are accepted or closed; their records stay under `delivery/` and `.scratch/.sflo/`.

## Frontier

- [Objective-derived checks](delivery/13-objective-checks.md) — measured 2026-10-14: catch 3 of 4 covered false accepts, 8/9 correct deliveries pass, but 11/20 generators produced a set and 3/11 sets hold wrong checks; not a hard gate (decision 015). Next: round 2 as repair feedback plus a review flag (pending user).
- [Phase 4 — queue and integration](delivery/12-queue-integration.md) — measured 2026-10-13: direct and queued tie at 2/6 chains, 3 false accepts each; queue stays opt-in. Route option 3 (objective checks) chosen 2026-10-14, unit 13.
- [Phases 1–3 — delivery rate, worker, test factory](delivery/11-delivery-rate.md) — measured; closed 2026-10-13: overnight third run 1 of 3; large modules are a known limit. Run note: `.scratch/.sflo/11-delivery-rate/run.md`.

- Route check (2026-10-14, user asked whether further development is worth it): agent recommends maintenance mode. Use the factory for small, precisely described changes and moderate test-writing; keep the delivery-rate cohort as a benchmark for new local models; stop building new components (queue, decomposition, objective-check round 2). The unmeasured question is delivery on objectives the user writes before knowing the solution. Pending the user's choice.

## Later

Phase 5 in the roadmap, only after phase 4 shows steady gains.

## Closed

- 01–07 accepted (publication, visibility, local review, environments, document evidence, browser checks, document reliability).
- 08 planning pilot: discovery closed, planning advisory.
- 09 executable review: role ensemble qualified; requalification closed 2026-10-10 (decision 011).
- 10 ensemble integration: merged to `main` as opt-in at Phase 0.
