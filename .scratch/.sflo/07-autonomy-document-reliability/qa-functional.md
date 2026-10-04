# Unit07 independent functional QA / harness preflight

**PASS for the bounded no-model functional slice; live source alignment, ten-answer semantics and rig offline replay remain pending.** Candidate `2fe870d`, manifest SHA256 `4e1481dede629f9c83be9bbd0002d0975eccbd33820d4456ef5c75bd9eecfc2e`. Every bound file hash verified before and after the independent probe. No maintained edits or model calls.

| Check | Result/evidence |
|---|---|
| Independent public answer through actual bounded fork children | Invalid JSON then valid response: exactly two calls, original/repaired canonical responses retained, format2 success resolves and replays. Two invalid responses: exactly two calls, inspectable answer_failure, replay refuses. Acquisition was explicitly a synthetic fixture executor. [Probe](qa/probe.py), [results](qa/probe-results.json), [log](qa/probe.log). |
| Focused affected regressions |11 `test_document_repair` tests passed:40K/+1 extraction, quote repair, exhaustion, first-valid/legacy replay, no authority/transport/overflow repair, cancellation, rehashed ledger tamper, CLI failure, receipt overflow and symlink/extra-file refusal. [Log](qa/affected.log). No broad/full-suite repeat. |
| Harness adapters | Public acquire→resolve IDs, answer question override, AnswerFailure.identifier diagnostic, resolve of both format2 outcomes, response-1/2 filenames all match frozen candidate. Initial-request reconstruction matches product interface; product owns repair. Syntax passed; harness SHA6358feb74d26f966efd38ec91f083f16fb288aeee859f6d75ab90fbca6abf7f0. |
| Preserved QA setup failure | Initial private probe passed an unbound synthetic executor and failed before inference; fixed only the disposable probe binding. [Original error](qa/probe-initial-error.txt). |

Reproduce: `python3 .scratch/.sflo/07-autonomy-document-reliability/qa/probe.py`; `PYTHONPATH=.:tests python3 -m unittest test_document_repair`. The probe imports the frozen candidate from this checkout and asserts its manifest before/after.

The two-phase plan remains valid. Independent source gate will bind actual acquired bodies/spans and all ten oracle cases; this reviewer leaves coordinator_go false. Root alone supplies coordinator authorization after review. Fresh acquired bytes differing from cached baseline need explicit addenda; no silent expected-fact changes. Functional success and citation provenance do not establish semantic success.
