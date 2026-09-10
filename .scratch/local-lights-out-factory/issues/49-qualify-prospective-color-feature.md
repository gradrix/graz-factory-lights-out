# Qualify a prospective hex-color parser feature with generated faults

Type: task
Status: resolved

## Frozen scope

Use leds-service merged baseline 9ab0926a9c693d6972aadd3fc009593ed1c3c88a.
Color.fromHex accepts exactly six ASCII hex digits, optionally preceded by one #,
after surrounding whitespace is removed; preserve case-insensitivity. All other
inputs including nonstrings return a new white Color. Preserve stored r/g/b values,
toRGB channel order, constructor and generateRandom. Add at least six pytest cases.

Prepare an independent reference implementation and oracle, automatically generate
and sandbox-qualify faults, then freeze implementation, test and integration gates
before any model call. Keep model, prompt protocol and budgets unchanged. Record
planning failures, worker retries and any intervention; do not call this unaided
specification discovery. Publish useful target change only after independent review.

## Answer

Merged [leds-service PR 11](https://github.com/gradrix/leds-service/pull/11) at
d02622a865333d3044859aba22ffdc4303b188b1. Local model wrote implementation and all 11
new tests. All 17 target tests pass; independent oracle and generated-fault gates
pass; 85 other original files are unchanged; replay makes no model calls.

First build halted with test repair-protocol failures. Reference qualification also
hid mutation crashes because inputs were combined in one test. Split reference cases,
excluded the additional crashing mutant and ran a separate frozen-policy build with
same instructions/model/budgets. Planner and implementation retried automatically;
tests passed first response without reviewer source edits. Both builds retained in
[campaign results](../leds-color-campaign-results.json); [delivery results](../leds-color-results.json)
record final verification. This is supervised qualification, not unattended success.

Added a regression showing mixed assertion/runtime errors across separate tests must
not qualify a faulty variant. All 15 adequacy tests pass; ruff/mypy and portable fixture
reconstruction pass. No factory runtime changes. Next improve protocol reliability
and reference coverage; keep all failed evidence and unchanged model constraint.
