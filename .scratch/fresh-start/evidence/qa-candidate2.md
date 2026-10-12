# Candidate 2 independent QA

**Verdict: PASS for the bounded runner/sandbox recheck.** This is not final acceptance of live-model task competence.

Frozen candidate: `/tmp/gflo-review-candidate2`.
Identity: `13c94ac78c706752d190bbee8d066cab82c3bc36dcfeb4b742d03a0499260acf`.
All manifest file hashes matched before independent probes. No maintained files, tests, or remote rig state changed.

| Finding / requirement | Recheck and observation | Status |
|---|---|---|
| QA-01: early crash blocks resume | Actual child process exits 77 immediately after attempt directory creation. Reopened Factory now accepts. Clean control also accepts | Resolved |
| QA-02: stale accepted artifacts | Clean accepted control stays accepted. Separate workspace, patch and task mutations each become invalidated; resume rejects each | Resolved |
| QA-03: orphan writer races recovery | Real sandbox continuously writes candidate; SIGKILL controller leaves writer alive; Factory.resume with production cleanup stops it, then verifies stable candidate | Resolved for interrupted-run recovery |
| Repair and exhaustion | Existing regression suite retains actual failure evidence, repairs in second attempt, preserves source, stops at budget | Pass |
| Published-verdict recovery | Existing regression confirms no repeated worker call after saved verification | Pass |
| Practical sandbox | Existing real Docker checks prove network isolation, read-only verification mount and command timeout; prior candidate's unchanged sandbox implementation also had host-secret/socket/root-write probes | Pass |
| Export and CLI | Independent patch passes git apply --check, applies expected file change to disposable source; real subprocess CLI status returns accepted without model | Pass |
| False quality success | Existing controlled test rejects zero discoverable tests and scratch artifacts, while complete control passes | Pass |
| Entire maintained suite | 23 tests passed in 3.880 seconds, including real offline Docker execution | Pass |

No new blocking defect found in this focused recheck. The separate cleanup callable directly addresses recovery ordering without introducing a framework. Runner, worker and sandbox remain appropriate responsibilities for this release; no architecture removal is warranted by these checks.

README now explains task preparation, frozen checks, exit codes, resume, patch review and application. Operations documents explicit rollback and setup; architecture states practical isolation limits and attempt/resource bounds. These resolve the prior missing-documentation observation. Remote installation and rollback claims were not independently rerun, as rig actions were excluded. Pilot results explicitly remain pending, which accurately bounds current evidence.

Remaining acceptance work belongs to the broader release: the three live-model scenarios against the final quality contract, complete honest pilot results, and measured coverage with explained gaps. This QA establishes deterministic runtime behavior, not coding competence or hardened hostile-code isolation. Reused candidate1 sandbox evidence is tied to an unchanged sandbox implementation; candidate2 also reran its executable sandbox tests.

## Reproduction and durable evidence

Complete independent probe: [qa-candidate2-probes.py](qa-candidate2-probes.py).
Captured output: [qa-candidate2-probes.log](qa-candidate2-probes.log).
Manifest: [candidate2.json](candidate2.json).

```sh
cd /tmp/gflo-review-candidate2
python3 -m unittest discover -s tests -v
python3 /home/gradrix/repos/gflo/.scratch/fresh-start/evidence/qa-candidate2-probes.py
```

The probe exits nonzero on any unmet expectation. It uses only disposable fixtures, the frozen candidate and the locally installed pinned Docker image. Expected rejection counts as a passing assertion. Output confirms QA-01 controls/recovery, QA-02 all artifact variants, QA-03 actual orphan cleanup, patch application and CLI status.
