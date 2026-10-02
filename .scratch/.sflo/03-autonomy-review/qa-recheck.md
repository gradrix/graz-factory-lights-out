# Independent slice recheck — PASS

Candidate: `197371ea5dc47b4aad77f3ac1f2a79c2a72f2410`, tested from a frozen `git archive` in `qa-recheck-candidate/`. All three initial findings are closed on the exercised paths. No maintained files changed and no GPU calls. Loopback fake HTTP model and real pinned Docker acceptance image as in initial receipt.

| Coverage | Result |
|---|---|
| Pass plus unresolved question through real Reviewer/HTTP | Interrupted; no acceptance |
| Incomplete reviewer adapter schema | Interrupted; no acceptance |
| Review evidence deleted; then both review and verification deleted | Accepted status invalidated |
| Review evidence mutated/restored | Factory and Observer invalidate mutation, accept restored original |
| Controls: valid pass, unknown decision, malformed JSON schema, blocking pass | Expected acceptance/rejections preserved |
| Check → review → repair → recheck | Accepted on attempt 2, repair evidence reaches worker |
| Required reviewer missing during recovery | Rejected |
| Crash after saved review/verification | Accepted on restart without repeating worker |
| Product question | needs_input; repeated resume remains stopped at attempt 1 |
| Fresh review context / no tools / local endpoint restrictions | Passed |
| Additional repair plus question, invalid source location, oversized files | Rejected |
| Candidate regressions | Review 6, runner 13, observation 7: all 26 passed |

Evidence: `qa-recheck-evidence/results.json`, `assertions.json`, `http-requests.json`, durable run artifacts, `qa-extra-recheck.log`, and `qa-recheck-{review,runner,observation}-tests.log`.

Executable probes: `qa-probe-recheck.py` preserves original controls/findings on the new candidate; `python3 .scratch/.sflo/03-autonomy-review/qa-assertions-recheck.py` exits 0 with no failures; `python3 .scratch/.sflo/03-autonomy-review/qa-extra-recheck.py` exits 0. The fixture-producing probe requires a fresh evidence directory when rerun. Existing test commands ran from the frozen candidate: `python3 -m unittest discover -s tests -p 'test_review.py' -v`, and equivalent runner/observation filenames.

Boundary: this closes controller slice findings, not final Stage 2 qualification. Real-model comparison and held-out coding tasks remain separately owned. A stopped question has no in-place answer API; resolving it still requires a new explicit task contract. Unavailable-model transport was not independently simulated in this recheck.

## Portable reproduction and scope note

The temporary source trees used during QA were removed before publication. Evidence scripts now use `qa_pinned.py` to reconstruct their exact candidate from Git into an automatically cleaned temporary directory, including the pinned import path for Docker guardian subprocesses. No duplicate runtime implementation is published. Historical commands above describe the original execution.

To rerun without overwriting retained evidence, set `GFLO_QA_EVIDENCE` to a new absolute directory and run the corresponding probe, then assertions with the same environment value. For example:

```sh
GFLO_QA_EVIDENCE=/tmp/gflo-independent-recheck python3 .scratch/.sflo/03-autonomy-review/qa-probe-recheck.py
GFLO_QA_EVIDENCE=/tmp/gflo-independent-recheck python3 .scratch/.sflo/03-autonomy-review/qa-assertions-recheck.py
GFLO_QA_EVIDENCE=/tmp/gflo-independent-recheck python3 .scratch/.sflo/03-autonomy-review/qa-extra-recheck.py
```

For the initial failure, use `qa-probe.py` and `qa-assertions.py`; expected assertions exit status is 1. Pinned regressions can be repeated with `python3 .scratch/.sflo/03-autonomy-review/qa_pinned.py 197371ea5dc47b4aad77f3ac1f2a79c2a72f2410 -m unittest discover -s tests -p 'test_review.py' -v` (substitute runner/observation filenames as needed). The referenced commits must remain available in Git.

The later reviewer request enables bounded thinking (1024 tokens within 4096 output tokens). That request configuration was not part of either pinned QA candidate. These controller findings and recheck results retain their original scope; they do not qualify the new model configuration. `thinking-bounded.json` and the separately running model requalification own that evidence.
