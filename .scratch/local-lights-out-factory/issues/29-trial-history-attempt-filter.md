# Qualify an attempt filter on GFLO history

Type: task
Status: resolved

## Scope

Add `gflo history ATOM --attempt N` for a positive, one-based attempt ordinal.
Default text/JSON output remains unchanged. Filter only the displayed attempts;
retain task status, accepted candidate identity, baseline, and acceptance findings.
Missing or invalid ordinals fail clearly. All existing history integrity checks
must still run before filtering, including evidence in unselected attempts.

Use an isolated source snapshot, a pinned offline dependency image, independent
CLI tests, and bounded local workers. Writable scope is CLI presentation only;
no ledger, acceptance, sandbox, or scheduling changes. Observe all attempts and
retain failed runs. Review generated code and run regression checks before applying
it to the development tree. Do not automatically merge or publish the candidate.

## Observations

Saved previous qualification work in local commit `3cdd83e` and created an isolated
checkout at `.gflo/self-trial-checkout`. Added a CPython 3.11/Linux x86-64 wheel-hash
lock and offline-built dependency image, pinned by local image SHA-256. Broker
restrictions and the default image are unchanged.

The first frozen trial quarantined after two attempts: worker guessed the wrong
history field, then corrected it but omitted rejection of an unmatched ordinal.
A separate trial adds the exact provider result shape and explicit missing-ordinal
behavior to the objective. Gates remain unchanged. First accepted run used its
retry after a redundant read request; second accepted on its first attempt.

The complete repository source plus tests exceeds the existing 256-KiB bundle
limit. Trial includes all runtime source plus relevant tests; regression review
uses bounded bundles per test module rather than raising policy limits.

## Answer

Trial complete: explicit-contract campaign accepted 3/3 fresh runs in five attempts.
Every candidate passed 279 tests and 25 subtests in bounded containers (eight optional
Docker tests skipped). Selected candidate also passed lint and mypy. Initial failed
campaign remains quarantined, not rescored. Two repeated-file reads consumed
initial attempts in the successful campaign; retry bounds remained unchanged.

Selected minimal candidate is committed as `091654a` on local branch
`trial/history-attempt-filter`, based on `3cdd83e`. It adds 19 CLI lines plus
independent tests and usage documentation. Main CLI remains unchanged. Ready for
human review before merging, as agreed for supervised self-modification. No push.
See [portable evidence](../self-history-trial-results.json). Broker qualification
follow-up is [issue 30](30-diagnose-memory-qualification-halts.md).

Owner authorized merge and push. Feature merged into main at `0d30d48` and pushed.
