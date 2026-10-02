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

Before adoption: validate lock/schema and exact URL membership at the controller boundary; integrate complete transport/publication cancellation, cleanup failures, hostile artifact validation and immutable receipts. Offline assembly must use `network=none` with no fallback. This prototype holds and hashes bytes in memory and discards them; it does not implement snapshot transfer, extraction, offline assembly or atomic publication. DNS timeout/owner-death fault injection and full cold-cache profile qualification remain untested here. The follow-up below separately tests the npm host and offline cache route. No broader public-only-egress or Stage 3 completion claim is supported.

## Follow-up: seed npm offline from fixed tarballs

**Observed: yes, for this complete three-dependency lock.** A separate `.gflo/environment-fetch-probe-v2/` keeps the first probe intact. Its trusted Python fetcher downloaded only the existing lock's exact `registry.npmjs.org` tarball URLs, using the same address/TLS policy and a 16 MiB per-artifact cap. Each lock SRI was decoded as SHA-512, checked before writing bytes, and independently rechecked on the host. Download sizes: @types/node **434,049**, TypeScript **4,250,436**, undici-types **21,020** bytes. No resolver or online npm process ran.

The fresh offline container used immutable Node image `sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0`, actual **Node v22.23.3 / npm 10.9.9**. It started with **zero cache entries** in new tmpfs, copied only approved package/lock manifests into its project directory, and supplied empty controller-created user/global npmrc files plus a small explicit subprocess environment. No host/project npmrc or credentials were mounted. Commands succeeded:

```sh
npm cache add /tarballs/0.tgz --offline --ignore-scripts
npm cache add /tarballs/1.tgz --offline --ignore-scripts
npm cache add /tarballs/2.tgz --offline --ignore-scripts
npm ci --offline --ignore-scripts --no-audit --no-fund
```

Both manifests remained byte-identical. npm installed TypeScript **5.8.3**, @types/node **22.15.3**, and undici-types **6.21.0**. An explicit TypeScript compiler invocation type-checked Node `Buffer` plus `undici-types` and compiled a smoke program whose output was `GET:cpu-only`. The entire cache-add/install/compile/run phase used `network=none`, explicit runc, nonroot user, read-only root, dropped capabilities, 512 MiB memory/swap, one CPU, 64 PIDs, 256 MiB work tmpfs, 16 MiB temporary tmpfs, and a 150-second guardian deadline. The online phase had no package/project manifests or code mounted, only trusted fetch code, sanitized URL/SRI records and its output directory.

This uses documented `npm cache add` behavior rather than writing npm cache internals. npm describes the cache as content-addressed and integrity-checked, but not reliable persistent storage; retain verified tarballs and locks as the durable inputs. [npm cache documentation](https://docs.npmjs.com/cli/v10/commands/npm-cache/). `npm ci` requires an existing compatible lock and avoids rewriting manifests; lifecycle scripts are disabled here. [npm ci documentation](https://docs.npmjs.com/cli/v10/commands/npm-ci/)

Input SHA-256 identities:

- `package.json`: `152e1b3aa7d2f0fca2ab5da0c1b443e0b811cd699a15a19ed807a41588fa85ee`
- `package-lock.json`: `2bd0d5d024a8f29b79d28b062d54d9e2a2f34737a67fd38d08ee0b031230b20f`

Reproduction: `python3 .gflo/environment-fetch-probe-v2/run.py`. Complete input/code/tarball hashes: `input-hashes.json`; exact URL/SRI bindings: `artifacts.json`; container commands: `receipt.json`; results: `fetch.log`, `offline.log`. Original environment locks and first probe were not changed.

This establishes one fresh-cache replay for these versions. It does not establish arbitrary npm-lock support, hostile tar extraction handling, immutable snapshot publication, or two complete Stage 3 profile executions. Package scripts remain disabled; compiler execution occurred only offline. The trusted-client versus kernel-egress distinction above still applies. No Stage 3 adoption claim follows.
