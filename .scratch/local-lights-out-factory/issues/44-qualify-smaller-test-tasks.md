# Qualify smaller independent ai-gamer test tasks

Type: task
Status: resolved

## Evidence and experiment

Issue 43 supplied two complete candidates, but the worker failed to recognize a
winning diagonal in a purported draw. Split the test feature into four independently
writable files (gaps, anti-diagonals, rectangular directions, draw potential). Keep
the accepted implementation immutable and reuse the original final winner oracle
and original-baseline rejection condition. Each worker must produce at least one
passing test; combined tests must reject the original with two assertion failures.

This is a supervised decomposition follow-up on a seen problem, not a new held-out
success score. Give the two already-observed bug coordinates in the requirements.
Use short pytest failure traces so every error fits feedback. No new model, increased
per-worker budget or relaxed checks. Retain all preceding failures.

## Answer

The four-task decomposition did not pass. Gap and anti-diagonal tasks each accepted
on the first attempt. Draw-potential task first supplied a winning board as a draw;
its retry returned an incomplete response and quarantined. Rectangular task was never
reached; final integration was not run. Per-worker limits remained 12K/4K, two
attempts, three turns. See [results](../ai-gamer-split-tests-results.json) and
[fixture](../ai-gamer-split-tests-fixture.json).

This is a negative qualification result. Smaller tasks improved the completed prefix,
but did not establish reliable semantic test generation or unattended delivery.
Current blocker: correction of an invalid generated test fixture within bounded
output/retries. Do not broaden the autonomy claim or discard this trial. A future
repair-protocol/model comparison must be prospective, fixed-budget and separately
scored; supplying the correct board would change what is being measured.
