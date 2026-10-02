# Paired repair script fast QA — PASS

Candidate `.gflo/repair-reasoning-probe.py`, SHA256 `2724185d54596ab2af3d4e36cf3fc0c8d37799f3b83f1cc4fed579728e04616b`.

| Check | Result |
|---|---|
| Matched inputs and budgets | Both arms copy/hash the same terminal source and acceptance, retain objective/checks, omit prior failure evidence consistently, use 1 attempt/24 turns/900 seconds/4096 response tokens; order reverses across the two cases |
| Effective coder requests | Mock confirms none versus medium/thinking-enabled/top-level 1024 budget; receipts match actual forwarded body hash/size/profile; caller body unchanged |
| Reviewer | Separate ordinary ModelWorker+Reviewer remains unchanged; receipt correctly describes medium, thinking enabled, top-level 1024, total 4096 |
| Failure evidence | Provider error still records error type/elapsed time; missing verification no longer crashes or reuses prior arm review; valid control records current arm review |
| Isolation/cleanup | Fresh output only; copied repositories; original fingerprints checked; pinned 3.12.13 runtime assertion; alarm around resume; explicit cleanup and stop if cleanup fails |

Both reported defects are closed. Reproduction: `python3 .scratch/.sflo/03-autonomy-review/qa-repair-reasoning-mock.py`; exit 0. Complete probe and output are in `qa-repair-reasoning-mock.py` and `.log` beside this report.

Scope: static inspection plus mocked requests and extracted receipt-path execution; no GPU/network/model calls. Deadline and cleanup were inspected, not fault-injected end to end. Wire receipts establish requested settings; actual server behavior still requires experiment evidence. This is a known-case comparison on a corrected interpreter, not unseen qualification or a controlled comparison with the original 3.11.15 cohort results. Omitting prior failure feedback means it measures rediscovery and repair of retained failed files rather than exact replay of the original repair request.
