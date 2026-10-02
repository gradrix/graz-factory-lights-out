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

These are repeated-set results used to improve the profile, not unseen-project success rates. The clean controls' two blocked portability concerns do not fail the intended Python 3.12/UTF-8 runtime; target-runtime context belongs in the next environment receipt. Numeric benchmark labels were not changed after observing these blocks.

[Controller recheck](../../.scratch/.sflo/03-autonomy-review/qa-recheck.md), [semantic recheck](../../.scratch/.sflo/03-autonomy-review/semantic-bounded-receipt.md), [frozen fixture lineage](../../evaluations/local-review/LINEAGE.json).

The bounded dense comparison caught seven seeded defects, missed a critical defect, produced four invalid assessments and missed the supplemental defect. Flash remains the measured serving choice. Cohort A then accepted **7/12** coding tasks: four avoidable questions and one generated-bytecode interruption prevented graduation. Its genuine pricing ambiguity stopped correctly. These failures are preserved in [coding-a.json](../../.scratch/.sflo/03-autonomy-review/coding-a.json).

Fresh local question assessment now distinguishes existing requirements and ordinary implementation choices from unresolved business policy. Invalid or unavailable assessments stop. Unreviewable generated artifacts return to bounded repair. [Independent repair QA](../../.scratch/.sflo/03-autonomy-review/qa-final-repairs.md) passed. A new unused set of twelve three-module tasks plus a separate queue-policy ambiguity is running on the 5090; stage acceptance still requires its results and independent semantic inspection.

## Reproduce qualification

```sh
python3 ops/prepare_qualification.py .gflo/qualification
PYTHONPATH=. python3 ops/qualify_review.py .gflo/qualification .gflo/review-result.json
PYTHONPATH=. python3 ops/qualify_coding.py .gflo/qualification .gflo/coding-results
```

Use the configured local endpoint and installed pinned sandbox image. The preparer verifies content hashes and creates clean Git input repositories; new Git commit metadata may differ from the original private preparation while model-visible file hashes remain identical. Scoring labels and references are controller-only data and are never supplied to the model. Coding workers receive isolated source copies; their acceptance stays outside the writable project mount. Preserve failed runs. Do not rerun into an existing output/state and call the result an unseen trial.
