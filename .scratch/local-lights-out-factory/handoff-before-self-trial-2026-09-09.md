# GFLO handoff — stateful reference workload qualified

## Current checkpoint — 2026-09-09

User authorized continued implementation and qualification until a concrete blocker
or owner decision. The scoped stateful milestone is complete; next owner decision
is the real repository and feature to qualify. No additional Wayfinder pass needed
for the completed work. Changes are local, not committed or pushed this continuation.

- Low-effort bounded escalation: 23/24 verified tasks; issue 27 resolved.
- Three-module inventory migration: passed combined validation, stale inputs,
  restart replay, and a synthetic finding probe in a separate ledger copy.
- New stateful campaign: three complete ten-step builds, 30 accepted atoms in
  32 attempts / 33 model turns. All final migrations passed first attempt.
- All three builds passed six supplemental and three additional boundary workflows.
- Original rejected migration repaired 3/3 on first attempts, each passing six
  supplemental workflows. Seen-failure checks are not independent held-out evidence.
- Full tests: 266 passed, eight optional Docker skips, 25 subtests; ruff and mypy
  passed. Campaign and supplemental gates ran in Docker.

The fix surfaces bounded observed JSON error fields before truncated logs and
restates the migration's path-based reporting interface. Expected gate outputs
remain private. Both changes were evaluated together, not separately. Keep the
two-file migration in one atom for now; separate workers need independently
checkable contracts and combined integration gates, not voting on correctness.

One resource-qualification halt (exit 137 without Docker OOM flag) was explicitly
resumed under unchanged controls. No worker retry reset. Original failed campaigns
and original 120-run scores/findings remain unchanged. Default model profile is
unchanged. Huge-system capability is not established.

## Continue

Choose a representative real Python repository and an owner-defined feature or
migration. Current broker is standard-library-only with 100 text files / 256 KiB
source bundles. Decide dependency provisioning and source navigation against that
target. Native scheduling/promotion and transitive invalidation across evolving
bases remain architectural work; the successful harness prepares tasks and advances
accepted bases sequentially. See [roadmap](../../docs/roadmap.md).

## Portable evidence and reproduction

[Results and frozen manifest](stateful-inventory-feedback-results.json) retain
identities, costs, candidate hashes, reviews, and limitations. Earlier failure:
[stateful results](stateful-inventory-results.json). Raw `.gflo/` evidence is ignored
and requires separate transfer or reproduction; keep `.scratch/` tracked.

```sh
.venv/bin/python scripts/run_inventory_workload.py --output .gflo/evidence/NEW --slice-result .gflo/evidence/inventory-slice-live-v1/result.json --profile vllm-python-worker-escalating-tools-v1
.venv/bin/python scripts/review_inventory_workload.py --campaign .gflo/evidence/NEW --output .gflo/evidence/NEW-review
.venv/bin/python scripts/recheck_inventory_migration.py --campaign .gflo/evidence/stateful-inventory-tools-v1 --output .gflo/evidence/NEW-repair
```

Successful raw directories: `stateful-inventory-feedback-v1`,
`stateful-boundary-feedback-v1`, and `migration-repair-feedback-v2` under
`.gflo/evidence/`. Repair harness is deliberately bound to the retained rejected
candidate; it does not reset historical quarantine. Earlier handoff preserved in
[checkpoint history](handoff-before-feedback-2026-09-09.md).
