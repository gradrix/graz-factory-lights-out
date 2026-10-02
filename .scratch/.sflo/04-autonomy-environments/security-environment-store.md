# Independent security assessment: environment store slice

Date: 2026-10-02. Skill: security-check. Candidate: `1506abf89cceb8e9adf1a446caf9d92ad53c29c2`. Frozen `gflo/environment.py` SHA-256: `6912a7850535ce614cced92c499cbd71e624b87cf9134bd02b456c5af89e38c4`.

## Outcome

**Repair required:** publication can fail after the new environment becomes resolvable, and public resolution does not participate in the publication lock. The reproduced failure leaves a failed attempt reusable. Other tested receipt, tree, cancellation-fence and private-cleanup checks behaved as intended. This assessment grants no preparer or Stage 3 acceptance.

## Coverage

Completed the narrow host-only store review under Python 3.10.12, using frozen commit files reconstructed from Git into ignored `.gflo/security-environment-store/1506abf89cceb8e9adf1a446caf9d92ad53c29c2/`. Inspected the accepted contract and all 13 frozen receipt/publication scenario plans. All three maintained store tests passed. The independent script recorded 60 successful observations; one observation intentionally reproduces the finding, so that count is not an acceptance verdict.

The script covers:

- Valid deterministic publication, idempotent existing-ID reuse, exact metadata/tree binding, and controller-derived dependency paths.
- Eighteen independent tampering variants: bytes, removal, addition, rename, execution/write modes, directory/root modes, file/directory symlinks, FIFO, receipt image/lock/tree binding, receipt mode/link, publication mode, and wrong expected receipt hash. Each was rejected.
- Six invalid identifier controls, including traversal, absolute paths, malformed hashes, suffixed paths and non-string input.
- Twenty-two rejecting corpus archives through `publish`, with known-good receipt/tree verified after every failure and no failed publication or leftover staging. Three fixture rejection cases whose small test-only count/expanded/transport limits are below production defaults were excluded; the archive helper's separate assessment covers those configured limits.
- Cancellation before reading, after transport, during trusted smoke, and at the final receipt-fsync fence; failed/throwing smoke, changed dependencies during smoke, oversized receipt, and pre-rename publication failure. Each preserved the good environment and removed staging.
- Cleanup failure remained explicit, retained only private staging, blocked another preparation while cleanup continued failing, and allowed reconciliation after the fault was removed. Concurrent preparation was refused. A symlink at the predicted new final ID was rejected without changing its target or the good receipt.
- A controlled post-rename directory-fsync failure, including a separate store instance resolving the new ID while the publisher still held its exclusive lock, reproduced the finding below.

The callback boundary is trusted: `publish` documents a trusted-preparer seam, and at this commit `git grep` finds `EnvironmentStore` used only in `gflo/environment.py` and its tests. No model-facing dispatch, caller-supplied arbitrary callback API, receipt import, or actual preparer exists in this candidate. The probe callbacks are controlled verification substitutes; their success does not establish real offline execution or smoke evidence.

## Finding: a failed publication remains resolvable

- **Severity:** medium; **confidence:** high, reproduced.
- **Affected code:** `gflo/environment.py:168` renames staging to its final receipt ID. Directory `fsync` and final `resolve` at lines 169–171 can still raise. The `finally` at lines 172–174 only removes the former staging path, which no longer exists. `resolve` at line 184 does not acquire the store lock.
- **Trigger:** an ordinary controller I/O error during final directory synchronization or final verification after rename; an attacker is not required. This violates the failure boundary relied upon when processing untrusted dependency archives.
- **Reproduction:** publish baseline G; publish a distinct H with a successful controlled smoke result; raise `OSError('controlled post-rename directory fsync failure')` only when `fsync` receives a directory descriptor. H's `publish()` raises, but H remains at ID `dc6b8de36947cc7349d4be481aac8e8513f7514186c3b87987eaa426ea171971` and `resolve(H)` succeeds afterwards. A separate `EnvironmentStore` instance also resolves H during the injected `fsync`, while the original publication lock is still held. G remains unchanged and no `.prepare-*` is left.
- **Impact:** another controller path can obtain a usable environment whose publication failed or has not completed its final durability/verification steps. The frozen `publication-failure` expectation requires H to be absent or explicitly failed; failed attempts must not silently become reusable.
- **Repair direction:** hold the exclusive publication lock through final acceptance; make public resolution acquire a compatible shared lock or fail promptly while publication is busy. Use a private resolver for checks performed under the publisher's own lock. Track only a newly renamed destination, and on a later error retire it to a private staging name before recursive cleanup. That keeps cleanup failures explicitly non-runnable and preserves preexisting good IDs. Recheck post-rename fsync/verification failures, temporary resolver refusal, failure during retirement/cleanup, and normal existing-ID reuse.

## Limits

The review assumes controller-owned store paths and no untrusted concurrent host filesystem writer. It does not test model/API routing that has not been implemented. The frozen scenarios requiring two real offline executions, producer/executor removal, cancellation during a blocked stream, owner death, daemon cleanup failure, and runtime/device/network isolation remain integration obligations. The cancellation probe at transport EOF shows a store publication fence; it does not establish interruption of a blocked `read`. No model, network, container, rig, GPU or maintained-code mutations occurred.

## Retrievable evidence

Publish only this report, `security-environment-store/probe.py`, and `security-environment-store/results.json`. The JSON preserves the original candidate identity, source hash, runtime and observations. The script reconstructs the exact trusted commit files via `git show`, so duplicate source/test/corpus trees are not needed in a clean checkout. Rerun results are saved separately under the ignored candidate directory.

```sh
python3 .scratch/.sflo/04-autonomy-environments/security-environment-store/probe.py
```

The script runs all probes plus the three frozen maintained store tests and returns failure on a probe or unit-test failure. The intentional finding probe asserts the original faulty behavior; use a separate repaired-candidate recheck before acceptance.
