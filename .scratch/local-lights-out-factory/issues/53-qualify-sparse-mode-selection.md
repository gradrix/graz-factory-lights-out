# Qualify sparse mode selection with planner and repair targets

Type: task
Status: resolved

## Frozen scope

leds-service baseline d02622a865333d3044859aba22ffdc4303b188b1.
Change only LedProgramRepository.changeMode: registered integer mode IDs may be sparse
and need not include 1. With nonempty programs, None request or None current selects
lowest ID; otherwise an existing request selects itself. For increasing requests,
select smallest registered ID >= request or wrap to lowest. For other requests,
select greatest registered ID <= request or wrap to highest. Empty registry raises
ValueError without changing state. Always update settings.mode on success. Only when
setProgram=True, set currentProgram and initialize it exactly once. Preserve other
methods and program registry; no hardware access.

Generate and qualify faults against isolated parametrized reference cases before
model calls. Require at least six real-method pytest cases, independent original rejection and
qualified-fault rejection. Same model, planner, repair handles and finite budgets.

## Answer

Negative qualification: no accepted implementation or target PR. Planner passed first
response but put a clamping algorithm into interface_contracts, contradicting explicit
wraparound requirements and its own acceptance prose. Worker copied it and made five
unchanged repairs across six responses/two attempts; then quarantined. Tests and
integration never ran. Repair handles were valid throughout.

216 reference cases and two qualified faults were frozen before calls. Initial
preflight found the original cannot be an assertion-only fault because valid activation
cases crash; it was excluded before live scoring and independently rejected by oracle.
Fixture reconstruction passed. [Results](../leds-modes-results.json) preserve failure
and diagnosis; [fixture](../leds-modes-fixture.json) is portable. Issue 54 tested
instruction priority and also failed; no product or factory runtime changes shipped.
