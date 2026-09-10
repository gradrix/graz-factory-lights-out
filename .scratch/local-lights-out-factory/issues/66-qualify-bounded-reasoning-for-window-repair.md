# Qualify bounded reasoning for window repair

Type: task
Status: resolved
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

## Answer

Added explicit `vllm-python-worker-windows-reasoning-low-v1` with low reasoning on every
worker turn, matching tokenizer/generation settings and caller-reviewed reservations.
Planning remains non-reasoning; existing profiles, gates and replay remain unchanged.

Frozen equal-budget comparison: full features control 0/3 versus reasoning 1/3;
retained repairs 0/2 in both. The accepted feature passed held-out commit recovery
and unchanged replay. All wire/budget audits passed. [Portable evidence](../window-reasoning/README.md)
contains every result and reproducing inputs. This does not justify a default upgrade.
Reasoning-only output truncation exposed a confirmed decoder failure; issue 67 handles
it separately without changing these results or resetting historical attempts.
