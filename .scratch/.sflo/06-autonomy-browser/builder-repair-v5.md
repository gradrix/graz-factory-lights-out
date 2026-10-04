# Rig seed-copy false rejection: v5 repair

V4 source6852a20, manifest and first failed rig trial remain preserved. The trial passed create-reload in1.720s, then refused validation before launch with `Seed changed during copy`; its final input/support hashes still matched. No failed result is relabeled a pass.

## Diagnosis

The old seed guard compared whole `stat_result` objects around its read. An isolated temporary-file probe on monster-gaming-pc.lan reproduced **only `st_atime_ns` changing**, with device/inode/mode/link count/owner/group/size/mtime/ctime unchanged. The old comparison nevertheless rejected the read. Evidence: `builder-seed-atime-rig.json`.

The repaired exact reader was transmitted only as a temporary stdlib probe, not installed or run as an application/browser. It accepted the same atime-only read; the old comparator would still reject. `builder-seed-fixed-rig.json` binds the tested function SHA256 `1800a85f224b27d50a07e608335ad6e53a8c25cff4708ec0a9ea459a66493b17`. Temporary probe files were removed; no services, model calls or rig browser runs occurred.

## Coherent input-seam repair

Only `gflo/browser.py` and `tests/test_browser.py` changed from v4. The seed reader now:

- Resolves parent components with directory descriptors and `O_NOFOLLOW`, retaining a pinned parent.
- Requires an ordinary single-link file of at most64KiB before reading.
- Opens the final file with `O_NOFOLLOW|O_NONBLOCK`; the latter prevents a regular-to-FIFO race from blocking before descriptor validation.
- Matches the opened descriptor to the pre-open source using device/inode/mode/link count/uid/gid/size/mtime_ns/ctime_ns.
- Reads at most65537bytes, rechecks descriptor metadata, resolves the final parent without links, and checks final parent/file identity and exact length.
- Excludes access time, which reading may legitimately change. Same-size content writes, restored mtime with changed ctime, replacement, and links remain rejected.

JSON validation and immutable private seed storage are unchanged. This is a seed-specific correction, not a general storage refactor or weakened mutation check.

## Verification

The initial host regression exposed an additional existing hard-link acceptance; it now rejects before pair launch. Focused controls cover synthetic atime-only descriptor changes, actual old-atime input, same-size write, truncation, write followed by restored mtime, file replacement, parent replacement, and symlink/FIFO/hard-link swaps between metadata inspection and open. The original rig atime-only behavior is independently reproduced as above.

`python3 -m unittest discover -s tests -p 'test_browser*.py'`: **31tests passed in39.116s**, exit0. Durable output `builder-seed-green.log`; initial host red output `builder-seed-red.log`. The affected suite retains five real local application journeys, trace checks, origin/health/WebSocket controls, pair lifecycle and both umask recovery cases. `git diff --check` passed. No new full-suite coverage claim is made for this narrow fix.

New immutable identity is `builder-candidate-v5.json`, SHA256 `ee60bbe4012e03acbcd5a9cd403a63f62290dd253c97a7f7979ead062ee53ea4`; its nine bound source/test/docs files retain all unaffected v4 hashes. Independent seed-seam security review and a fresh-directory rig trial remain coordinator/reviewer owned. No commits or coordinator metadata edits by builder.
