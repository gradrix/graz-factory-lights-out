# What local autonomy is feasible, and how will we qualify it?

Type: Research
Status: resolved
Blocked by: none

Decision changes: choose a staged architecture/tool route and distinguish engineering capabilities from unproven model reliability. Source: user request 2026-10-02. Research artifact: docs/research/autonomy-feasibility.md. Final decision will live in docs/decisions/architecture/003-autonomy-route.md.

Answer: tool/environment/visibility engineering is feasible; local-model end-to-end reliability remains a qualification question. Adopt docs/research/autonomy-feasibility.md and docs/roadmap.md; lasting decisions are product/002-autonomous-delivery.md and architecture/003-autonomy-route.md. Resolve model reliability through staged held-out trials, not by treating bigger context or more agents as proof.

Researcher consistency review found two gaps, both repaired: external browsing now explicitly requires validated non-root browser sandboxing, and stage 1 cancellation/resume stays in the CLI while the HTTP view is read-only. Review scope was documentary; model measurements come from the local pilot.
