# Independent local review and honest acceptance

Status: active
Blocked by: none; frozen cohort C-v2 running on the rig
Owner: /root
Contract source: docs/roadmap.md stage 2; user 2026-10-02 instruction to incrementally implement with 5090 testing and increasingly complex acceptance.

Deliver a fresh-context local read-only reviewer whose structured findings reference source and request repairs. Controller acceptance requires independent executable checks and a complete review; missing, invalid, oversized or unavailable review fails closed. Persist review/repair/recheck evidence. Ambiguous product requirements must produce a useful question and explicit needs-input state rather than invented policy. Pin review requirement into task contract; old accepted runs retain their original scope.

Acceptance: 10 defect candidates and 10 clean controls, all critical seeds caught, at least 8 defects caught, at most 2 false blocks. Compare Flash and dense Qwen under equal request budgets with explicit serialized model switching and measured switching overhead. Then at least 10/12 held-out bounded coding tasks accepted with no critical missed requirement under independent evaluation; separate ambiguous task stops with a useful question. Existing lifecycle/acceptance regressions pass and review → repair → recheck is observed. Evidence remains labeled as a small qualification floor, not large-project reliability.

Candidate: c17821c; current rig source hashes match
Evidence: execution record links controller QA, Flash/dense comparison, preserved cohortA7/12, cohortB11/12 raw /9 without known gaps, correct ambiguity stop, and current-candidate real repair success. Resumed independent controller and remaining B semantic QA passed. Frozen cohort C-v2 is running; final cohort semantic evaluation is pending. Stage unaccepted.
Execution run: .scratch/.sflo/03-autonomy-review/run.md.
