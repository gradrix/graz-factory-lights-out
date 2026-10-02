# Cohort B semantic evaluation

**All twelve task outcomes inspected: first four by the independent QA agent, remaining eight by the coordinator after the account usage limit.** Raw controller score 11/12; nine deliveries have no identified requirement gap, task02 has test/docs defects, task03 has an extreme valid-input limitation, and task09 stopped. No accepted critical functional miss identified in this inspection. This mixed inspection is not a completed fresh-agent final QA. Cohort A remains 7/12.

Frozen runtime reported by controller: `04c7ef6`. Frozen cohort-B manifest: `a4fa7ffef4dc63642356e402c02174947896f9d12863ac2f2eeb828e3aa46d60`.

| Task | Run | Outcome and semantic inspection |
|---|---|---|
| 01 dependency order | `541053c47a7a` | Accepted attempt 1; independent acceptance passes; all 26 generated tests pass. Source checks duplicate and unknown IDs, de-duplicates edges, reevaluates original-order priority at every selection, detects disconnected cycles and avoids input mutation. API routing and CLI retained. README documents new action and rules. No missed objective found. |

| 02 rate window | `0c3f4f76b509` | Accepted attempt 1; independent functional acceptance passes. Full-objective delivery fails: unchanged README omits required new usage; generated regression `test_retry_when_count_exceeds_limit` wrongly expects 20 instead of contract-correct 21. Target pinned-image generated suite confirms 25/26 passing and precisely this assertion failing; all four CLI tests pass at `/workspace`. |

| 03 retry schedule | `3c48308dd1cc` | Accepted attempt 1; independent acceptance passes; 27/27 target-generated tests pass; documentation present. Separate unbounded-attempt computational boundary found: see below. |

| 04 config precedence | `6358245a8c27` | Accepted attempt 1; independent acceptance and target-generated suite pass. Source correctly distinguishes default nulls from layer deletion, merges introduced objects against empty base, deep-isolates defaults/layer data, retains required-key semantics. API/CLI and new usage documented; no missed requirement found. |

## Confirmed noncritical findings

Task 02 `workspace/tests/test_admit.py:58` requires retry_at=20 for history [10,11,12], window 10 and limit 2. At t=20 two entries remain active, so no slot exists; t=21 is the earliest valid retry. The implementation correctly returns 21. Its generated suite therefore contains a wrong assertion even in the target sandbox. Task 02 README is byte-identical to the baseline and documents only count, omitting the explicitly requested new usage. Independent frozen acceptance does not enforce generated-suite success or documentation; fresh review also returned pass with no findings. These are incomplete delivery/QA obligations, not critical functional misses. Preserve raw accepted status alongside stricter semantic outcome.

Artifacts are copied read-only from terminal runs into `.gflo/semantic-b/<run>/`, excluding credentials/raw configuration. Each capture has a content-hash manifest; review and verification JSON are retained. Local acceptance and generated tests run in disposable copies under CPython 3.12.12 with its `python` executable on PATH to match the stated runtime. An initial local generated-test failure was a missing host `python` command, resolved by matching PATH; it was not a candidate defect. Evidence: `.gflo/semantic-b/audit-results.json`; collector/auditor scripts are adjacent.

The frozen independent oracle covers ordering invariants over all forward-edge four-node graphs, duplicates, missing dependencies, cycles, preserved actions and CLI. Generated tests add useful disconnected-cycle and rejected-input immutability checks. Documentation and full implementation were inspected in addition to test exit codes. No models or GPU used for this evaluation; no candidate or fixture edits.

Target generated suites also ran in the actual existing pinned image on the rig, with read-only workspace, no network, no GPU and source hash matching. Per-task `target-generated-tests.json` receipts and compact source patches are exported under `coding-b-evidence/`, along with review/verification and identity hashes. Task 01: 26/26 pass. Task 02: 25/26 pass; one wrong test assertion, zero target CLI errors.

Task 03 computational boundary: valid `attempt=10**30`, `max_attempts=10**30+1`, `base=1`, `cap=10`, `now=0`, transient outcome causes `MemoryError` while constructing the uncapped power. The private reference returns `{retry:true,at:10,delay:10}` immediately under the same 128MiB safety bound. Evidence: `.gflo/semantic-b/3c48308dd1cc/large-attempt-probe.json`. This is outside realistic retry counts but inside the explicitly unbounded integer contract; record as a noncritical computational robustness limitation, separate from usual-path correctness. No production-risk extrapolation.

