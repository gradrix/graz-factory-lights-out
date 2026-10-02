# Read-only security code review: approved environment preparer

Date: 2026-10-02. Skill: security-check.

Original frozen candidate: `51479e9663f810e33031774abceca067cd761a48`.
Source-level repair recheck: `25f75c3275739cc7cc2a4fc5a4e16580b81511d1`.

## Outcome

One actionable cleanup/publication defect was found in `51479e9`. The code change in `25f75c3` addresses it: the preparer's remaining transport/workspace cleanup completes before the store can commit the receipt. No additional actionable defect was identified in the bounded source review of approved URL validation, digest checks, fixed executor arguments, recipe assembly, manifest parsing and receipt publication.

This is a **source-review result only**. Full security qualification and Stage 3 acceptance remain incomplete.

## Finding in the original candidate

**Medium severity; high confidence from control flow.** Outer workspace cleanup occurred after the receipt became reusable.

At `gflo/prepare.py:193`, `prepare()` returns `store.publish(...)` while still inside `with preparation(store)`. The store removes its pending marker at `gflo/environment.py:181`, committing the receipt before returning. Only afterwards does the enclosing context manager execute `discard(work)` at `gflo/prepare.py:59`.

If that discard raises, `prepare()` fails after it has already created a resolvable new environment. The store's rollback cannot cover the error because its publication call has finished. This violates the accepted requirement that cleanup failure prevent acceptance/reuse of the failed attempt. It is distinct from intentionally preserving a preexisting good environment after a later failed operation.

This reviewer did not run a reproduction. The implementation owner separately reported a real stdlib preparation with injected cleanup failure that left a resolvable receipt, then supplied the repair. That reported execution is not counted as independent runtime coverage here.

## Source-level recheck at 25f75c3

The repair provides a cleanup closure from `preparation()`. The closure marks cleanup complete only after `discard(work)` returns successfully; later calls perform no cleanup I/O once completion is recorded.

The trusted publication verification callback now:

1. Completes the final offline smoke call and captures its evidence.
2. Closes the original archive stream.
3. Successfully removes the outer preparation workspace.
4. Returns to the store, which still needs to verify its staged tree, enforce cancellation, write/verify the receipt and remove the pending marker.

This ordering is sound in the reviewed code. `unpack_archive()` has fully consumed the input and created the store-owned staging tree before the callback runs. Closing the original archive and deleting the separate `.work-*` directory therefore do not remove data needed for the store's remaining verification. If cleanup fails, the callback raises while publication is still uncommitted. The store handles its own staging failure; outer cleanup may retry, but no new receipt has been committed. After successful publication, the outer cleanup closure is already complete and the archive is already closed.

Cancellation and the overall preparation deadline are checked again by the store after the callback, so time spent on cleanup does not skip the final publication fence. Existing-good reuse remains separate from committing a new candidate.

## Source coverage and observations

### Approved fetch boundary

Reviewed `gflo/recipes/fetch.py` and both approved `artifacts.json` files.

- URLs must use HTTPS, exact allowlisted registry hosts, and the default or explicit 443 port. Credentials, queries, fragments, non-ASCII/control characters and backslashes are refused. Output names use a bounded filename character set without path separators.
- All IPv4 DNS answers are checked; an empty answer or any address classified as non-global, multicast or reserved is refused. The client connects to a checked numeric address directly while retaining the original hostname for TLS verification. It does not resolve again at socket connection time.
- The code uses a default validating TLS context and an explicit socket/HTTPS connection. No proxy configuration or redirect handler is used. Only status 200 and identity/no content encoding qualify.
- Declared length, actual bytes and digest are checked. Only SHA-256 and SHA-512 with exact lowercase digest lengths are accepted. Each artifact is capped at 16 MiB; the fixed input list is limited to 32 artifacts, duplicate filenames are refused, and total fetched payload is capped at 64 MiB.
- Socket operations use a ten-second timeout. DNS itself has no local timeout in this helper; the enclosing guarded executor receives the remaining preparation deadline. That composition requires runtime qualification, especially for blocked resolver/cleanup behavior.
- These restrictions implement a trusted-client boundary. The online executor uses Docker bridge networking; the source does not establish a network firewall restricting every possible process connection to registry destinations.

