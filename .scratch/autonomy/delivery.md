# Local autonomy delivery

## Current turn

- [Clean and publish baseline plus autonomy plan](delivery/01-publish-plan.md) — accepted; published as b9d3765.

## Next implementation frontier

- [Observe and control one local run](delivery/02-visibility.md) — accepted; candidate 18a274f, real rig and independent QA evidence linked.

Later acceptance-bearing stages are in [the roadmap](../../docs/roadmap.md). They remain progressively specified plans, not a pile of preclaimed implementation tickets. No automatic production deployment or external-account action is authorized here.

- [Independent local review](delivery/03-local-review.md) — accepted at3bd8ae2; D12/12 plus ambiguity and independent QA, with documented quality limitations.

- [Prepare supported environments](delivery/04-environments.md) — accepted; runtime25f75c3 and96K/Q4 manager8fdde15. Three profile paths passed executable/local-review/independent semantic checks; original failed cohort is preserved. See the [acceptance record](../.sflo/04-autonomy-environments/acceptance.md).

- [Approved document evidence](delivery/05-document-evidence.md) — accepted at2049361; first Stage4 slice, two actual local answers and offline replay independently verified.

- [Supervised local browser checks](delivery/06-local-browser.md) — accepted at596ecb6; five actual-rig journeys, independent boundary/recovery checks, installed browser support. [Acceptance](../.sflo/06-autonomy-browser/acceptance.md).

- [Document extraction and bounded citation repair](delivery/07-document-reliability.md) — accepted at92deaab and installed;10/10repeats+3/3fresh,25cross-versionreplay checks. Exact-quote8/10failure preserved. [Acceptance](../.sflo/07-autonomy-document-references/acceptance.md).

- [Direct versus two-task planning pilot](delivery/08-planning-pilot.md) — accepted discovery; four arms and independent checks complete, no independently complete increment. Planning stays advisory; [closure](../.sflo/08-autonomy-planning-pilot/acceptance.md).

- [Read-only executable local-review discriminator](delivery/09-executable-review.md) — role ensemble qualified (80b4956, 8/8 + 8/8); consistency candidate 6920218 passed gate 1 16/16 grounded and blind run 1 24/24 grounded on an independent cohort; blind run 2 pending. [Qualification](../.sflo/09-autonomy-review-qualification/run.md).

- Maintained ensemble review integration — opt-in `gflo/ensemble.py` on branch `integration/ensemble-review`; offline controls 12/12 and 40/40 replay equivalence; awaiting blind run 2, rig suite and rig vertical before merge. Contract and run record on that branch under `.scratch/.sflo/10-autonomy-ensemble-integration/`.
