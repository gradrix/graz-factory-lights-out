# Initial independent slice QA — FAIL

Candidate: `ba364023ad90bcea68193ff1c5ddf8e6971f7b07`. Executed an immutable `git archive` copy in `qa-candidate/`; live edits are excluded. Contract: `contract.md` in this directory. No GPU inference or maintained file edits. Model calls used a loopback fake HTTP server; acceptance used the installed pinned Docker image `sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578`.

## Findings

1. **Major: unresolved product question can be accepted.** `gflo/review.py:33` does not reject a nonempty question accompanying `pass`. A real HTTP review `{decision: "pass", findings: [], question: "Should the value be 3 instead?"}` reached `accepted`. The valid empty-question control accepts; unknown decisions, missing schema, and pass with a major finding correctly interrupt. Require the complete consistency rules before controller acceptance.
2. **Major: controller does not enforce complete review schema.** `gflo/runner.py:309` checks only the decision token. A reviewer adapter returning just `{decision: "pass"}` reaches `accepted`. Current CLI's Reviewer rejects this malformed response, but the controller's own acceptance boundary does not uphold the contract. Validate at that boundary against the actual candidate files.
3. **Major: accepted status survives loss of all review evidence.** After a valid acceptance, deleting both `attempts/1/review.json` and `attempts/1/verification.json` still reports `accepted`. `accepted.json` binds only candidate and patch; `status()` does not check review/check evidence. This is a durability/audit failure, not a claim that the original execution skipped review. Bind required check/review evidence into the receipt and validate its presence/integrity.

## Coverage

| Check | Observed | Verdict |
|---|---|---|
| Unknown/malformed HTTP decision and pass + blocking finding | Interrupted; no acceptance | Pass |
| Pass + unresolved question | Accepted | Fail |
| Incomplete adapter decision | Accepted | Fail |
| Check → review → repair → recheck | Two Docker-checked attempts; first repair passed to next worker, second pass accepted | Pass |
| Required review persisted and missing reviewer on restart | Frozen requirement true; restart without reviewer rejected | Pass |
| Crash after saved verification | Restart accepts in same attempt without repeating worker | Pass |
| Product question stop/resume | needs_input; repeated resume remains needs_input at attempt 1 | Pass for stopping; no in-place answer/resume API exists |
| Review evidence deletion | Still accepted after both evidence artifacts deleted | Fail |
| Fresh context / no reviewer tools | Every HTTP review has two messages and no tools | Pass |
| Local inference constraint | HTTPS remote and LAN endpoints rejected | Pass |
| Existing focused regressions | 4 review tests + 13 runner tests pass | Pass |

## Reproduction and evidence

- `PYTHONPATH=.scratch/.sflo/03-autonomy-review/qa-candidate python3 .scratch/.sflo/03-autonomy-review/qa-probe.py` creates fixture repositories and durable run artifacts under `qa-evidence/`. Use a fresh evidence directory to rerun; the preserved fixture directory is intentionally not overwritten.
- `python3 .scratch/.sflo/03-autonomy-review/qa-assertions.py` exits **1**, matching the failing acceptance expectations; conforming controls are asserted first. `qa-assertions.log` lists failures.
- `qa-evidence/results.json`, `qa-evidence/assertions.json`, `qa-evidence/http-requests.json`, and per-run task/check/review/receipt artifacts preserve observations. Deleted evidence cases are explicitly named `receipt`.
- From `qa-candidate/`: `python3 -m unittest discover -s tests -p 'test_review.py' -v` (4 passed); same command with `test_runner.py` (13 passed).

This is a controller/reviewer slice, not final Stage 2 acceptance. Real-model 20-candidate qualification and 12 coding tasks are owned separately by the main agent. Oversized/unavailable-model behavior is inspected but not independently exercised here. Question resolution currently requires a new explicit task contract; no answer workflow was found. The controller findings require repair and fresh verification before acceptance.

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
