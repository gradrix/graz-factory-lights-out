# Independent security recheck: environment store

Date: 2026-10-02. Skill: security-check. Candidate: `6dd3556016ec00ba3e65d0232fe78094edc9587b`. Frozen `gflo/environment.py` SHA-256: `58e6251fdfae97106c3035092f1b0b3ba0a1b267634b9fed76917e0feb325598`.

## Outcome

**Further repair required for failed retirement.** The original publication error is handled correctly when retirement succeeds, and readers now respect the publication lock. A controlled failure of both directory synchronization and the retirement rename still leaves the failed candidate resolvable. No broader Stage 3 acceptance is granted.

## Coverage

Completed the requested store-only recheck on Python 3.10.12. All five frozen maintained tests passed. The independent script recorded 64 successful observations, including the preserved tampering/cancellation/corpus controls and one successful reproduction of the remaining defect. The count is evidence coverage, not an acceptance score.

Confirmed repairs and controls:

- A post-rename directory-fsync failure retires H, preserves G, and leaves no staging after successful cleanup. H cannot resolve afterwards.
- A separate store instance cannot resolve H while the publisher holds the exclusive lock, including after H's directory has been renamed into place.
- A post-rename private-verification error likewise retires H.
- A recursive-cleanup error after successful retirement leaves only private `.prepare-*` staging. H is not resolvable. Further preparation is refused while private cleanup continues failing; explicit reconciliation succeeds after removing the fault.
- Two shared readers can coexist, and a preparation is refused while a shared reader holds its lease.
- Prior-good reuse, receipt/path/content/mode/link tampering, invalid IDs, the 22 corpus rejection cases appropriate to production limits, four cancellation fences, failed verification, oversized receipts, pre-rename errors, and destination-link controls continue passing.

The thirteen frozen receipt scenario plans remain the reference. Their store-level portions have been exercised as described above and in `security-environment-store.md`. Actual offline runs, live producer cancellation/owner death and daemon/executor cleanup remain outside this slice.

## Remaining finding: failed retirement does not revoke reuse

- **Severity:** medium; **confidence:** high for the reproduced behavior.
- **Candidate:** `6dd3556016ec00ba3e65d0232fe78094edc9587b`, new-publication exception handling in `EnvironmentStore.publish`.
- **Trigger:** after staging is renamed to H, directory `fsync` raises. The subsequent `published.rename(stage)` also raises. Both operations depend on the same filesystem, so a failed rollback under an I/O fault is a plausible failure class. The probe uses bounded injected exceptions rather than damaging a filesystem.
- **Evidence:** `retirement-rename-failure-leaves-failed-candidate-resolvable` injects `OSError('controlled publication durability failure')` for directory synchronization and `OSError('controlled retirement rename failure')` only when a final-ID directory is renamed back to `.prepare-*`. `publish` raises the retirement error. After the exclusive lease closes, `resolve('dc6b8de36947cc7349d4be481aac8e8513f7514186c3b87987eaa426ea171971')` succeeds. G remains unchanged. This is a completed reproduction, not a hypothetical consequence.
- **Impact:** failed cleanup permits the failed attempt to be reused. The frozen cleanup/publication contract requires explicit failure and blocked reuse until reconciliation.
- **Smallest useful repair direction:** establish a durable pending-publication marker before moving the tree to its final ID; public resolution must reject pending candidates. Retain that marker through final sync/private verification, and remove it only at the publication commit point. Errors before that point must leave a non-runnable marker even if retirement and recursive cleanup cannot write to the filesystem. Preserve G and existing-ID semantics. An equivalent persistent eligibility mechanism is acceptable; a process-local flag alone would not fence another resolver or a later process.
- **Recheck needed:** failed retirement remains unresolved; pending candidate cannot resolve after process-local state is discarded; successful publication clears eligibility state; a pending same-ID candidate cannot be reused as good; final marker-removal failure remains blocked. Preserve the already passing reader/failure/cancellation controls.

## Retrievable evidence

Track only this report, `security-environment-store-recheck/probe.py`, and `security-environment-store-recheck/results.json`. The original-candidate evidence remains in `security-environment-store.md` and its sibling probe/results directory.

```sh
python3 .scratch/.sflo/04-autonomy-environments/security-environment-store-recheck/probe.py
```

The script reconstructs exact trusted files from candidate Git history into ignored `.gflo/security-environment-store/6dd3556016ec00ba3e65d0232fe78094edc9587b/`, runs probes and the five frozen maintained tests, and stores rerun observations there without overwriting the retained original JSON. No duplicate source/test/corpus files need to be published.

## Boundaries

Controller-owned store; no untrusted concurrent host writer; controlled trusted verification callbacks. No model, network, container, rig, GPU, or maintained-code mutations. This assessment does not establish preparer supervision, host-crash durability, offline runtime evidence, or task-binding integration.
