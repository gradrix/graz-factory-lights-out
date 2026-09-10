# Expose remaining model turns to bounded workers

Type: task
Status: resolved

## Observed failure

The ai-gamer test follow-up spent all four turns reading omitted dependencies and
never produced a candidate. The controller enforces the limit, but the worker view
does not include remaining turns or the actual output reserve. Failure traces also
show incomplete output and unnecessary reads; budget visibility is one hypothesis,
not a proven complete repair of test generation.

## Requirement

Project the controller's remaining attempt turns and actual output reserve into the
worker instruction before exact tokenization. State that the current response counts
and a last-turn read leaves no chance to submit a candidate. Preserve finite retry,
context/output and scope limits; retain all historical failures. Verify countdown,
reset on retry and identical tokenization/generation messages. Run a fresh pinned
ai-gamer test follow-up without changing its policy/gates and report failures honestly.

## Answer

Controller projects remaining turns (including current response) and actual output
reserve before exact tokenization. Countdown/retry reset and HTTP message equality
regressions passed; full Docker-enabled suite passed 412 tests and 25 subtests.
Fresh unchanged-policy trial produced two complete candidates instead of exhausting
reads; both failed. Retry repaired private reset misuse but retained a winning board
as a draw. No acceptance or general reliability improvement is claimed. See
[results](../worker-turn-budget-results.json). Next test smaller separate cases.
