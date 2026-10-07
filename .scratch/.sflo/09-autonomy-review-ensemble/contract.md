# Role ensemble review with fresh cohort

Decision: user, 2026-10-07 — "sure do new cases.. and also see what is possible to make it more robust. We don't care about tokens or spinning many agents with different system prompts (roles) at the same thing.. Tokens and time are free - this is electricity based solution". Design below is agent-authored under that direction. Predecessor ../09-autonomy-review-units/run.md: trial3 3/4; thinking cap resolved; case04 A6 judged from source while ignoring contradicting captured evidence.

## Fixtures

Review cohort 2 (prototype 2f5eae7, manifest 06b6fc2a…): 16 cases. Dev: k01–k04 (cohort-1 known cases, already used for tuning) and d01, d02, d03, d05. Holdout: d04, d06, d07, d08, d09, d10, d11, d12. d-cases are coding-d reference projects (no model run informed them); six carry one seeded objective violation (d01 CLI traceback, d05 dedupe first-not-last, d06 tie-break, d09 README invocation, d10 unsorted blockers, d12 input mutation), six are unchanged references. Every d-case verified against its private acceptance check in the approved offline image ([verification](../../../../gflo-review-evidence-prototype/evaluations/review-cohort-2/private/verification.txt) in the prototype worktree). The seed author also designs the pipeline; holdout scoring once, without tuning on holdout outcomes, is the guard. Holdout results are reported even if dev passes.

## Pipeline (per case, all on the 5090, sequential on the single slot)

1. Evidence battery (no model): project tests from a writable copy of the root; every fenced documented command executed in one shell session per block with project-path substitution, documented vs actual output and exit recorded.
2. Three role explorers, each the unchanged predecessor exploration loop in its own child with its own ledger/candidate copy: requirement tester, adversarial edge-case hunter, documentation verifier. Per explorer 8 requests, 12 commands, 900 s (780 s exploration), thinking 4096. Roles are generic and derived from objective statements, not from seeds. Explorer verdicts are advisory only.
3. Union catalog of all attested commands with role tag; per-command feedback bounded to head 3 KiB + tail 3 KiB with an explicit controller elision count.
4. Requirement statements: each objective sentence; units group consecutive statements up to 400 characters. The unit wire references statement IDs.
5. Per unit, role requests over a shared cached prefix (common system policy + evidence), role in the trailing assignment: auditor classifies every catalog command as supports/contradicts/unrelated with segment citations (complete coverage enforced); prosecutor searches for a grounded blocking violation; judge is invoked when the auditor marks any contradiction or the prosecutor does not pass, and receives controller-expanded contested excerpts. Unit decision: pass when auditor and prosecutor are clean, otherwise the judge's.
6. Thinking cap 8192, max_tokens 12288 for unit roles; any exhausted, invalid or failed role leaves the unit incomplete. Case aggregation and reverification as in the units contract.

## Acceptance

Dev and holdout scored separately against private expectations: classification and completeness automatically, grounding of every repair finding independently. Target: all cases complete; every seeded defect repaired with a finding on the seeded requirement; every control passes. Report per-split confusion, per-role contribution, and cost. A full holdout pass permits a broader qualification decision only; no maintained promotion.
