# Local end-to-end factory

## Destination

Plan an eventually autonomous local software factory: accepted product intent to planned work, prepared environments, implementation, independent verification, repair, integration and a reproducible release or preauthorized deployment. Publish the current minimal implementation and remove the superseded factory files and archive.

## Notes

User direction, 2026-10-02: push the first version, delete previous implementation/docs instead of archiving, and plan local end-to-end autonomy with small reasoning tasks, environment setup, process visibility, logs, search and a headless browser. This turn authorizes cleanup/publication and planning, not implementing all future capabilities or deploying generated products. Current source: this checkout; running copy: MONSTER-GAMING-PC ~/gflo-runtime. Tracker: version-controlled local Markdown, consistent with repository practice. Research uses primary sources. No paid/cloud inference fallback.

## Decisions so far

- [First release evidence](../../docs/pilot-results.md): bounded execution/recovery works; semantic review caught defects executable checks missed.
- [Current architecture](../../docs/architecture.md): keep the small runtime as the implementation baseline.
- [Autonomous delivery](../../docs/decisions/product/002-autonomous-delivery.md): user-approved destination and deletion/publication supersede first-release-only limits.
- [Measured capability route](../../docs/decisions/architecture/003-autonomy-route.md): agent-proposed stages and qualification gates; engineering feasibility is distinct from model reliability.

## Not yet specified

Model reliability across unfamiliar larger projects; useful task/context sizes; review false-negative rates; acceptable unattended throughput. These need experiments rather than promises.

## Out of scope

Implementing the entire roadmap this turn, cloud LLM dependence, rewriting Git history, production/external-account writes without a preauthorized target, and claiming universal large-project autonomy.

[Delivery map](delivery.md)
