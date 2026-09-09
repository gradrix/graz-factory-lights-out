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

## Next: choose a representative repository

Choose an existing Python repository and a concrete multi-module feature or API
migration with owner-defined acceptance criteria. Start with a bounded slice that
fits the current standard-library broker and 100-file/256-KiB source-bundle limit.
A dependency-heavy or larger target first requires explicit dependency provisioning
and source-selection work; do not silently raise those limits.

Prepare the task graph and provider contracts, independent per-task gates, and
whole-feature checks before model work. Split workers where ownership and validation
are independent; retain combined checks at shared interfaces. Measure complete
feature success, retries, cost, and discovered false acceptances across repetitions.

Remaining architectural work includes transitive invalidation across evolving bases,
native graph scheduling and promotion, larger-source navigation, and supported
third-party build dependencies. Prioritize these against the chosen repository.
The reference workload does not establish huge-system reliability.

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

Before publication:

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

Publication, remote pushes, and repository visibility changes are separate owner
actions. No release or larger-build qualification is implied by this cleanup.
