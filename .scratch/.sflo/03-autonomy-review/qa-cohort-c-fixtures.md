# Cohort C fixture QA — BLOCKED before model exposure

Frozen manifest SHA-256: `4aeb6fd0c2e88c0ad393d1a659eb062ae321f0db1a04dec80adb84ff880ef11f`. All 95 bound file hashes verified. No cohort files, maintained code, or tests changed; no GPU/model calls.

**One confirmed blocker:** all task oracles compare results using Python `==`. For task 06, the conforming reference passes, and a deliberately incorrect version returning integer `0`/`1` for the boolean `check` action also passes API checks, generated tests, and CLI checks. JSON `0`/`1` are not the required `false`/`true`. The mutation only wraps the reference dispatch result in `int(...)` for that action, retaining all other behavior. Both complete Docker outputs are saved in `qa-cohort-c-probe.json` under `reference` and `integer-instead-of-boolean` for task 06.

Repair recommendation: preserve C and freeze a new manifest with a common recursive result comparator that distinguishes boolean and numeric JSON values, plus identity controls containing booleans. Check the repaired oracle rejects this exact mutant while accepting the reference. Use exact integer checks where objectives explicitly require exact integers; avoid accidentally rejecting contract-permitted equivalent values.

| Check | Outcome |
|---|---|
| Allocation, calendar, matching expected values recomputed independently | 7, 5, and 69 examples agree; arithmetic uses rational quotas, calendar uses absolute month offsets, matching uses exhaustive assignment enumeration |
| Real Docker reference controls | Tasks 01, 07, 08, 06 all pass |
| Allocation floating-point quota mutant | Rejected, covering large nearly equal weights |
| Calendar retained February clamp mutant | Rejected |
| Greedy matching mutant | Rejected |
| Missing tests / failing tests / missing README content | All rejected in task 08 |
| Common quality oracle | Counts at least 3 discoverable unittest cases, runs them, requires README >=40 words plus action and cli.py; meaningfulness and complete usage semantics remain semantic-review responsibilities as cohort README states |
| Other objective/oracle compatibility | No additional contradiction identified in bounded inspection; this is not exhaustive proof |

Reproduction: `python3 .scratch/.sflo/03-autonomy-review/qa-cohort-c-probe.py` (exit 0 means expected controls and the known false acceptance reproduced). Complete executable probe: `qa-cohort-c-probe.py`; outputs: `qa-cohort-c-probe.log`, `qa-cohort-c-probe.json`. Recomputed expected-value counts: `qa-cohort-c-independent-values.json`. Docker image: `sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578`.

An initial QA harness run used an inaccessible temporary directory; its reference controls all failed import. After fixing only the scratch harness directory permissions, all reference controls passed and only then was the finding accepted. This was not a cohort defect. Existing 24 baseline/reference validation outcomes were inspected but not all rerun; four risk-focused controls and seven mutations were sufficient for this pre-exposure audit.
