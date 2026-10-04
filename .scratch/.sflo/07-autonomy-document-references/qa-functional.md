# Independent format3 functional QA / harness adapters

**PASS for the bounded no-model slice.** Candidate92deaab, manifest `acd723171fe9b3f5ce9b90b2dc8aea29dbb5e57d41854cf322798690556bc698`; every bound file hash verified before/after. No model/rig calls or maintained edits. Live13-case semantic/source and rig replay gates remain pending.

| Check | Observed result |
|---|---|
| Public answer, actual bounded child processes | A bool span selector rejects; single repair with valid duplicate selectors succeeds, keeps both response files, materializes exact curly source punctuation and counts both citations. Two invalid responses produce immutable diagnostic, never replayable. |
| Request identity / harness | Captured actual public first request equals `reference_request(evidence,model,question)` exactly; ledger request hash matches its canonical encoding. Proposed import/signature and format3 resolve/AnswerFailure behavior match harness. |
| Focused protocol regressions |7tests pass: exact Unicode, frozen format2 protocol, strict IDs/counts/extra fields, encoded boundaries, long-span capacity refusal, aggregate/preflight limits, rehashed canonical/catalog/version tampering. |
| Actual historical records, private copies |16records from preserved trial1format2 and acceptedformat1 stores resolve. Eightformat2 and twoformat1 answers replay unchanged; twoformat2 diagnostics retain refusal semantics; four evidence records resolve. All original/copied file hashes unchanged except excluded root lease. |

Complete reproducible probes and results: [public fork probe](qa/probe.py), [results](qa/probe-results.json), [focused log](qa/affected.log), [legacy probe](qa/legacy.py), [legacy results](qa/legacy-results.json). Acquisition in the public probe uses an explicitly synthetic executor; bounded answer children are real processes with fake clients, not model calls.

Thirteen-case harness SHA `c299b7acae6920d2e5644d4746e2ac4038e4a482922faec341159f1b1808f3bc` and prepared replay script syntax pass. No broad full-suite repeat. Security independently owns adversarial authority/expansion/publication boundaries. Source alignment must still bind actual new IDs/body/spans before inference; prior failures remain unchanged and all ten old questions count as repeated diagnostics.
