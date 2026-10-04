# Prototype checkpoint boundary: early security review

2026-10-04. Contract `d52ae8c2f322f417fed6c8cf6ace5343720cc40f86f0d0aeb6b9294e2fc33bea`. Emerging disposable source `/home/gradrix/repos/gflo-planning-prototype/ops/planning_pilot_prototype.py`; not a frozen candidate verdict. Read-only source inspection; no model, rig, Git-hook execution or maintained mutation.

## Concrete boundary requiring closure

At inspection, `checked_tree` admitted arbitrary regular `.git` metadata, then `checkpoint` called ordinary `gflo.runner.git` for init/add/commit. Reinitializing copied Git metadata can preserve project-selected hooks/config. The host Git invocation inherits host environment/config; `.gitattributes` may select configured filters, or `export-ignore`/`export-subst` may change archived source. `.gitignore` can exclude accepted files from ordinary add. The existing Factory also invokes host Git through both `git` and `_snapshot_git`; protecting only the new commit command leaves other entry points.

These are source-supported risks, not an observed compromise. Builder was notified before freeze. Minimal prototype boundary: reject reserved Git control artifacts before host Git inspects model-produced data, and use a controlled Git environment/config, disabled hooks and empty template path across every prototype Git seam. Force-add intended content or reject unsupported ignore controls; do not silently drop accepted content. Preserve authoritative project bytes or fail the arm. Environment scrubbing must include Git configuration injection and repository-selection variables, not merely replace HOME. No runtime repair is authorized in this unit.

## Authorized mode restoration

Root authorizes restoration only in fresh task2 workspace while pending/attempts0, never in task1 or contracts. Before restoration, verify exact file/directory set, types and file bytes against the accepted checkpoint; reject links, hardlinks and special files. Restore only the frozen0777 permission bits. Reject unsupported special permission bits rather than silently normalizing an accepted source. Bind mode-map SHA256 and record before/after identities.

`runner.fingerprint` binds file0777/content and entry names but does not bind directory modes. Therefore explicit directory-mode verification is additional evidence, not something proved by equal fingerprints alone. Git archive does not represent empty directories; missing entries must fail under the exact-set precondition. Git executable bits, source/base tree and index must remain unchanged by restoration. Final task2 fingerprint plus full mode map must match accepted task1; verify original task1 remains accepted and untouched. Perform state checks/restoration under the Factory lease before worker dispatch.

## Required focused controls on frozen prototype

- Model-created `.git/config`, `.git/hooks/pre-commit`, nested `.git` or `.git` indirection refuses before host Git; harmless sentinel remains absent.
- `.gitattributes` selects a controlled host filter, and export-ignore/export-subst variants: no sentinel execution or silent byte/set change. Inherited global/system/config-environment/template hooks cannot influence host Git.
- Ignore patterns cannot remove accepted files from checkpoint; ordinary conforming source succeeds.
- Wrong bytes, missing/extra path, type replacement, symlink/hardlink/special file, executable-bit mismatch, special permission bits and changed source refuse restoration.
- Non-executable permission differences restore to the frozen map only while pending/attempts0; directory modes, final full fingerprint and Git tree/exec modes verified. Running/attempted/accepted task2 refuses.
- Task1 source, receipt/patch/contracts and prior-good state remain unchanged; evidence includes hashes and before/after mode maps.

Coverage is **pending frozen harness and independent controls**. This plan neither accepts the prototype nor expands service/model authorization.

## Separate cancellation contract review

Reviewed `cancellation-probe-contract.md` SHA256 `3e9489bddae8eca7df79e9770118b07c860469ffadd3849f91bc34e1d5a89176`. Its one-request,60second work/150second cleanup, unchanged-service and frozen-admission boundaries are sufficient for the stated narrow measurement. Two concrete driver obligations were sent to root: `idle:false` alone is not positive busy (require valid same-identity slot with `is_processing is True`); and preserve the race with normal completion (recheck client alive before signalling, retain termination status and whether a complete response arrived, classify completion-before-stop as inconclusive). The sole POST should use the existing ModelWorker.request seam and durable pretransport debit. No inference execution was performed or admitted by this review.