## Continuation after independent-agent capacity limit

The independent QA agent hit the account usage limit after inspecting tasks 1–4. Subsequent source inspection below is by the coordinating agent, separately from local model generation; it is not a completed fresh-agent final QA. Frozen outputs remain unchanged.

- Task05 escaped log fields (`3a580376311a`): exact four-escape handling, first-equals split, sorted encoding, strict ASCII keys, duplicates and empty fields correctly handled; inputs unchanged. API/CLI preserved, new usage documented, target generated suite passes. No missed objective found by coordinator.
- Task06 archive manifest (`df03c8b4fc28`): rejects traversal, ambiguous separators, colons/NUL, duplicate normalization and whole-segment ancestor conflicts; exact totals and sorting preserved. No filesystem extraction occurs. API/CLI/docs present, target generated suite passes. No missed objective found by coordinator.

- Task07 optimistic version (`fb1fb7b64726`): external checks rejected the first incomplete implementation (missing update action); second attempt implements create-only/null, expected-version merge and deep independence of all returned containers. Read/API/CLI retained, usage documented, target generated suite passes. No missed objective found by coordinator.
- Task08 batch grouping (`751bc03d4c4b`): validates duplicate/unknown IDs before grouping, preserves requested order and falsey successes, does not retry or mutate input. API/CLI/docs and target generated suite pass. No missed objective found by coordinator.

- Task09 migration (`fa94c69430ad`): interrupted and never accepted. The retained candidate fails to set output revision3 despite the explicit requirement. It asks about already-excluded accounts/order inputs and an already-specified target revision; question assessment failed grounding and the controller stopped. The frozen acceptance correctly catches the missing revision update. This is a failed autonomous completion, with safe failure classification.
- Task10 weighted LRU (`ef27abbc21eb`): second attempt passes; preserves too-heavy replacements unchanged, removes replacement keys without counting eviction, promotes gets, evicts older entries by total weight, and retains input data. API/CLI/docs and target generated suite pass. No missed objective found by coordinator.

- Task11 event watermarks (`c38088d51d73`): accepted attempt 3 after two real local review repairs despite executable checks passing. Review1 found distinct serialization of numerically equal values; its suggested float normalization introduced a large-integer collision, caught by review2 together with a sparse-sequence loop. Final code uses exact numeric comparison and walks present sequences. Generated suite and supplemental equality/sparse probes pass. New usage documented. Minor residue: unused canonical-form computation and an inaccurate unused-helper docstring remain; reviewer did not flag them.

Supplemental fixture audit (not a frozen-score rewrite): the prepared task11 reference conflates `true` with `1` using Python equality. The final generated candidate correctly distinguishes them. The phrase “JSON equality” should be made explicit in the next fixture revision. [RFC6902 section4.6](https://www.rfc-editor.org/rfc/rfc6902.txt) provides the interpretation used by these supplemental probes: JSON types must match, with numbers compared numerically. Candidate/reference results are in event-equality-probe.json. Neither original fixture nor its results was overwritten.

- Task12 Unicode index (`aefc008cb097`): correct UTF-8 cumulative offsets for code points, rejects inside-character/out-of-range offsets, handles end/empty and repeated requests, leaves inputs unchanged. API/CLI/docs and target generated suite pass. No missed objective found by coordinator.
- Separate ambiguous queue policy (`3e2cd228ff6e`): needs_input on attempt 1 with an explicit request to choose fairness and its priority interaction. The objective expressly leaves both undecided. No policy invented; this is the expected result and outside the twelve-task denominator.

## Qualification result

Raw numeric harness passes 11/12 plus the correct ambiguity stop. All eleven accepted outputs repeat the frozen functional oracle successfully. Ten of their generated suites pass; task02 has one failing assertion. Semantic inspection identifies nine of twelve deliveries without a requirement gap, plus the documented minor unused-helper residue in task11. The two accepted defects are retained, not silently repaired in the frozen batch. Final fresh-agent QA and qualification of the later generated-test gate remain pending; stage2 is not graduated.
