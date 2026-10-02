# Preparation phase interruption QA

**PASS for the remaining fetch/final-smoke interruption scope**, frozen `25f75c3275739cc7cc2a4fc5a4e16580b81511d1`.

| Phase | Independent probe and result |
|---|---|
| Online fetch | A private trusted helper copy pauses for 60s immediately before DNS resolution and emits a marker. Actual preparation launches its normal bridge-network fetch container; the 3s preparation deadline stops it with code 124. Marker confirms the intended blocked-DNS simulation was reached. The exact inspected container is absent afterward; no reusable receipt exists. No DNS lookup or external connection occurred. |
| Final publication smoke | First create a valid stdlib receipt. On the next preparation, wait until the second smoke invocation and assert `.prepare-*` staging exists. Only this smoke command is delayed; cancellation fires after 2s. Actual smoke executor exits 130 with its marker. All owned containers disappear, staging/scratch disappear, published file hashes remain identical and the prior receipt resolves unchanged. |
| Recovery | Another unmodified preparation succeeds and returns the same prior-good environment ID. |

[Executable probe](qa-preparation-phase-interruption/probe.py), [results and inspected executors](qa-preparation-phase-interruption/results.json), [log](qa-preparation-phase-interruption/probe.log).

```sh
python3 .scratch/.sflo/04-autonomy-environments/qa-preparation-phase-interruption/probe.py
```

These are deliberate waits inside real preparation containers, not observations of a real registry outage. The helper and smoke command changes exist only in a disposable copy/process; maintained recipes are untouched. Earlier [lifecycle QA](qa-preparation-lifecycle.md) supplies actual assembly timeout/cancellation/owner-SIGKILL and resource evidence; [cleanup recheck](qa-profiles-recheck.md) supplies outer-cleanup failure preservation. No new defect found. No model/GPU/rig/shared-service changes or overall Stage 3 acceptance claim.
