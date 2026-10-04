# SEC-B5: deterministic guardian facts permissions

Original v3 source at91b1e76, its manifest and independent evidence remain unchanged. New frozen manifest `builder-candidate-v4.json` SHA256 `b9f0c1c64dc9f3802c7bf0d34997a648cdec383efd3a34d8570572ead61a216f` binds all nine maintained paths and explicit lineage to v3 `bbcd59aa9ba4223a022eb0c7d0915188b530b5a35308897384d3594fdfa04da3`.

## Reproduction and repair

Independent B5 identified that guardian `open(...,'x')` inherited the caller's umask while recovery required mode0644. The new actual local regression starts the real guarded app/browser pair under each umask, kills its controller after both containers are running, waits for guardian cleanup and a complete retained facts record, then invokes public recovery.

Red evidence `builder-b5-red.log`:

- umask002 produced0664, violating the intended private0600 facts mode.
- umask077 produced0600, but public recovery failed because it required0644.

The writer now exclusively creates facts with `O_NOFOLLOW` and mode0600, explicitly applies0600 through the open descriptor, writes/flushes/fsyncs, and closes. Recovery validates the same exact0600 mode plus existing regular-file/owner/link/size checks. Validation was not widened to accept group/world-writable evidence. Only `gflo/browser_pair.py`, `gflo/browser.py`, and the live regression in `tests/test_browser_live.py` changed from v3.

## Verification

`python3 -m unittest discover -s tests -p 'test_browser*.py'`: **26tests passed in38.713s**, exit0. Durable output `builder-b5-green.log`. This affected suite includes both actual umask owner-death/recovery paths, five application journeys, second-context trace validation, B1–B4 regressions, actual origin/WebSocket/readiness negatives, daemon logging readback, and controlled creation uncertainty.

For both umasks the new facts mode was0600, no owned containers remained, explicit recovery cleared the fence/staging, and earlier immutable support remained. The test reads the complete JSON before recovery to avoid mistaking an in-progress private write for a completed guardian record. `git diff --check` passed.

The prior v3 full gate remains144tests/86%; no new full-suite or coverage claim is made for this narrow permission repair. No rig/model calls, service changes, commits or edits to coordinator metadata. Existing frozen v3 evidence is not rewritten or permission-normalized. Independent affected-seam recheck remains pending against this v4 identity.
