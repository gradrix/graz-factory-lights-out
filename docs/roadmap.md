# Roadmap and release readiness

## Next qualification workload

Build a small Python inventory/reservation application with a shared domain library,
a JSON command-line interface, and a reporting consumer. Use SQLite persistence and
the standard library so the first experiment fits the existing Python broker.
This is a proposed reference workload, not an implemented application.

It tests coupled changes and state transitions while giving us clear independent
oracles: stock never becomes negative, a request ID reserves at most once, failed
operations leave state unchanged, and cancelling twice cannot inflate stock.

### 1. Close the semantic validation gap

Keep the original evaluation score frozen. Expand gates using repeated identifiers,
equivalent values, boundary inputs, and seeded faulty implementations. Investigate
the unresolved version-sort repair with a bounded comparison of reasoning-enabled
inference and smaller repair tasks. This requires an explicit new model profile;
current client requests disable thinking. Record all attempts and costs separately.

Exit: both known faulty candidates fail, reference implementations pass, repair
results are independently checked, and a fresh qualification campaign has zero
discovered false acceptances. If this fails, continue validation/repair work rather
than scaling the workload or relaxing the criterion.

### 2. Qualify a three-module slice

Prepare one domain provider, one CLI consumer, and one report consumer from a common
base. Freeze public contracts and independent integration gates before inference.
Exercise one provider API change and both consumer migrations. Reuse the current
prepared integration mechanism; do not assume it can schedule the product itself.

Exit: all three accepted contributions compose correctly, a stale consumer is
rejected, restart preserves history, and a later child finding blocks reuse.

### 3. Run the stateful application campaign

Prepare ten bounded changes in these dependency waves:

| Wave | Prepared changes | Independent checks |
| --- | --- | --- |
| A | Stock value rules; SQLite repository; reservation transitions | Invalid quantities, rollback, reopen persistence |
| B | Idempotent request handling; cancellation; JSON CLI | Replayed requests, double cancellation, malformed input |
| C | Availability report; audit export | Agreement with authoritative state, stable ordering |
| D | Provider API revision; both-consumer migration as one bounded change | Old consumers rejected, full end-to-end workflow |

Each wave uses one immutable common base for its contributions. Until nested
integration and promotion exist, the trusted harness explicitly prepares the next
base from a verified combined artifact and records that provenance. Model-generated
code does not choose its own acceptance gates. Persistence checks launch multiple
application processes within a gate's isolated workspace; they require no host mounts.

Freeze ten contracts, reference solutions, hidden gates, and faulty variants before
scoring. Run three fresh repetitions with at most three attempts per atom (90 total),
8K/2K routine context/output budgets, and separate cumulative cost reporting. Any
budget change starts a new campaign. Require all end-to-end invariants, no discovered
false acceptances, and verified recovery. Report task success and whole-application
success separately; a partial application is not a successful build.

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
