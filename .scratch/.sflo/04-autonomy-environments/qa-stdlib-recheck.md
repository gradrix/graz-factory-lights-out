# Stdlib environment repair QA

**Verdict: PASS for the accepted-run integrity repair.** Candidate `f5b5491bdb58da85481430f2cb9363103166a067`; independent focused slice recheck using s-qa. This closes the finding in [original QA](qa-stdlib.md), whose evidence is retained. It does not accept Stage 3.

| Check | Observed result |
|---|---|
| Unchanged environment control | Real Docker task accepted after controller restart; repeated accepted resume succeeds. Frozen image overrides an intentionally nonexistent configured image. |
| Original negative probe | Changing dependency-root permissions from 0555 to 0755 makes Factory status `invalidated`; accepted resume raises ValueError. |
| Observer boundary | The same tampered accepted run returns `invalidated` through Observer.status (asserted in executable probe). |
| CLI/runtime regression | Prepare twice yields identical ID; inspect and two checks pass without a model configuration. Actual Python 3.12.13, pinned fb1118 image, runc, network none, read-only dependency mount; attempted worker dependency write rejects. |
| Runner regressions | 15 tests pass, including accepted integrity and existing resume behavior. |

The repair adds environment resolution to shared `accepted_intact`, so terminal acceptance now includes the same frozen dependency validation used during execution. No further defect observed in this scope. Original worker/reviewer-context evidence remains applicable; those paths are unchanged by this repair.

## Reproduction and evidence

Run from repository root:

```sh
python3 .scratch/.sflo/04-autonomy-environments/qa-stdlib-recheck/probe.py
python3 .scratch/.sflo/03-autonomy-review/qa_pinned.py f5b5491bdb58da85481430f2cb9363103166a067 -m unittest discover -s tests -p test_runner.py -v
```

Evidence: [probe](qa-stdlib-recheck/probe.py), [probe log](qa-stdlib-recheck/probe.log), [result](qa-stdlib-recheck/result.json), [runtime checks](qa-stdlib-recheck/checks.json), [receipt](qa-stdlib-recheck/receipt.json), [runner log](qa-stdlib-recheck/runner-tests.log). Disposable run `b52de84540fa`; environment `b9ca5be28ee06735117b13ce9944c0276cca091a3a7be6c14c5b90b01c6a62b9`.

No maintained edits, target-model calls, GPU calls, rig changes, or API/Node profile qualification.
