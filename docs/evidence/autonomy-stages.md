# Incremental autonomy qualification

## Visibility and controlled operation — accepted

Candidate `18a274f`; independent review and real RTX 5090 trials, 2026-10-02.

| Actual local-model task | Interruption | Accepted attempt | Elapsed |
| --- | --- | ---: | ---: |
| Invoice decimal CLI | Targeted cancellation, then resume | 2 | 136.4 s |
| Inventory utility | Controller SIGKILL, then resume | 2 | 165.5 s |
| Log summary CLI | None | 1 | 74.2 s |

Every run had exactly one durable acceptance event. A second HTTP client observed execution. Independent real-Docker probes checked killed/cancelled writers, recovery, event replay, evidence integrity, read-only HTTP boundaries, redaction/truncation and startup cancellation. Chromium checked desktop light/mobile dark, artifact navigation, disconnect/reconnect and empty-state behavior.

Three QA findings were repaired: fresh-state API failure, false pending state after startup cancellation, and lost `--rm` command arguments in the guardian. Container creation is completed before starting any writer. Final guardian tests also passed on the rig. Source used by the initial model trials was `3c3a834`; subsequent repairs were rechecked within their affected scopes through the accepted candidate.

[Independent acceptance](../../.scratch/.sflo/02-autonomy-visibility/qa-accepted.md), [rig receipt](../../.scratch/.sflo/02-autonomy-visibility/rig-trials.json), [final rig guardian checks](../../.scratch/.sflo/02-autonomy-visibility/rig-guardian-final.txt), [coverage](../../.scratch/.sflo/02-autonomy-visibility/coverage-final.txt).

## Independent local review — accepted

Accepted candidate **3bd8ae2**, 2026-10-02. Actual local-model cohort D ran on **4346ba5**; later changes repair display/trace redaction and promote the already-tested default profile. Model prompts, reviewer and controller acceptance logic did not change after that cohort.

| Gate | Observed result |
| --- | --- |
| Frozen reviewer defect/control set | Flash caught10/10 seeded defects, all critical, with2 false blocks and0 format failures; supplemental known defect caught. |
| Equal-budget dense reviewer comparison |7/10, critical miss,4 invalid assessments; Flash retained. |
| Fresh coding cohort D | **12/12 accepted**, all repeated executable checks and independent semantic checks passed. |
| Separate product ambiguity | Correct `needs_input`; no invented allocation implemented. Question wording still included unnecessary policy detail. |
| Real repair | D09 repaired a failing generated CLI test on attempt2. Earlier B11 demonstrated genuine reviewer findings and repair; unchanged-component continuity was independently checked. |
| Lifecycle/privacy regressions |59-test whole suite,88%coverage at89d66ea; subsequent parity repair passed21 affected tests and independent HTTP/worker probes. Promoted image passed8 sandbox/qualification tests. |

Qualified serving is the installed Flash-Next Coder export, one serialized local request, **131072 context**. Coding requests use medium reasoning with a requested1024-token thinking budget inside4096 total output tokens. Sandbox runtime is independently measured **Python3.12.13**, imagefb1118f… . The server does not separately report actual reasoning-token consumption.

D used182 coder calls, a maximum27628 prompt tokens (median8632), median65.8 generation tokens/s, and2910.67seconds total task wall time (about49minutes). All565 trajectory lines parse as JSON. These measurements exclude reviewer/question-assessment calls from token statistics and do not qualify128K problem solving.

**Remaining quality limitations:** D06 review wrongly rejected a correct tie-break and caused unnecessary repair. D09 retains a minor README escaping error. D05 tests assume `/workspace`; several outputs contain unnecessary validation or test-quality residue. Ambiguity wording suggests an unstated partial-payment rule even though it correctly stops. No accepted critical or substantive functional miss was found, but twelve bounded tasks are a qualification floor, not proof of reliable large-project autonomy.

[Full independent D evaluation](../../.scratch/.sflo/03-autonomy-review/qa-coding-d.md), [raw result](../../.scratch/.sflo/03-autonomy-review/coding-d.json), [runtime identity](../../.scratch/.sflo/03-autonomy-review/coding-d-runtime.json), [metrics](../../.scratch/.sflo/03-autonomy-review/coding-d-model-metrics.json), [review-loop continuity](../../.scratch/.sflo/03-autonomy-review/qa-review-loop-continuity.md), [final privacy recheck](../../.scratch/.sflo/03-autonomy-review/qa-nested-verdict-parity-recheck.md).

### Preserved failed trials

A finished7/12; B had11 raw acceptances but only9 deliveries without identified requirement gaps; C finished9/12 and failed its gate. Their scores were not rewritten. Earlier trials used Python3.11.15 despite later objectives targeting3.12; separate3.12 checks do not retroactively correct execution. A paired repeated-case probe then repaired2/2 known failures with bounded medium reasoning versus0/2 without reasoning. That small experiment motivated fresh D; it is not an unseen success rate.

[Execution history and repairs](../../.scratch/.sflo/03-autonomy-review/run.md), [C semantic evaluation](../../.scratch/.sflo/03-autonomy-review/qa-coding-c.md), [runtime provenance correction](../../.scratch/.sflo/03-autonomy-review/qa-runtime-provenance-addendum.md), [paired repair evidence](../../.scratch/.sflo/03-autonomy-review/qa-repair-reasoning-results.md). Earlier independent Docker checks that used the local default runtime establish functionality, not GPU isolation; later receipts explicitly select runc.

### Reproduce D as a repeated trial

```sh
python3 ops/prepare_qualification.py .gflo/repeated-d --source evaluations/coding-d
PYTHONPATH=. python3 ops/qualify_coding.py .gflo/repeated-d .gflo/repeated-d-results
```

Use the qualified configuration and installed pinned image. Existing destinations are refused. Published hashes identify the original model-visible inputs; new Git commit metadata can differ. Acceptance checks remain outside the writable worker mount. These now-known cases cannot be labeled unseen in a rerun.

## Supported environments — implementation next

Approved design uses pinned bases plus immutable read-only dependency snapshots. Fetch, offline assembly, hostile artifacts and publication require their own qualification. Three model-task fixtures passed independent pre-exposure checks after two oracle false passes were repaired; this is fixture evidence, not an implemented environment capability. [Delivery unit](../../.scratch/autonomy/delivery/04-environments.md).
