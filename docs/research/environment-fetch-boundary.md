# Fixed-artifact fetch boundary feasibility

Date: 2026-10-02. Discovery for Stage 3 under [ADR 004](../decisions/architecture/004-environment-snapshots.md), not adoption or qualification. Maintained runtime and cohort D were untouched; no GPU or target-model calls.

## Supported route

A small trusted stdlib client can replay controller-approved **exact artifact URL + SHA-256 + byte limit** records without running pip/npm, package code, or project code online. The disposable implementation accepts only HTTPS, exact `files.pythonhosted.org` / `registry.npmjs.org` hosts, port 443, no userinfo/query/fragment, and no redirects. It makes one IPv4 resolution, rejects the entire answer set if any address is nonglobal, multicast or reserved, then connects a numeric validated address. TLS uses the original hostname for SNI and certificate identity checking; HTTP Host also retains it.

`http.client` exposes the connection and response operations needed without an automatic redirect loop; proxy tunneling is an explicit separate operation which this client never invokes. Socket timeouts bound individual blocking operations; a guardian supplies the total deadline. [Python HTTP client documentation](https://docs.python.org/3.12/library/http.client.html)

Global-address classification alone needs care: shared address space is nonglobal, and multicast is rejected explicitly. This prototype deliberately has no IPv6 path. [Python ipaddress documentation](https://docs.python.org/3.12/library/ipaddress.html)

`ssl.create_default_context()` enables required certificates and hostname checking. Passing the original `server_hostname` is essential even though TCP connects a numeric address. The actual installed 3.12.13 source was inspected and saved; current 3.12 documentation is newer, so it was not treated as proof of identical installed implementation. [Python TLS documentation](https://docs.python.org/3.12/library/ssl.html)

## Measured evidence

Disposable files: `.gflo/environment-fetch-probe/` (`fetch.py`, `negative.py`, `run.py`, `deadline.py`, receipts and installed-source capture). Commands: `python3 .gflo/environment-fetch-probe/run.py` and `python3 .gflo/environment-fetch-probe/deadline.py`. The first repeats a fixed artifact fetch, not resolution. It does not run the earlier `prepare.py`.

| Check | Observed result |
|---|---|
| Actual image | `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, CPython 3.12.13 |
| Existing annotated-types 0.8.0 wheel lock | 13,427 bytes fetched; SHA-256 `f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0` matches frozen resolution/requirements lock |
| Connection | Approved hostname resolved to four global IPv4 addresses; connected `151.101.0.223` with original hostname TLS validation |
| Synthetic negatives | Private, loopback, link-local, shared, multicast, mixed DNS; wrong URL authority/scheme/port; redirect; excess actual bytes; bad hash; certificate-verification exception all rejected |
| Deadline | Deliberately sleeping network-none executor stopped with 124 and confirmed removed |

The online executor used explicit `runc`, nonroot UID/GID, no capabilities, no-new-privileges, read-only root/probe mount, 128 MiB memory+swap, one CPU, 32 PIDs, and 4 MiB temporary filesystem. Only trusted probe files and sanitized fixed lock were mounted, with no project or credential mounts. The 64 KiB artifact limit is checked against headers and streamed bytes; no decompression or artifact execution occurs. The guardian deadline is 35 seconds after creation, with separately bounded create/cleanup operations. Synthetic certificate failure tests propagation and hostname arguments; it is not a live invalid-certificate-server test.

## Boundary and remaining gate

This is a **trusted fetch-client policy**, not a kernel network-namespace egress firewall. Docker bridge can still route elsewhere if arbitrary code executes; DNS itself uses the container resolver. The route is defensible only while the online program, image and approved lock are controller-owned and no untrusted code runs. A client/runtime compromise is outside this policy's protection. If Stage 3 requires containment of arbitrary online code, an independently enforced egress boundary remains necessary.

Before adoption: validate lock/schema and exact URL membership at the controller boundary; integrate complete transport/publication cancellation, cleanup failures, hostile artifact validation and immutable receipts. Offline assembly must use `network=none` with no fallback. This prototype holds and hashes bytes in memory and discards them; it does not implement snapshot transfer, extraction, offline assembly or atomic publication. npm-host fetch, DNS timeout/owner-death fault injection and full cold-cache profile qualification remain untested here. No broader public-only-egress or Stage 3 completion claim is supported.
