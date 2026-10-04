# Browser v4 focused independent security recheck

2026-10-04. **Outcome: PASS for B5 and affected recovery controls; no blocker in this scoped review to proceeding with target-rig qualification. Coverage: exact source delta, actual local owner-death/recovery under two umasks, controlled creation uncertainty and acknowledgement.** This does not accept the complete browser unit or full Stage4. No model calls, rig operations, maintained edits or shared-service changes.

## Candidate and carried evidence

Immutable commit **`6852a20`**, [builder-candidate-v4.json](builder-candidate-v4.json) SHA-256 **`b9f0c1c64dc9f3802c7bf0d34997a648cdec383efd3a34d8570572ead61a216f`**. All nine manifest paths match before/after, including the private reconstructed runtime and immutable commit. [Before](security-browser-v4/hashes-before.json), [after](security-browser-v4/hashes-after.json).

Compared with v3 `91b1e76`, the only maintained runtime changes are guardian facts creation with exclusive/no-follow mode0600, explicit descriptor chmod0600, flush/fsync, and the recovery reader's matching strict0600 check. The changed live test adds the umask regression. [Exact runtime delta](security-browser-v4/source-delta.patch). Browser helper/profile, fixed logging options, redirect/WebSocket policy, readiness fetch, publication cancellation fence and create-uncertainty classification are unchanged.

Consequently the bounded B1–B4 closure evidence in [the v3 recheck](security-browser-recheck.md) carries forward for those unchanged paths. The v2 original report and v3 B5 failure are preserved; no earlier result was rewritten as a pass. The new checks below cover the changed writer/reader and their interaction with recovery.

## Actual owner death and recovery

[owner_modes.py](security-browser-v4/owner_modes.py) reconstructs v4 into ignored `.gflo/browser-security-v4/frozen/`. For each inherited umask002 and077 it prepares a private store, runs an actual passing fixture result, starts a fresh pair with a reviewed waiting journey, observes **both owned containers running**, then SIGKILLs only its controller process. The detached candidate guardian performs its ordinary owner-EOF cleanup. The probe waits for a complete retained JSON facts record and successful empty daemon listing, then calls the public recovery API without exceptional acknowledgement.

Both cases passed:

- Facts mode is exactly0600 regardless of umask.
- Both exact owned containers are absent; owner exit is-9.
- Guardian reports cleanup confirmed with no uncertain create.
- Ordinary cleanup succeeds, clears incomplete staging/fence, and preserves the prior passed result and support receipt.
- Recovery publishes immutable original guardian facts with the matching byte hash. `operator_acknowledged_create_uncertainty` is false, correctly distinguishing this measured ordinary cleanup from exceptional operator acknowledgement.

Full facts, identities and timings are in [owner-mode-results.json](security-browser-v4/owner-mode-results.json). Successful final owned-label readbacks are in [final-absence.json](security-browser-v4/final-absence.json). Four actual pairs were used: a positive fixture and interrupted pair for each umask. No copied helper or permission normalization was used in these v4 owner-death checks.

## Uncertainty and acknowledgement regression

All six independent [recovery cases](security-browser-v4/recovery-results.json) pass through [recovery.py](security-browser-v4/recovery.py): explicit uncertain create, guardian exception, missing facts, retained uncertain facts at the required0600, recovery-commit sync error and absence-query error.

Ordinary cleanup refuses uncertain completion and preserves original bytes; new admission remains blocked; prior good remains inspectable. Acknowledgement plus current absence commits original failure evidence/hash and the explicit statement **`currently absent; not proof of create completion`**, then permits admission. Sync/query failures leave the original evidence and fence until the successful controlled retry. This validates the selected acknowledgement semantics; it does not establish completion of a real delayed daemon request.

The nine [guardian controls](security-browser-v4/guardian.py) also pass under [umask002](security-browser-v4/guardian-results-umask002.json) and [umask077](security-browser-v4/guardian-results-umask077.json): clean pair; timeout/nonzero/transport/malformed/invalid-encoding create outcomes; second-create timeout; removal error; absence-query error. All six ambiguous creates remain explicitly unconfirmed, and both other cleanup errors remain unconfirmed. These command failures are deterministic injections, not actual daemon disruption. Actual writer permissions are established by the owner-death cases above.

## Scope and reproduction

Run the named Python probes from the repository using their full path. They reconstruct `6852a20` into ignored private storage. Actual owner tests require the existing pinned images and approved local package archives, with no image pull. Scripts write their own result files, so preserve existing results before rerunning. The copied `probe.py` supplies the previously reviewed synthetic fixture for controlled seams; the broad v3 matrix was not rerun unnecessarily.

This assessment supports moving to the assigned rig gates. It does not replace five-journey functional QA, actual target-rig renderer/shared-memory/resource evidence or the coordinator's final contract decision. Kernel/browser exploit resistance, hostile controller writers, host power-loss durability and actual shared-daemon outage remain outside the demonstrated boundary.
