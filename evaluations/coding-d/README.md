# Conditional coding qualification cohort D

This is an unused, independently prepared twelve-task small-project qualification set for a future corrected runtime candidate. It does not replace cohort C or revise any prior result. No target coding/reviewer model run informed these fixtures, references, acceptance checks or control expectations. A separate refund-policy ambiguity is outside the twelve-task denominator and must yield a useful business question and needs_input.

The tasks cover contact import, HTTP reporting, environment templates, SQLite warehouse adjustments, release digests, backup retention, webhook authentication, Markdown catalogs, invoice exports, service readiness, support redaction and artifact selection. Each source is a clean committed repository with domain.py, api.py and cli.py, preserving a useful existing action while requiring new behavior through API and CLI. Task shapes, bounds, JSON types, ordering, errors and atomicity are explicit. Three attempts, 24 turns per attempt, 900 seconds per task remain frozen; ops/qualify_coding.py enforces the wall budget.

## Environment and isolation

Approved image: sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc. Its actual runtime was queried and confirmed as CPython 3.12.13. Validation uses that image offline, with read-only source/acceptance mounts and a temporary /tmp filesystem. No GPU, model endpoint, external service or production database is used. SQLite cases create private disposable databases under /tmp.

Only task objective and source enter target coder context. Acceptance, private references, build/validation scripts and validation outcomes remain outside coder and reviewer contexts. Stage fresh workspaces for every run. The private JSON reference maps are implementation witnesses and must not be disclosed as hints. Each reference must pass; each baseline must fail because the requested action is missing after retained behavior checks.

## Evidence and limits

Private validation records include 12 baseline failures, 12 reference passes, 12 missing-test rejections, 12 failing-test rejections and 12 unchanged-documentation rejections. Checks use recursive strict JSON type/value equality, so bool/int substitutions are rejected. They exercise API, decoded CLI, retained behavior, immutability, domain boundaries, specified errors and SQLite persistence/rollback. Support redaction additionally checks mutable-container aliasing. Three passing discoverable unittest methods and new README usage are required.

Executable checks cannot prove test meaningfulness, full documentation quality, timing-safe HMAC use or universal correctness. Independent semantic review remains required. Finite task checks and this small qualification floor do not establish large-project reliability. Environment compatibility alone is not model qualification.

manifest.json binds every non-Git file, every source commit, budgets, actual runtime metadata and preparation provenance. MANIFEST.sha256 binds the manifest. Freeze before any target-model exposure; later corrections create a new version and retain the original set and evidence. Independent QA should audit before exposure.
