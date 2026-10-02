# Local end-to-end factory

## Destination

Plan an eventually autonomous local software factory: accepted product intent to planned work, prepared environments, implementation, independent verification, repair, integration and a reproducible release or preauthorized deployment. Publish the current minimal implementation and remove the superseded factory files and archive.

## Notes

User direction, 2026-10-02: push the first version, delete previous implementation/docs instead of archiving, and plan local end-to-end autonomy with small reasoning tasks, environment setup, process visibility, logs, search and a headless browser. Superseded by user direction on 2026-10-02: proceed with incremental implementation toward self-sufficiency, with testing stages, actual 5090 trials and progressively more complex acceptance. Generated production deployments still need a preauthorized target. Current source: this checkout; running copy: MONSTER-GAMING-PC ~/gflo-runtime. Tracker: version-controlled local Markdown, consistent with repository practice. Research uses primary sources. No paid/cloud inference fallback.

## Decisions so far

- [First release evidence](../../docs/pilot-results.md): bounded execution/recovery works; semantic review caught defects executable checks missed.
- [Current architecture](../../docs/architecture.md): keep the small runtime as the implementation baseline.
- [Autonomous delivery](../../docs/decisions/product/002-autonomous-delivery.md): user-approved destination and deletion/publication supersede first-release-only limits.
- [Measured capability route](../../docs/decisions/architecture/003-autonomy-route.md): agent-proposed stages and qualification gates; engineering feasibility is distinct from model reliability.

## Not yet specified

[Local review qualification](issues/02-review-reliability.md) is accepted at3bd8ae2 after target-matched D12/12 plus independent QA; minor quality and reviewer false-positive limitations remain explicit. Model reliability across unfamiliar larger projects; useful task/context sizes; review false-negative rates; acceptable unattended throughput. These need experiments rather than promises. [Environment preparation research](issues/03-environment-preparation.md) is resolved; implementation is now the active frontier. [Bounded environment executor](issues/04-environment-build-boundary.md) is resolved toward immutable bases plus dependency snapshots; actual preparation remains unimplemented.

## Out of scope

Cloud LLM dependence, rewriting Git history, production/external-account writes without a preauthorized target, and claiming universal large-project autonomy.

[Delivery map](delivery.md)
