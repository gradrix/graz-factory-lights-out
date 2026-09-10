# Qualify bounded reasoning for window repair

Type: task
Status: ready-for-agent
Blocked by: 65

## Evidence

Atomic-moves-v2 failed all three complete builds. With failure-local draft windows,
v4 accepted one of three. Remaining test workers retained incorrect assumptions about
SQLite foreign-key enforcement or per-batch indices despite diagnostics and available
source. Context availability alone did not establish reliable semantic repair.

The earlier explicit low-effort reasoning escalation qualified 23/24 bounded runs
(issue 27), but the current window profile always disables thinking. Do not conflate
that older workload with this stateful feature or claim the new failure proves a fix.

## Scope

Add an explicitly prepared window-worker reasoning/escalation profile, keeping existing
profiles and historical replay unchanged. Preserve exact-window editing, task-created
file replacement, diagnostic context, original requirement authority and finite retries.
Use the same pinned model/deployment. Bind reasoning effort and output reservation to
wire evidence; qualify a finite larger output allowance if needed, with reliability
primary and token cost secondary. No silent policy upgrade or attempt reset.

Freeze a comparison on the atomic-moves feature and retained repair cases. Reuse all
source, requirements, gates and held-out commit checks; do not add SQLite-specific
prompt instructions or manually fix candidates. Preflight budgets and request fields,
then report every acceptance, failure, intervention and post-audit result. A small
qualification cannot establish a general model/profile ranking.
