# Independent question-gate slice QA — PASS with error-reporting boundary

Candidate `47640a0262c7338cb333456d9817dde8ae7c5c21`, reconstructed from Git into an automatically removed temporary directory by `qa_pinned.py`. No product/test edits and no GPU calls. A fake loopback HTTP model drove the actual ModelWorker, question assessor, Reviewer, Factory and real pinned Docker acceptance checks.

| Probe | Observed result |
|---|---|
| Already specified question, needed=false | Guidance returned as tool result; coder continued; Docker check and fresh review passed; accepted |
| Undecided subscription price, needed=true | Exact original question and assessment retained in worker.json; needs_input; repeated resume stays at attempt 1 |
| Missing assessment schema, invalid JSON, nonboolean needed | Interrupted after two HTTP requests; no verification and no coder continuation |
| Quote absent from objective | Interrupted; no verification |
| HTTP 503 during assessment | Interrupted; no verification |
| Empty choices response | Interrupted safely with IndexError, rather than normalized RuntimeError |
| Repair following proceed | Review repair evidence reached second coder attempt; recheck/review accepted on attempt 2 |
| Assessor context/authority | Fresh two-message request; no tools |
| Existing regressions | 12 review tests and 5 worker tests passed |

No false acceptance or swallowed assessment failure was observed. The verifier-chosen empty-response probe exposed a small error-reporting boundary: `complete()` indexes `choices[0]`, while `assess_question()` does not catch IndexError. The controller still interrupts and persists interruption evidence, but the CLI does not normalize this exception to its usual error message. Other malformed-response controls produce RuntimeError. This does not block the exercised fail-closed semantics.

## Reproduction

`python3 .scratch/.sflo/03-autonomy-review/qa-question-probe.py` exited 0; every routing expectation is asserted, including conforming proceed and question controls. To rerun without replacing retained evidence, set `GFLO_QA_EVIDENCE` to a fresh absolute directory. `qa_pinned.py` requires the exact candidate commit to remain in Git.

Evidence: `qa-question-evidence/results.json`, `requests.json`, durable per-run trajectories/worker/question/check/review artifacts; `qa-question-probe.log`; `qa-question-review-tests.log`; `qa-question-worker-tests.log`.

Pinned regression command: `python3 .scratch/.sflo/03-autonomy-review/qa_pinned.py 47640a0262c7338cb333456d9817dde8ae7c5c21 -m unittest discover -s tests -p 'test_review.py' -v`, likewise `test_worker.py`.

Scope: deterministic routing, persistence, grounding validation and affected review/repair semantics only. Exact substring matching establishes that a quote exists, not that its interpretation is correct; semantic question necessity remains dependent on model evaluation. This receipt does not establish cohort B success, retroactively change cohort A, or qualify the model's ability to distinguish real ambiguity. Those evaluations remain separate.
