# Roadmap and release readiness

## Completed scoped qualifications

The low-effort escalation profile verified 23/24 small task runs. A three-module
inventory migration passed independent integration, stale-input, restart, and
finding checks. A subsequent stateful campaign built an eight-module SQLite
inventory application through ten prepared changes, three times: all 30 tasks
accepted in 32 attempts. Each build passed six supplemental workflows and three
additional boundary workflows. The trusted harness advanced immutable accepted
bases sequentially; autonomous planning and native promotion were not exercised.

Earlier stateful campaigns failed and remain recorded separately. Clearer interface
instructions and bounded observed-error feedback preceded the successful campaign;
this combined trial does not isolate their individual contribution. The original
120-run campaign score and its false-acceptance findings remain unchanged.

## Current: supervised GFLO self-trial

A bounded history-filter feature was trialled on GFLO itself. An explicit provider
result contract led to three accepted runs; every candidate passed 279 tests and
25 subtests in bounded batches. The selected change was merged after owner approval.
This is one feature repeated, not a broad repository benchmark.

The trusted dependency-image recipe is documented in [infra/worker](../infra/worker/README.md).
Workers remain offline and restricted. Full repository tests required bounded
batches under the existing 256-KiB limit. Next engineering investigation is an
intermittent memory-qualification halt; retain strict controls while diagnosing it.

Snapshot-backed planning and reviewed feature progression now run a bounded graph
through accepted providers, consumers, and independent combined checks. An expense
report feature passed three executions: 12 tasks accepted in 12 attempts, with
omitted source preserved and no model calls on replay. The planner's ambiguity probe
initially failed; a direct clarification result and explicit response instructions
then produced blocking product questions. All stages remain recorded.

Next qualify different products, uncertain interfaces, and manager escalation before
recursive delegation. Keep per-task and whole-feature checks independent of model
prose. Measure complete feature success, retries, costs, and discovered false
acceptances across repetitions. See [product intake](product-intake.md).

## Large-repository migration requirement

Large-repository support is an architectural requirement, not an assumed property
of the current bundles. [ADR 0001](adr/0001-repository-snapshots-and-bounded-task-inputs.md)
records the migration: immutable repository identity, bounded context selections,
and separately prepared execution inputs. The first source-access slice is implemented:
immutable snapshots, bounded reads/search/selections, legacy-bundle parity, and
digest-bound edits preserving omitted files. A real 193-file, 1.53-MB GFLO snapshot
yielded a 238-KB execution subset. Reviewed task graphs now use snapshot-bound
preparation and accepted-base progression while preserving historical records.
Larger execution inputs remain future work.

The sequence is snapshot-backed access and text search, revision-bound symbol
lookup, then dependency/impact queries and incremental indexing. Graph storage is
an implementation choice rather than a scheduler dependency. Changes must preserve
unselected files and reject stale source/index bindings. See the concrete
[implementation slice](../.scratch/local-lights-out-factory/issues/32-separate-repository-access-from-task-bundles.md).

Qualify progressively on real repositories, measuring source-selection sufficiency,
index freshness and resource use, model cost, and repeated whole-feature correctness.
A large index alone does not establish large-build reliability. Ancestor findings now block snapshot-worker reuse; general transitive invalidation,
parallel/nested scheduling, native promotion, and larger isolated builds remain
separate requirements. No million-line support is currently implemented.

## Potential public release

The current scope supports an experimental source preview, not a production or
turnkey autonomous factory claim. Public documentation now has installation,
architecture, operations, evaluation, and this single active roadmap. Development
handoffs, issues, and research remain version-controlled in `.scratch/` for portable
continuation. Raw run evidence remains in ignored `.gflo/`. A separate reviewed
public snapshot can omit internal planning history without removing it here.

A clean public working-tree snapshot installed successfully on Python 3.13.5.
Its prepared demo submitted without GPU access; 245 tests and 25 subtests passed,
with eight optional Docker checks skipped. Ruff, mypy, and local Markdown links
also passed. This verifies the CPU onboarding path, not fresh-host GPU setup.

Before a supported release:

- Owner selects a license and confirms attribution requirements.
- Review the exact staged source and Git history for private material. Excluding
  development notes from a snapshot does not erase earlier commits; a clean public repository may
  be preferable to publishing existing history.
- Run a fresh clean-checkout install and the documented GPU demo on the intended
  release environment. Automate CPU checks in CI after selecting the public host.
- Prepare an audited evidence bundle for the published evaluation, with exact
  source/profile identities and enough receipts to verify the summary.
- Document and verify model-cache provisioning on a fresh GPU host. The measured
  profile currently assumes a populated offline cache.

The repository is public; owner-authorized merges and pushes are underway.
Public visibility does not imply a supported release or larger-build qualification.
