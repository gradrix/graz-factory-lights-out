# Prioritize requirements over planner implementation advice in repair workers

Type: task
Status: resolved

## Evidence

Issue 53 planner wrote correct wraparound acceptance prose but contradictory min/max
fallback algorithm in interface_contracts. Worker copied that algorithm and returned
five unchanged repairs despite gate failures. Requirements are already supplied in
the task objective; clarify their precedence over planner-generated implementation
advice without weakening required API signatures or validation gates. Retain failed
trial and test a separately prepared replay of the same plan, source and budgets.

## Answer

Instruction-only experiment failed. A fresh ledger reused the same proposal, source,
gates and finite budgets. Worker again returned the wrong clamping algorithm followed
by five unchanged repairs, exhausting six responses/two attempts. No tests/integration.
The tested priority instruction and transport assertion were reverted, leaving factory
runtime unchanged. [Results](../leds-modes-priority-results.json) retain the exact
instruction and failure. Do not reset either quarantined run or count this as success.

Next requires structural separation of planner interface declarations and implementation
advice, with explicit treatment of contradictions. Preserve historical plan digests and
replay; do not retroactively reject old accepted contracts. This is a design/implementation
next step, not a request to change models or loosen validation.
