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

## Independent local review — qualification in progress

Controller checks have independently passed after repairing contradictory pass/question results, incomplete adapter schema acceptance and missing review-evidence integrity. Local model quality has separate gates; this stage is not accepted yet.

The first no-thinking Flash run identified ten seeded causes and passed all nominal controls. Independent semantic inspection discovered that a nominally clean Decimal implementation itself failed large valid inputs. The score is retained with that flaw. Dense Qwen also had malformed responses and a critical miss.

Fixture revision 2 corrects the money control/reference, adds large-value and exponent assertions without narrowing the objective, and retains the original defective control as a supplemental case. A stronger prompt alone still missed it. Unrestricted reasoning spent 8,192 output tokens without a verdict on the two money inputs. A separate 1,024-token thinking budget inside the 4,096-token total allowance distinguished defective money, corrected money and a state-transition defect in roughly 8–16 seconds. The complete bounded Flash repeat identified ten seeded defects plus the supplemental defect, with two false blocks and no format failures. Suggested repairs still need execution and re-review: some were incomplete.

**Runtime correction:** The factory sandbox used Python3.11.15, although later task objectives specified3.12+. Supplemental semantic checks used host3.12.12 or a separate3.12.13 image. The current cohort therefore does not establish target-runtime conformance. [Independent provenance audit](../../.scratch/.sflo/03-autonomy-review/qa-runtime-provenance-addendum.md).

These are repeated-set results used to improve the profile, not unseen-project success rates. The clean controls' two blocked portability concerns do not fail the intended Python 3.12/UTF-8 runtime; target-runtime context belongs in the next environment receipt. Numeric benchmark labels were not changed after observing these blocks.

[Controller recheck](../../.scratch/.sflo/03-autonomy-review/qa-recheck.md), [semantic recheck](../../.scratch/.sflo/03-autonomy-review/semantic-bounded-receipt.md), [frozen fixture lineage](../../evaluations/local-review/LINEAGE.json).

The bounded dense comparison caught seven seeded defects, missed a critical defect, produced four invalid assessments and missed the supplemental defect. Flash remains the measured serving choice. Cohort A then accepted **7/12** coding tasks: four avoidable questions and one generated-bytecode interruption prevented graduation. Its genuine pricing ambiguity stopped correctly. These failures are preserved in [coding-a.json](../../.scratch/.sflo/03-autonomy-review/coding-a.json).

Fresh local question assessment now distinguishes existing requirements and ordinary implementation choices from unresolved business policy. Invalid or unavailable assessments stop. Unreviewable generated artifacts return to bounded repair. [Independent repair QA](../../.scratch/.sflo/03-autonomy-review/qa-final-repairs.md) passed. The unused cohort B finished on frozen runtime `04c7ef6`: **11/12 controller-accepted**, with the separate queue-policy ambiguity correctly stopped. All accepted outputs repeated functional checks successfully. Inspection found nine deliveries without an identified requirement gap: task02 had a wrong generated assertion and omitted usage documentation; task03 fails an astronomically large valid retry count; task09 stopped on malformed question grounding. Task11 needed two review repairs before passing, including a critical precision defect introduced by earlier repair advice. [Raw result](../../.scratch/.sflo/03-autonomy-review/coding-b.json), [semantic evaluation](../../.scratch/.sflo/03-autonomy-review/coding-b-semantic.md).

Candidate `c17821c` now executes present Python regression suites alongside external acceptance. The actual task02 failure is caught and a real-Docker controller probe demonstrates failure → repair → recheck → review → acceptance. Full factory suite: **48 tests, 87% coverage**. The earlier development-account interruption is resolved. [Resumed independent QA](../../.scratch/.sflo/03-autonomy-review/qa-resumed.md) passed 32 targeted regressions and real-Docker failure/repair/integrity probes. [Remaining cohort-B semantic QA](../../.scratch/.sflo/03-autonomy-review/qa-semantic-resumed.md) also completed, preserving its original defects. Stage2 remains unaccepted pending revised-candidate qualification.

The local Flash endpoint still advertises **131072 tokens**. This cohort used at most **27522 prompt tokens**, median 9,599; median measured coder generation speed 78.3 tokens/s. Total task wall time was 1,706 seconds, including repair/review. These figures describe this small cohort and exclude reviewer requests from token metrics; they do not qualify128K problem solving. [Metrics](../../.scratch/.sflo/03-autonomy-review/coding-b-model-metrics.json).

## Reproduce qualification

```sh
python3 ops/prepare_qualification.py .gflo/qualification
PYTHONPATH=. python3 ops/qualify_review.py .gflo/qualification .gflo/review-result.json
PYTHONPATH=. python3 ops/qualify_coding.py .gflo/qualification .gflo/coding-results
```

Use the configured local endpoint and installed pinned sandbox image. The preparer verifies content hashes and creates clean Git input repositories; new Git commit metadata may differ from the original private preparation while model-visible file hashes remain identical. Scoring labels and references are controller-only data and are never supplied to the model. Coding workers receive isolated source copies; their acceptance stays outside the writable project mount. Preserve failed runs. Do not rerun into an existing output/state and call the result an unseen trial.

## Current correction on the 5090

Runtime `c17821c` matches the rig's source hashes. A separate repeated trial started from cohortB task02's defective accepted output. The new test gate rejected attempt1; after the test and documentation repair, local review requested an additional validation correction; attempt3 was accepted in350.61seconds. Both external acceptance and generated regression checks passed again against hash-matched copied output. [Real repair evidence](../../.scratch/.sflo/03-autonomy-review/project-test-repair-rig/result.json), [check readback](../../.scratch/.sflo/03-autonomy-review/project-test-repair-rig/repeated-verification.json).

This known-case result proves the repair path with the actual local model. It leaves the original cohort scores intact. Independent verification of the correction has now passed. Broader revised-candidate qualification is running as frozen cohort C-v2: twelve new bounded tasks plus a separate ambiguity case, after independent fixture validation. Stage3 environment preparation remains gated on this result and semantic evaluation. Factory inference and execution remain local.
