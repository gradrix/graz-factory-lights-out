# Seed reader misses same-size rewrites within one timestamp tick

Type: task (maintained-product defect, found 2026-10-09 by Claude Code coordinator)
Status: open, not yet claimed; independent of the ensemble-review route

## Observation

On the rig (`monster-gaming-pc.lan`, WSL2 kernel 6.6.87.2, Python 3.13), the maintained suite fails two subtests of
`tests/test_browser.py::SeedReaderTests.test_write_replacement_and_parent_swap_during_read_are_rejected`
(`same-size`, `restore-mtime`): `read_seed` returns without `ValueError`. Main a073fd2 and integration candidate
0c91359 fail identically (163 and 175 tests, failures=2, skipped=1); every other test passes.

Cause, reproduced: file timestamps on that kernel advance in ~4 ms ticks (successive `stat -c %z` after rewrites
show identical ctime within a tick). `gflo/browser.py` `read_seed` detects a change during copy only by the
identity tuple (dev, ino, mode, nlink, uid, gid, size, mtime_ns, ctime_ns); a same-size rewrite inside one tick
leaves that tuple unchanged, so the test's mid-read rewrite is undetected.

## Question

What change-during-copy guarantee should seed admission give where timestamps are coarse? Candidate routes:
copy-then-verify by content hash against a second pinned read (narrows but does not close the window), refuse
seeds whose mtime/ctime lie within a granularity margin of the read time (forces a settled input), or record the
limit and make the test assert only what stat identity can prove. A choice needs a bounded probe on the rig.
