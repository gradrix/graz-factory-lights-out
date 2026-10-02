# Document publication and cleanup repair

Original candidate `fba3e2f5fe14c640818808b32242c617b7a2ed78c3b2fbb332e7080764b6f336`, original manifest/report/evidence preserved in commit `dc60ee3`. No original outputs overwritten. Frozen contract unchanged.

New candidate manifest: `builder-candidate-v2.json`, SHA256 `9c01da103e9f145bfc426e4a4c3f02780b85a845594a4716d1437d36c413cb3c`. The manifest binds all nine candidate paths and explicit lineage. Maintained delta from the original candidate: `gflo/documents.py`, `tests/test_documents.py`, `docs/document-evidence.md`. No commits, rig/model calls or shared guardian/package-fetch changes by this builder.

## D1: publication invariant

Confirmed the additional postcommit failure: injecting an `OSError` in staging `Path.exists()` caused acquisition to report failure after publication. Independent D1 additionally demonstrated failed final directory sync plus failed retirement could leave reusable new evidence.

Repair moves verification, pending-marker removal, staging-directory sync, cancellation/deadline checks and output preparation before the final atomic staging-to-ID rename. No rollback is necessary because nothing is visible until this last operation. Acquisition and answer set staging to `None` after successful commit; their finalizers do not stat a vanished staging path. Answer rendering reads its evidence before commit. Tests reject staging-sync and final-rename failures, preserve a prior valid record, prove postcommit staging stat is absent and prove answer does not re-read evidence after commit.

The guarantee is atomic visibility with no reported preparation failure after successful commit. The final parent-directory rename is not followed by another potentially failing fsync; sudden power-loss persistence is not certified. This limitation is explicit in usage documentation and does not claim a tested crash-durability guarantee.

## D2: uncertain executor cleanup

Confirmed all three new regression cases against the old implementation: `TimeoutExpired`, returned124, returned130 each allowed a later valid acquisition without explicit cleanup. Independent findings also explain why the existing guardian can mask cleanup failure with timeout/cancellation status.

Repair installs `.cleanup-required` before launching the executor and clears it only on a zero exit. Exceptions, owner death and any nonzero result leave a reuse fence. Since this guardian does not separately attest cleanup success on failure, even an ordinary rejected helper result conservatively requires explicit cleanup. This avoids trusting diagnostic wording or particular masked status values. Marker creation is exclusive/no-follow; if creation fails the executor is never launched.

This intentionally changes cancellation recovery: even if actual container removal succeeded, explicit `documents cleanup` clears the marker before new work. Tests cover every reported uncertain status, existing125/RuntimeError controls, and recovery. Documentation explains the behavior. Successful normal acquisition needs no cleanup.

## Verification

- Focused suite:31 document tests passed.
- `git diff --check` passed.
- Full `make coverage`: **119 tests passed,86% branch-aware coverage,exit0**; durable log `builder-coverage-v2.log`.
- Actual approved Python docs acquisition passed on repaired source: `builder-acquire-v3.json`, evidence ID `a6f2336a1b4c6705b2f70fd7aefa09b8839f29ca55b25d264561f3e87d144166`. Same approved URL, pinnedPython3.12.13/fb1118 image, no policy exceptions.
- Actual local Docker lifecycle repeat: `local-lifecycle-v2.py`, `builder-local-lifecycle-v2.json`. Controlled stalled-fetch substitution runs the real document envelope/guardian. Both cancellation and owner-SIGKILL observed a running container, then zero remaining containers and no reusable records. Both retained the recovery marker; owner death also retained staging. Explicit cleanup left only `.lock`.

Independent security recheck requested from the original reviewer against this manifest. Model/rig/semantic qualification remains parent-owned and pending; no earlier acceptance is implied.
