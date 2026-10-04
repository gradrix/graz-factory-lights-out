# Browser v5 focused seed security recheck

2026-10-04. **Outcome: PASS for the seed-copy repair. Coverage: exact source delta plus24 focused controls; no broad suite, Docker, rig or model rerun by this reviewer. No scoped blocker to the next rig trial.** Earlier rig failure and v2–v4 evidence remain unchanged.

## Frozen identity and unchanged boundary

Commit **`596ecb6`**, [builder-candidate-v5.json](builder-candidate-v5.json) SHA-256 **`ee60bbe4012e03acbcd5a9cd403a63f62290dd253c97a7f7979ead062ee53ea4`**. All nine maintained paths match at entry and final readback; private reconstructed runtime and committed bytes match too. [Before](security-browser-v5/hashes-before.json), [after](security-browser-v5/hashes-after.json).

Relative to v4 `6852a20`, only `gflo/browser.py` and its unit test changed. [Runtime delta](security-browser-v5/source-delta.patch) adds `read_seed` and replaces the former full-stat seed comparison with that helper. Pair guardian, permissions/recovery semantics, cancellation publication fence, container arguments, browser helper/seccomp, origin/logging policy and artifact parser are unchanged. [V4 security evidence](security-browser-v4.md), including its explicitly carried B1–B4 evidence, remains applicable to those unchanged boundaries.

## Independent evidence

[seeds.py](security-browser-v5/seeds.py), [seed-results.json](security-browser-v5/seed-results.json):

- **Actual atime-only change passes.** The checkout mount did not advance access time, which its rows report honestly. A separate tiny reviewer-owned temporary file under `/dev/shm` did undergo a real read-induced atime change while mtime/ctime stayed unchanged. `read_seed` returned its exact bytes; the old full-stat inequality was true and would reject that same transition. No atime stat value was mocked. Temporary files were removed.
- **Bounds remain strict.** Ordinary2-byte and exact65,536-byte inputs pass.65,537 bytes, directory, source symlink, symlink ancestor, hardlink and FIFO reject without reading the file. Valid reads request at most65,537 bytes.
- **Before-open substitution rejects.** Regular-file replacement, symlink replacement and FIFO replacement are introduced between the initial metadata check and descriptor open. All reject before a read; the FIFO path does not block.
- **During-copy changes reject.** Controlled hooks perform actual filesystem operations after the bounded read and before final checks: same-size content rewrite, truncate, rewrite followed by restoring mtime, leaf replacement, parent-directory replacement, adding a hardlink and changing file mode. Every case rejects. The restored-mtime case retains its original mtime but changes ctime, so the rejection does not depend solely on mtime.
- **Public call boundary holds.** The store accepts the aged-atime ordinary seed using a controlled passing executor. Hardlink, FIFO and symlink seeds each fail with zero pair calls. These are public-seam tests with a controlled executor, not actual container launches.

The new source walks parent directories with no-follow directory descriptors, validates the leaf without following links, opens it with no-follow/nonblocking flags, and checks descriptor and final path identities. Stable identity includes device/inode/mode/link count/UID/GID/size/mtime/ctime; atime alone is excluded. Reopening the parent chain detects the measured parent replacement. JSON validation, fixed private copy and receipt digest still occur before executor launch. This does not establish resilience against a malicious privileged host writer; controller ownership remains the contract assumption.

## Reproduction and verdict limit

Run `python3 .scratch/.sflo/06-autonomy-browser/security-browser-v5/seeds.py` from the repository. Its local helper reconstructs `596ecb6` under ignored `.gflo/browser-security-v5/frozen/`; no duplicate runtime tree is published. Results are overwritten by a rerun, so preserve them first. The actual atime test requires ordinary `/dev/shm` access-time behavior; a different mount policy must be reported rather than treating unchanged atime as an observed transition.

No maintained file was edited and no existing failed rig record was modified. The coordinator's pending real rig qualification and full unit acceptance remain separate. This repair neither expands target authority nor relaxes content/mutation checks, and it does not imply full Stage4 acceptance.
