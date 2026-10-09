# Local end-to-end factory

## Destination

Plan an eventually autonomous local software factory: accepted product intent to planned work, prepared environments, implementation, independent verification, repair, integration and a reproducible release or preauthorized deployment. Publish the current minimal implementation and remove the superseded factory files and archive.

## Notes

User direction, 2026-10-02: push the first version, delete previous implementation/docs instead of archiving, and plan local end-to-end autonomy with small reasoning tasks, environment setup, process visibility, logs, search and a headless browser. Superseded by user direction on 2026-10-02: proceed with incremental implementation toward self-sufficiency, with testing stages, actual 5090 trials and progressively more complex acceptance. Generated production deployments still need a preauthorized target. Current source: this checkout; running copy: MONSTER-GAMING-PC ~/gflo-runtime. Tracker: version-controlled local Markdown, consistent with repository practice. Research uses primary sources. No paid/cloud inference fallback. Latest user continuation: continue without an arbitrary milestone stop; keep advancing the authorized destination through accepted increments. Runtime resource/recovery bounds remain engineering controls, not a session stopping rule.

## Decisions so far

- [First release evidence](../../docs/pilot-results.md): bounded execution/recovery works; semantic review caught defects executable checks missed.
- [Serving allocation](../../docs/decisions/architecture/002-model-profile.md): 96K/Q4 is the measured faster default; fresh API and TypeScript qualification passed.
- [Current architecture](../../docs/architecture.md): keep the small runtime as the implementation baseline.
- [Autonomous delivery](../../docs/decisions/product/002-autonomous-delivery.md): user-approved destination and deletion/publication supersede first-release-only limits.
- [Measured capability route](../../docs/decisions/architecture/003-autonomy-route.md): agent-proposed stages and qualification gates; engineering feasibility is distinct from model reliability.

- [Owned application browser checks](../../docs/decisions/architecture/005-local-browser-verification.md): one supervised isolated pair with fixed Playwright assertions and bounded evidence; accepted at596ecb6 with actual-rig shared-memory and recovery evidence.

- [Planning pilot outcome](../../docs/decisions/architecture/008-planning-pilot-outcome.md): keep planning advisory; qualify executable verification before adding orchestration.

- [Role-ensemble executable review](../../docs/decisions/architecture/009-role-ensemble-review.md): evidence battery + role explorers + per-unit auditor/prosecutor/judge passed a fresh holdout 8/8; still isolated.

## Not yet specified

[Broader document reliability](issues/07-document-reliability.md) initial exact-quote repair trial failed8/10 on persistent punctuation mismatches. [Bounded source references](../../docs/decisions/architecture/007-bounded-document-references.md) now selects format3 with explicit expansion limits and unchanged old readers; [delivery07](delivery/07-document-reliability.md) is accepted at92deaab and installed. Ten repeated diagnostics and three fresh questions passed independent semantics;25cross-versionoffline checks passed. [Small planning prototype route](planning-prototype-route.md) is resolved by [the actual four-arm pilot](issues/08-planning-value.md): no complete increment and no planning benefit established. [Executable-review discovery](issues/09-executable-review.md) qualified a role ensemble (decision 009); open: broader repeated qualification, judge consistency, maintained integration.

[Seed reader timestamp granularity](issues/10-seed-read-timestamp-granularity.md): rig suite shows same-size mid-read rewrites go undetected on coarse (~4 ms) timestamps; open task, independent of review work.

[Serving throughput under useful context](issues/05-serving-throughput.md) measured a roughly4.5x improvement at96K/Q4 over128K on identical input. Fresh API and TypeScript tasks passed with independent semantic QA. [Approved document evidence](delivery/05-document-evidence.md) is accepted at2049361; [supervised local-browser journeys](delivery/06-local-browser.md) are accepted at596ecb6. [Browser/research route](../../docs/research/research-browser-route.md) informs later work; [Local-browser feasibility](issues/06-local-browser-boundary.md) is measured in an isolated prototype; the accepted browser component remains unchanged in installed runtime92deaab; earlier defects and failed trials remain preserved.

[Local review qualification](issues/02-review-reliability.md) is accepted at3bd8ae2 after target-matched D12/12 plus independent QA; minor quality and reviewer false-positive limitations remain explicit. Model reliability across unfamiliar larger projects; useful task/context sizes; review false-negative rates; acceptable unattended throughput. These need experiments rather than promises. [Environment preparation research](issues/03-environment-preparation.md) is resolved; the three-profile implementation is accepted. [Bounded environment executor](issues/04-environment-build-boundary.md) is resolved toward immutable bases plus dependency snapshots; three profiles are implemented and have passed cold preparation on the rig; lifecycle/input/security and bounded model-task qualification passed.

## Out of scope

Cloud LLM dependence, rewriting Git history, production/external-account writes without a preauthorized target, and claiming universal large-project autonomy.

[Delivery map](delivery.md)
