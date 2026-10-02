# Environment snapshot security boundary

Reviewed 2026-10-02 using the security-check skill. Independent design review of ADR 004, environment preparation/boundary research, and the private `.gflo/environment-locks` feasibility probe. Maintained runtime was outside the change scope. No containers, image pulls or GPU workloads were started by this review.

## Outcome

The base-image plus dependency-snapshot design is suitable for a bounded first implementation. The private helper is not safe to promote unchanged into the preparer. The constraints below are required before accepting hostile manifests/artifacts or claiming cancellation, immutable receipts, public-only network access or GPU exclusion. No Stage 3 implementation acceptance is granted.

## Coverage

Read the proposed architecture, preparer/package-wheel probe, stored Docker configurations and receipt, and the existing owner-pipe guardian. Ran a disposable host-only probe against the actual `cp` function extracted with Python AST: duplicate archive names were accepted and the last entry won; a pre-existing destination symlink redirected output outside the intended destination. Both targets were inside a temporary directory and were removed afterwards.

Coverage is incomplete for production: no integrated preparer exists in the reviewed candidate; hostile sparse/PAX archives, lock corruption, late publication, daemon outage, actual device visibility, enforced fetch egress and phase-by-phase cancellation were not tested. Stored successful offline installations support feasibility, not these missing guarantees. Registry/package vulnerability assessment was outside scope.

Reviewed identities (SHA-256):

- ADR 004: `2e399e4d77f2b85165180f9be438f323e14d367d0de655bb717be04080f8210e`
- Private `prepare.py`: `9e2e32caeb817fe492a7502d14fc1d0e6f3072cd7567536b71289b7c1e514fb3`
- Private `receipt.json`: `3fc53417966148b3d21fd1d9d6d20002d2d8c9907ad1565c408fb01142ea77ea`

## Trust boundary and practical constraints

The trusted controller owns Docker access, fixed profiles, artifact storage and publication. Generated project files, dependency metadata, package bytes and archive names are untrusted. Assets at risk are host files and credentials, controller availability, the known-good environment, local services reachable from fetch, and GPUs reserved for serving. Hashes identify bytes; they do not make package code trusted.

### 1. Validate the complete archive before writing any artifact

**Observed, high confidence:** `cp` bounds transport to 128 MiB and rejects incoming traversal, links (except skipped `.bin` links), and special entries. It then writes entries directly into a reusable destination while iterating. It does not reject duplicate normalized paths, limit entry count or expanded size, or protect against existing destination symlinks. The disposable probe reproduced both duplicate replacement and a host write through an existing symlink. This does not show that the current regular-file snapshots escaped their directories; it demonstrates unsafe reuse of this helper.

Use a fresh controller-private staging directory for each attempt. Validate all normalized names, duplicates, ancestor/file conflicts, entry counts, declared and actual total output bytes before extraction. Reject sparse encodings and unsupported tar extensions unless specifically qualified: an uncompressed transport cap alone is not an expanded-size guarantee. Create files without following links and without overwrite; permit only regular files/directories, with controller-selected modes and no preserved owners or special permission bits. Skip only the defined npm `.bin` layout, not any arbitrarily named `.bin` directory. Delete staging on any failure. Publish only a completed validated snapshot.

### 2. Bind the bytes that execute to the receipt

**Observed, high confidence:** the prototype records image identities and runtime results and retains `SHA256SUMS`, but it does not implement receipt-based verification or atomic publication. Read-only container mounts prevent that container's writes; host-side mutation remains possible.

The receipt must bind template revision, platform, image ID and available registry identity, normalized request/locks, fetched artifacts, and the final extracted tree. Define a canonical tree digest covering relative paths, file bytes and meaningful execution modes; an archive digest alone is insufficient after extraction. Keep project-source/wheel identity separate from reusable dependencies. Resolve mounts only beneath a controller-owned artifact root using receipt IDs, never paths supplied by the model or receipt input. Verify integrity before use and ensure no untrusted process can mutate the tree between verification and execution. Keep staging and publication on the same filesystem, atomically publish a complete receipt, and retain the prior good receipt after failure. No signing service is needed for this local trust model.

### 3. Make public fetch a real network boundary

**Observed, high confidence:** the probe selects public registries and uses Docker bridge networking. That is not public-registry-only egress; it does not establish exclusion of LAN or host services. The README correctly states this limitation.

Accept only normalized supported manifest fields. Validate every resolved URL and redirect against approved registry/CDN destinations; reject VCS, local paths, arbitrary URLs and lockfile overrides before fetching. If public-only network access is an acceptance claim, enforce it outside the package-manager configuration, including denial of loopback/link-local/private destinations through DNS or redirects. Otherwise explicitly retain broader bridge egress as an unresolved boundary. Fetch receives sanitized manifests only, not project source, repository config, credentials or host home directories. The prototype mounts the whole fixture during fetch; narrow this in the maintained implementation.

Keep assembly and project builds at `network=none`, with no fallback. Python wheel-only/hash checking and npm `--ignore-scripts` are useful controls already exercised by the probe. Project build backends and explicitly invoked scripts are still code execution: run them only in the offline capped executor. Frozen package hashes do not establish package trust or current vulnerability status.

### 4. Supervise transport and publication as part of cancellation

**Observed, high confidence:** helper `run` captures all output in memory before logging; `cp` performs blocking stream reads with no deadline. Its `finally` kills the Docker CLI, not a independently supervised executor. Container cleanup relies on the owner reaching `finally`; SIGKILL bypasses it. The existing guardian handles owner-pipe EOF and reports cleanup failure, but the private preparer does not use it.

Run every preparation executor under a guardian from creation through removal, and bound total elapsed time, archive reads, logs and host staging use. On cancellation, revoke publication eligibility first, stop producers, confirm executor removal and no surviving writer, then discard staging. A cancelled or superseded attempt must fail the final publication check even if its smoke step just succeeded. Daemon unavailability is cleanup failure that blocks reuse until reconciled. Retain this evidence per phase; successful ordinary-container owner-death research is not coverage of the entire preparer lifecycle.

### 5. Check actual mounts, environment and runtime devices

**Observed, high confidence:** stored configurations show read-only selected mounts, capability dropping, no-new-privileges, resource limits, `Privileged=false` and `DeviceRequests=null`. They also show `Runtime=nvidia` for the local dependency probe. The earlier rig boundary report used `runc`; those are different observations. Null device requests alone do not prove absent GPU exposure under every runtime/image configuration. This is an evidence gap, not a finding that GPUs were actually exposed.

Select the approved non-GPU runtime explicitly where available, and retain inspect plus in-container device visibility evidence. Check the full effective environment and mounts for Docker/SSH sockets, keys, host credentials and serving secrets; do not infer their absence from a partial HostConfig record. Keep mount destinations and image selection controller-owned. No GPU computation is needed to establish this boundary.

## Small implementation acceptance slice

The next slice should implement one guarded preparation lifecycle and one strict archive/receipt path shared by the three fixed profiles. Demonstrate rejection of duplicate/traversal/link/sparse/oversized artifacts, receipt/tree tampering, forbidden dependency URLs and missing offline artifacts. Cancel while receiving an archive and at publication, kill the owner, and simulate cleanup failure. Confirm old receipts remain usable and failed attempts cannot become runnable. Then perform the planned profile scenarios and two fresh offline executions. This is a focused boundary gate, not a request for a general build platform or additional language support.
