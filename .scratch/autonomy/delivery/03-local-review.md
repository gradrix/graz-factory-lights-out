# Independent local review and honest acceptance

Status: accepted
Blocked by: none
Owner: /root
Contract source: docs/roadmap.md stage 2; user 2026-10-02 instruction to incrementally implement with 5090 testing and increasingly complex acceptance.

Deliver a fresh-context local read-only reviewer whose structured findings reference source and request repairs. Controller acceptance requires independent executable checks and a complete review; missing, invalid, oversized or unavailable review fails closed. Persist review/repair/recheck evidence. Ambiguous product requirements must produce a useful question and explicit needs-input state rather than invented policy. Pin review requirement into task contract; old accepted runs retain their original scope.

Acceptance: 10 defect candidates and 10 clean controls, all critical seeds caught, at least 8 defects caught, at most 2 false blocks. Compare Flash and dense Qwen under equal request budgets with explicit serialized model switching and measured switching overhead. Then at least 10/12 held-out bounded coding tasks accepted with no critical missed requirement under independent evaluation; separate ambiguous task stops with a useful question. Existing lifecycle/acceptance regressions pass and review → repair → recheck is observed. Evidence remains labeled as a small qualification floor, not large-project reliability.

Candidate: 3bd8ae2; D model trial4346ba5, privacy repairb0342cc, default-profile promotion3bd8ae2
Evidence: D12/12, ambiguity needs_input, independent semantic acceptance with documented minor limitations; reviewer seed gate10/10/all critical/2falseblocks. Unchanged-loop continuity, final nested-privacy recheck and promoted-profile checks passed. Whole59tests88% plus21 affected privacy and8 promoted-image tests. Full links: docs/evidence/autonomy-stages.md.
Execution run: .scratch/.sflo/03-autonomy-review/run.md.
