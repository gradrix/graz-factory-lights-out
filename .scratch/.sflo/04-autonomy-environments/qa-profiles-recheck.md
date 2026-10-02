# Profile repair QA

**PASS for the repaired slice**, frozen candidate `25f75c3275739cc7cc2a4fc5a4e16580b81511d1`. Independent s-qa; prior three-profile evidence remains at [qa-profiles.md](qa-profiles.md). No Stage 3 acceptance claim.

| Check | Observed result |
|---|---|
| Packaged API generated tests | Real Docker verifier builds/installs the src-layout project wheel offline, then successfully imports its package from an added generated unittest. Both independent external control and generated tests pass. Source test bytes remain unchanged. |
| False-pass control | Change only that generated assertion to a wrong result: external check still exits 0; generated-test execution exits nonzero and combined verification rejects. |
| Cleanup failure, empty store | Inject failure only for outer `.work-*` cleanup during real stdlib preparation. Preparation raises and leaves no published reusable environment. |
| Cleanup failure, existing valid receipt | First prepare successfully, then inject the same failure on another preparation. All prior published file hashes remain identical and the original receipt still resolves with its original hash. |
| Context | Frozen API context now explicitly describes offline wheel build/install and installed-package test path. |
| Lifecycle continuity | 15 runner tests pass; runner/restart code unchanged from previous three-profile QA. |

## Reproduction

```sh
python3 .scratch/.sflo/04-autonomy-environments/qa-profiles-recheck/probe.py
python3 .scratch/.sflo/03-autonomy-review/qa_pinned.py 25f75c3275739cc7cc2a4fc5a4e16580b81511d1 -m unittest discover -s tests -p test_runner.py -v
```

[Probe](qa-profiles-recheck/probe.py), [results including complete verifier output](qa-profiles-recheck/results.json), [probe log](qa-profiles-recheck/probe.log), [runner log](qa-profiles-recheck/runner-tests.log). API uses the prior independent cold-prepared locked dependency snapshot recorded in `qa-profiles/results.json`; acquisition is unchanged and was not repeated. Cleanup probes prepare fresh stdlib stores and use deliberate host cleanup fault injection; they do not simulate daemon failures. Interrupted private scratch is explicitly removed after assertions.

No new product defect observed. No maintained edits, protected-fixture changes, models, GPU or rig calls. Full acquisition/resource/security acceptance remains outside this focused recheck.
