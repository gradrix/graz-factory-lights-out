# Roadmap and release readiness

## Current capability

GFLO is an experimental factory for bounded, independently checked changes. It can
plan tasks against immutable repository snapshots, compile plans under an operator's
policy, advance dependent work through accepted results, and run combined checks.
Workers have bounded context, offline execution, finite retries, development feedback,
and optional exact-edit repair. Findings block reuse of challenged acceptance;
exhausted work retains a review packet.

The same local model has now generated useful changes in ai-gamer and leds-service.
The latter produced a parser fix and six tests, including a reviewed coverage repair.
These are supervised qualifications: Codex selected tasks and prepared independent
checks, and review found weaknesses in generated tests in both domains. They do not
establish unattended whole-product delivery. Historical failures, costs and assistance
are recorded in [evaluation](evaluation.md) and portable development evidence.

## Next priorities

1. Qualify the reusable pytest adequacy gate prospectively across more features.
   It detects supplied faulty module variants; selecting sufficient, meaningful
   variants still needs trusted preparation. Preserve findings and measure first-pass
   acceptance separately from reviewed correction.
2. Qualify repeated features across different real repositories and uncertain
   interfaces. Measure complete feature success, retries, model cost and review
   effort. Planning JSON reliability and source-selection sufficiency remain open.
3. Extend revision-bound navigation with dependency/impact queries and broader
   incremental indexing, guided by a concrete larger feature. Qualify larger isolated
   execution inputs and dependency installation against that workload.
4. Improve fresh-host GPU/model-cache provisioning and verify the documented setup
   on a clean host before calling it turnkey.

Single planning remains the default. The specialist-board comparison used 3.6 times
as many planning tokens without demonstrated quality improvement. Add recursive
management only when measured workloads justify it. See [product intake](product-intake.md).

## Large-repository migration requirement

[ADR 0001](adr/0001-repository-snapshots-and-bounded-task-inputs.md) separates immutable
repository identity, bounded model context, and prepared execution inputs. Snapshots,
text search, revision-bound Python definition lookup, and reuse of unchanged same-path
analysis shards are implemented. Edits preserve unselected files and reject stale
bindings; opaque assets remain in repository snapshots.

Qualify progressively on larger real repositories, measuring selection sufficiency,
index freshness, resource use and repeated whole-feature correctness. Graph storage
is an implementation choice rather than a scheduler dependency. General transitive
invalidation, parallel/nested scheduling, native promotion and larger isolated builds
remain separate requirements. Million-line repository capability is unqualified.

## Potential public release

The repository is public and supports an experimental source preview. Maintained
installation, architecture, operations and evaluation guides live in `docs/`.
Version-controlled `.scratch/` retains handoffs, issues and reproducible fixtures for
work on another machine. Raw runtime artifacts stay in ignored `.gflo/` and require
separate transfer or recreation.

Before a supported release:

- Owner selects a license and confirms attribution requirements.
- Review the exact release source and Git history for private material; excluding
  files from a snapshot does not remove them from earlier history.
- Repeat a clean-checkout install and the GPU demo on the intended release host;
  add automated CPU checks to CI.
- Prepare an audited evaluation evidence bundle with source/profile identities and
  receipts, and verify model-cache provisioning on a fresh GPU host.

The CPU setup helper prepares the demo without a model call. Existing GPU trials
assume provisioned host dependencies and a populated offline model cache. See
[evaluation](evaluation.md) for the scope of completed checks.
