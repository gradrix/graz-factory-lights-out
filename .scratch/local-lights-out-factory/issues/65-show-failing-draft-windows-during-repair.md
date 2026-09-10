# Show failing draft windows during repair

Type: task
Status: resolved

## Evidence

Atomic-moves-v2 trial-1 and trial-2 test workers each exhausted six responses. All
repair views contained zero windows from their newly created test file; reviewed
initial context paths named only original inputs. Diagnostics contained failure
locations, and the worker repeatedly replaced entire drafts. The first trial's
incorrect cross-batch index expectation remained despite visible actual/expected
diagnostics. Missing source context is confirmed, but is not proven to be the sole
cause of that semantic failure.

## Scope

For window workers, derive at most two bounded context requests from retained failure
file/line references. Treat references as untrusted navigation hints: permit only
current readable source, reject outside/prohibited/missing/out-of-range paths, and
preserve exact draft identity and range-bound edit authority. Keep 12,000 source bytes,
eight windows, explicit requested-window priority and all existing turn/attempt limits.
Other profiles remain unchanged. No task names or expected answers in runtime prompts.

Test a failing new-file draft, normal traceback formats, scope and budget boundaries.
After the frozen v2 trials finish, repeat the same three policies on fresh ledgers,
retaining earlier failures. Qualify full real-SQLite gates, commit-time held-out checks,
existing winner tests, and historical factory replay.

## Answer

Window views now select at most two 25-line windows from current draft locations in
retained diagnostics. Relative paths must already be readable and line numbers valid;
no new permissions, turns, attempts or byte budget. Explicit reads retain priority;
eight-window omissions are explicit. Five regression cases cover exact draft repair,
traceback formats, escaped output, scope and combined context limits.

Full factory suite: 508 tests/25 subtests; ruff/mypy and historical replay pass.
The retained failed turn now exposes its assertion without inference or ledger changes.
Three identical fresh GPU policies accepted 1/3 versus baseline 0/3. The other two still
failed semantic assumptions despite visible source, so this is a context availability
fix, not a demonstrated general reasoning fix. [All evidence](../atomic-moves/README.md).
Next: issue 66, explicitly bounded reasoning for window repair on the same model.
