# Review-loop evidence continuity at 4346ba5

Candidate: `4346ba5289f24f228f83f6f45646f32e41cd48c1`. Scope assessment against the Stage 2 contract, not a replacement qualification. No models, GPU, rig, or maintained changes.

**Conclusion:** the historical genuine loop evidence remains applicable to the unchanged reviewer/controller/verifier mechanism. It must retain its original runtime/profile labels. A new target-model loop is not required merely to re-prove those unchanged components. It does not establish a success rate for the new medium coder; current unseen D results and their independent semantic evaluation remain separate gates. D06's false-positive repair supplies no useful-defect-detection evidence.

## Exact continuity

| Component | Git blob continuity |
|---|---|
| `gflo/review.py` | `200931c5054b107ea71cbe397645b9a235edce84`, identical at 04c7ef6, c17821c, 4346ba5 |
| `gflo/runner.py` | `36bf31bff7da5e894ab9bf499de7f1e84ea0e0d0`, identical at all three |
| `gflo/sandbox.py` | `dddb23d332f4a9205a354674e96f31a5d6406aad`, identical c17821c→4346ba5; earlier B11 predates added generated-test gate |
| Coder | New bounded-thinking request and structured trace serialization; previous-verdict construction unchanged |

B11 run `c38088d51d73` on 04c7ef6 records repair/repair/pass with checks passing each time. Review2 identifies a genuine exact-integer collision and sparse-sequence iteration defect; semantic supplemental probes confirm final behavior. Review1's suggested float normalization introduced the critical issue, so this is evidence of eventual detection and repair, not uniformly reliable repair advice. Exact receipts: `coding-b-evidence/11-event-watermarks/attempts/{1,2,3}/{verification,review}.json`; semantic account: `coding-b-semantic.md:44` and `event-equality-probe.json`.

Repeated B02 run `171a71b31de6` on c17821c records external/generated exits `[0,1]`, then `[0,0]` with review repair, then `[0,0]` plus pass. `project-test-repair-rig/evidence.json` binds distinct candidate hashes per attempt and final acceptance artifacts; `result.json` records 350.61 seconds; `repeated-verification.json` repeats final checks. The initial wrong generated assertion is an independently demonstrated real failure. The subsequent reviewer integer-validation interpretation is less decisive than B11's precision defect; it is not needed to establish useful detection. Both historical runs used image a8a3/Python3.11.15, not D's 3.12.13 target.

## Current regression assessment

All 14 current `test_review.py` regressions pass, including persisted findings driving repair and acceptance requiring review. A new minimal handoff probe confirms medium/1024/4096 requests receive the exact prior verdict without context mutation; trace JSON parses. This closes the concrete changed-coder interface risk without new target-model calls. No further functional-loop regression identified. Existing current environment/wire/process tests cover their respective changes; do not relabel old model results as current-profile trials.

**Separate privacy boundary discovered:** the previous verdict is serialized JSON embedded inside a user-message string. An assignment such as synthetic `token="ALPHA BETA"` acquires escaped quotes there, and the current scrubber leaves its value in recorded message text. The handoff probe confirms this leak while proving model input is unchanged. This is an actionable evidence-privacy issue, not a failure to deliver repair feedback; retain D unchanged and address separately before claiming complete quoted-secret handling.

Reproduce: `python3 .scratch/.sflo/03-autonomy-review/qa-review-loop-handoff.py` (exit 0 verifies handoff and reproduces known privacy boundary). Evidence: `.py`/`.log` beside this note and `qa-review-loop-continuity-tests.log`. Regression invocation: `python3 .scratch/.sflo/03-autonomy-review/qa_pinned.py 4346ba5289f24f228f83f6f45646f32e41cd48c1 -m unittest discover -s tests -p test_review.py -v`.
