# Qualify preauthorized reasoning escalation

Type: task
Status: resolved
Blocked by: 18, 25

## Scope

Add an explicit prepared profile that permits two attempts and one model turn per
attempt: first thinking-disabled with 2K output, then reasoning with 4K output if
retained failure evidence exists. Both use the same 8K context ceiling, source,
contract, and gates. Keep the default unchanged. Preserve existing infrastructure
halt/resume behavior and ledger fencing; restarts must not reset the allowance.

Qualify the profile across implementation, defect repair, consumer migration, and
test generation. Freeze gates, reference programs, faulty variants, and numerical
criteria before scoring. Record all failed attempts and supplemental review. This
is a bounded progression check, not evidence of huge-system capability.

## Completion criteria

- Wire-level tests bind tokenization and generation to the selected attempt policy.
- Invalid budgets/turn allowances fail before submission; retry/restart cannot add attempts.
- Historical default RunPlans remain valid and unchanged.
- Fresh multi-class campaign and independent semantic checks are reported honestly.

## Answer

Explicit escalating profiles preserve the two-attempt allowance and existing
request/ledger authority. The pinned template defaults to xhigh reasoning; that
variant failed its campaign threshold. Explicit low effort qualified 23/24 runs
across four classes, with zero discovered false acceptances and 32 attempts.
Evidence: `.gflo/evidence/escalation-qualification-low-v1/`. The subsequent
three-module inventory slice also passed all product and reuse checks.
Default policy remains unchanged; these are scoped qualifications.