### Fixed code and offline assembly

Reviewed `prepare.execute()`, both assembly helpers, the Node smoke helper, approved manifests/locks and the Python smoke code.

- Preparation selects from three fixed profiles and immutable image IDs. It refuses missing images rather than pulling. Docker arguments are constructed by controller code; project manifests do not supply image, mount, runtime or arbitrary Docker flags.
- The online call runs only the fixed Python fetch helper and mounts the maintained approved recipe directory read-only. Project source is not mounted into online acquisition, and fetched bytes are hashed and placed in an archive rather than imported or executed there.
- Assembly and smoke calls use network none. Python installation uses fixed hashed wheels, no index/cache/dependency resolution, and binary-only installation. Node assembly uses an explicit sanitized npm environment, offline mode, ignored lifecycle scripts, and the approved copied lock/manifest. Those two files must remain byte-identical after installation.
- Node assembly removes only the two known TypeScript convenience symlinks after checking their exact layout; remaining special/link entries fail validation. The host archive reader independently rejects links and unsupported entries.
- Executor arguments request runc, nonroot host UID/GID, read-only root, all capabilities dropped, no-new-privileges, explicit memory/swap/CPU/PID/shared-memory limits, and capped `/work` and `/tmp` tmpfs mounts. Passed bind mounts are read-only. No Docker socket, host home, credential directory or GPU device argument appears in this template.
- This establishes requested configuration in code. The helper verifies the inspected image identity and records projected execution facts; real resource/device/credential absence was not verified in this pass.

### Artifact, manifest and receipt handling

- Binary transport requests the existing 128 MiB cap. Host extraction uses the previously reviewed bounded archive helper for fetched artifacts and assembled dependencies. The complete fetched filename set must match the approved artifact list, and the controller rechecks each digest and size before assembly.
- The receipt metadata binds approved files, complete approved lock files, fetched artifact hashes, recipe/preparer/fetch identity, immutable image identity and observed runtime. The store supplies the dependency-tree and smoke evidence binding.
- Project validation copies only the required regular, non-linked manifest files, rejects files over 64 KiB, and parses the copies with fixed code in an offline capped interpreter. Python build-system and direct dependency declarations must match the supported recipe. Node dependency declarations and the complete non-root package lock entries must match the approved lock; scripts, workspaces and overrides are rejected.
- Manifest parsing does not import project source or execute a project build backend. Project build/execution, where permitted, remains a separate offline boundary; this review does not establish application correctness or complete qualification scenarios.
- Preparation has a separate lifetime lock and a shared overall deadline passed through container phases and final publication fencing. Source review confirms explicit failure paths for unsuccessful containers, invalid output, hash/size mismatch, unsupported runtime and cancellation. It does not prove actual cancellation latency, cleanup completion or resource exhaustion behavior.

## Method and limits

Only local read-only `git show`, `git diff`, tree listing and source inspection were performed for this pass. The only written artifact is this requested report. No target code or maintained tests were executed, no dynamic probes or failure injections were performed, no containers were started, and no external requests or system changes were made.

The earlier archive, store and controlled-transport reports remain evidence for their exact frozen slices. They do not constitute independent end-to-end qualification of this preparer candidate. In particular, this pass does not establish actual Docker producer cleanup after owner death, interruption of blocked network/transport operations, enforced live cgroup limits, absence of credentials/socket/GPU devices in real executors, real daemon-outage handling, host-crash durability, dependency vulnerability status, or task-binding integration. The implementation owner's reported suite results were not independently rerun or upgraded into security evidence.

Before full acceptance, renew the outer-cleanup failure regression and relevant publication/cancellation checks against the integrated candidate, then complete the remaining live executor and frozen profile-scenario gates. No full security or Stage 3 qualification is claimed here.
