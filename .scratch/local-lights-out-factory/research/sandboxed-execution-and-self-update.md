# Sandboxed execution and safe self-update for a local lights-out factory

Research snapshot: 2026-09-02. This report separates requirements stated by
standards and official project documentation from recommendations for this
Factory. There is no single industry standard for autonomous coding agents;
the proposed design composes established CI/build, container-hardening,
software-supply-chain, and secure-update patterns.

## Decision

**Allow scripts to execute.** A useful software factory must run build scripts,
test runners, package-manager lifecycle hooks, downloaded tool installers, and
newly generated programs. Treat all of them—including scripts from otherwise
trusted registries—as untrusted native code. Save and identify a download before
execution; never stream network bytes directly into a shell. Execute it only in
the disposable worker's security boundary, with the same permissions as any
other generated command.

**Keep the durable orchestrator outside disposable worker containers.** This is
a logical trust boundary, not necessarily a requirement that the orchestrator
be an unsandboxed host process. It may itself run as a pinned, non-root service
or a separate persistent container. However, an attempt worker must not be able
to modify its binary/image, durable database, policy, evidence store, launcher,
signing material, or container-runtime control socket.

**Let the Factory improve itself through staged replacement, not in-place
self-mutation.** Version N remains the active controller while ordinary workers
modify a candidate checkout, build immutable candidate N+1, validate it against
a copied state store, and run it in shadow/canary mode. A small external updater
controlled by N verifies the candidate, atomically switches a version pointer,
observes health, and rolls back on failure. N+1 never overwrites the process or
state store from which it is currently running.

This preserves lights-out autonomy: the policy can pre-authorize a passing
candidate to promote without asking a human, while deterministic gates and the
old generation—not the candidate model—control the promotion.

## What official guidance establishes

### Containers are a useful boundary, not a complete security boundary

Docker identifies namespaces, cgroups, daemon exposure, container configuration,
capabilities, and kernel hardening as separate security concerns. It explicitly
notes that default capabilities and mounts can provide incomplete isolation,
especially when combined with kernel vulnerabilities. Cgroups provide resource
accounting and limiting and help defend host availability against denial of
service, but do not isolate data by themselves
([Docker Engine security](https://docs.docker.com/engine/security/)).

Rootless Docker runs both daemon and containers as a non-root user inside a user
namespace, specifically to mitigate daemon and runtime vulnerabilities
([Docker rootless mode](https://docs.docker.com/engine/security/rootless/)). It
reduces impact; it does not make arbitrary execution harmless.

Docker's default seccomp profile is an allowlist that blocks roughly 44 of more
than 300 syscalls. Docker calls it moderately protective and recommends keeping
it enabled
([Docker seccomp profile](https://docs.docker.com/engine/security/seccomp/)).
Docker also exposes `no-new-privileges`, while the Linux kernel documents that
the flag prevents `execve` from granting privileges via setuid/setgid bits or
file capabilities and cannot be unset once enabled. The kernel cautions that it
does not prevent every privilege change
([Docker run security options](https://docs.docker.com/reference/cli/docker/container/run/),
[Linux `no_new_privs`](https://kernel.org/doc/html/v5.8/userspace-api/no_new_privs.html)).

Docker documents that `--privileged` grants all devices and largely removes the
normal AppArmor/SELinux restrictions. Its recommended shape is to grant only a
required capability rather than elevate the entire container
([Docker runtime privileges](https://docs.docker.com/engine/containers/run/)).

The Docker daemon is a host-control boundary. Docker warns that membership of
the Docker socket's group or access to the daemon API may grant root access to
the host. Docker also demonstrates why: an authorized daemon client can mount
the host root filesystem into a container
([Docker daemon reference](https://docs.docker.com/reference/cli/dockerd/),
[Docker daemon attack surface](https://docs.docker.com/engine/security/)). Host
bind mounts are writable by default and can alter or delete host files
([Docker bind mounts](https://docs.docker.com/engine/storage/bind-mounts/)).

For a stronger execution boundary, gVisor intercepts application syscalls and
implements the system API in its Sentry, minimizing direct access to the host
kernel. Its own documentation still says a sandbox is not a substitute for a
secure architecture, relies on host cgroups against resource exhaustion, and
does not eliminate hardware side channels
([gVisor security model](https://gvisor.dev/docs/architecture_guide/security/)).
Firecracker instead places each workload behind a KVM microVM barrier and adds
its `jailer` as a second defense layer
([Firecracker architecture](https://firecracker-microvm.github.io/)). These are
different compatibility/performance/security tradeoffs, not absolute safety.

### Ephemeral jobs and externally preserved records are established CI practice

GitHub warns that persistent self-hosted runners can be persistently compromised
by untrusted workflow code. It recommends ephemeral runners for autoscaling and
requires each such runner to accept at most one job. It also recommends sending
runner logs to external storage before production use
([GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use),
[GitHub self-hosted runner reference](https://docs.github.com/en/actions/reference/runners/self-hosted-runners)).

SLSA Build L3 requires isolated builds, no access to platform secrets such as a
provenance signing key, no influence between concurrent builds, no persistence
into later builds, and an ephemeral environment per build. It also requires
protection against cache poisoning. SLSA explicitly distinguishes isolation
from hermeticity: an isolated build is not necessarily networkless
([SLSA producing artifacts](https://slsa.dev/spec/v1.1-rc1/requirements)).

NIST SSDF 1.1 requires separating and protecting development environments
(PO.5.1), applying least privilege and endpoint hardening (PO.5.2), preserving
release and integrity information (PS.3.1), collecting and protecting component
provenance (PS.3.2), and reviewing and continuously verifying third-party
components (PW.4.1 and PW.4.4)
([NIST SP 800-218](https://doi.org/10.6028/NIST.SP.800-218)). NIST gives
minimizing Internet access as one possible implementation example, not as a
universal prohibition. General outbound access is therefore compatible with
SSDF if the threat is accepted and compensated for.

### Dependency resolution and installation can execute code

Official pip documentation says default installation can run arbitrary code and
does not protect against remote tampering. It recommends pinned requirements,
`--require-hashes`, and binary-only installs for a more secure mode
([pip secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/)).
`npm ci` requires a lockfile, fails when manifest and lock disagree, and does not
rewrite them. Current npm policy can also deny install-time scripts by default
and allow specific packages
([npm ci](https://docs.npmjs.com/cli/commands/npm-ci/)). Go authenticates module
contents against `go.sum` and the checksum database and provides `go mod verify`
to detect changed cache contents
([Go modules reference](https://go.dev/ref/mod)).

These are ecosystem examples, not proof that lockfiles make dependencies safe.
Pins and hashes make inputs identifiable and repeatable; they do not establish
that the identified code is benign.

### Secure updates require trusted metadata and rollback resistance

The Update Framework (TUF) is a specification for securing software update
systems. Its client workflow verifies signed, versioned, expiring metadata and
advances trusted root metadata one version at a time, providing a suitable
standardized basis for authenticating Factory release channels and resisting
rollback/freeze-style update attacks
([TUF specification](https://theupdateframework.github.io/specification/)).
NIST SSDF additionally recommends retaining older in-house component versions
until transitions complete successfully (PW.4.2) and protecting release
integrity/provenance separately from release files (PS.3.1).

## Recommended trust architecture for this Factory

```text
external launcher / updater                 immutable and model-inaccessible
            |
stable orchestrator N                       durable policy, DAG, leases, DB
      |             |             |
credential      egress proxy      execution broker
broker          + audit log       (rootless Docker/runsc or microVM)
                                      |
                               disposable attempt worker
                               - candidate checkout only
                               - no host runtime socket
                               - no durable state writes
                               - no raw long-lived secrets
                                      |
                               artifacts/evidence by digest
```

The inference server should also be a separate service. An arbitrary-code worker
normally needs only a narrow inference API, not direct access to the GPU device,
model files, or inference-server credentials. This keeps the scarce RTX 5090 and
the model service outside the native-code attack surface.

### Durable control plane

Run these outside the attempt worker's mount and credential namespace:

- the Work/Product graph database, event journal, accepted evidence, policy,
  capability profiles, and canonical repositories;
- the process that creates/destroys workers and the only client authorized to
  call the container/microVM runtime;
- raw search/provider credentials, signing keys, promotion authority, and the
  update/rollback launcher;
- append-only or content-addressed logs and artifacts copied out through a
  narrow result protocol.

The orchestrator can be rootless and separately containerized. Persistence is
not the problem; writable reachability from untrusted attempts is. Never mount
`/var/run/docker.sock`, a rootless Docker socket, the host home directory, or the
orchestrator's durable data into a worker. If a task must build container images,
submit a bounded build context to a separate rootless BuildKit service rather
than giving the worker a general Docker socket. BuildKit supports non-root
operation, but its documented rootless-container setup may require relaxed
seccomp/AppArmor/system-path protections, so isolate that builder as its own
privileged trust domain and do not silently apply those relaxations to ordinary
workers
([BuildKit rootless mode](https://github.com/moby/buildkit/blob/master/docs/rootless.md),
[BuildKit security boundary](https://github.com/moby/buildkit/blob/master/PROJECT.md)).

### Worker baseline

Use a fresh filesystem and process namespace for every attempt. A practical
initial profile is:

- rootless runtime plus a non-root UID inside the worker;
- `cap-drop=ALL`, `no-new-privileges`, default or tighter seccomp, and the host's
  AppArmor/SELinux policy; never `--privileged`;
- read-only image root, ephemeral `/tmp`, and one writable attempt checkout;
- no host paths except narrowly scoped read-only inputs copied or mounted for
  that atom; no canonical Git worktree write access;
- no runtime socket, host PID/IPC namespace, host networking, device nodes, SSH
  agent, user credential files, or model/GPU device by default;
- outbound networking through a policy proxy; no inbound/listening exposure;
- fresh dependency caches or content-addressed, read-only verified cache inputs;
- externally enforced PID, memory, disk, process-time, and wall-time controls,
  with logs exported before destruction.

For the first local implementation, rootless Docker with those controls is a
reasonable compatibility baseline. Offer `runsc`/gVisor as the preferred
untrusted-script profile if required language/toolchains pass compatibility
tests. Reserve a Firecracker/Kata-style microVM profile for higher-risk native
code or when a stronger kernel boundary justifies the operational complexity.

Resource budgets may be **configurable and explicitly disabled** for trusted
experiments, matching the user's preference. However, attempt count alone is
not an availability control: a single fork bomb, unbounded download, or disk
fill can prevent the orchestrator reaching attempt two. The host should retain
non-negotiable emergency reserves or a watchdog outside the worker even when a
profile declares its normal token/tool/time budgets “unlimited.” This is a
design recommendation derived from Docker's cgroup guidance, not a standard
mandate.

### Network and credential boundary

General outbound Internet access is compatible with this design. Permit DNS and
HTTP(S), `curl`, public Git hosts, registries, and search. Enforce outside the
worker:

- deny loopback, link-local/cloud-metadata endpoints, host interfaces, and
  private/local ranges unless a capability explicitly grants a destination;
- record resolved destination, redirects, response digest, byte count, and
  retrieval time for consequential inputs;
- give direct unauthenticated access where suitable, but broker authenticated
  search/package capabilities with short-lived, destination-scoped tokens;
- keep signing, repository-write, deployment, cloud, and container-control
  credentials wholly absent from ordinary workers.

Kubernetes' official secret guidance supports the underlying practices: use
short-lived secrets, isolate access, and audit it; merely allowing a workload to
consume a secret means that workload can reveal it
([Kubernetes Secrets guidance](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)).

General Internet plus arbitrary execution necessarily permits exfiltration of
everything readable by the worker. No prompt-injection detector changes that.
Therefore, only material safe to disclose should enter an Internet-enabled
worker. Private source requires a separate no-network/restricted-egress profile
or an explicit acceptance of that confidentiality risk.

## Download-and-execute protocol

Replace “downloaded programs may not execute” with this deterministic policy:

1. The worker may fetch within its network capability. It must store the body
   before use; `curl ... | sh`, process substitution from a URL, remote shell
   sourcing, and equivalent stream-to-execution forms fail policy.
2. The evidence recorder captures original URL, redirect chain, timestamp,
   media/type detection, byte length, and a cryptographic digest. Where an
   upstream signature, checksum, TUF metadata, SLSA provenance, or release
   attestation exists, verify and record it.
3. Prefer capability-profile package managers and locked inputs. Resolve a new
   version in a distinct dependency-change atom; subsequent build/test atoms
   consume the committed lockfile and fail when it drifts.
4. Package lifecycle hooks count as downloaded code execution. Disable them
   during resolution/inspection when the ecosystem supports it, then enable
   only in the disposable build worker when the package genuinely needs them.
5. Execute as the worker UID with no elevated capabilities and exactly the same
   filesystem, network, credential, and resource boundary as generated code.
   Never invoke host `sudo` or host package managers.
6. Preserve stdout/stderr, exit status, sandbox policy, input digests, and output
   digests. Copy only declared outputs back through the broker. Re-validate
   paths, sizes, file types, and expected contracts outside the worker.
7. Destroy the worker after the attempt. A retry receives a fresh environment
   and immutable evidence from the prior attempt, not its potentially
   compromised process tree or writable tool cache.

This permits installers and scripts without pretending that source inspection
can reliably classify arbitrary code as safe. Isolation and least authority are
the primary controls; provenance and scanning add evidence.

## Safe autonomous self-growth

Treat “Factory modifies Factory” as an ordinary product graph with an exceptional
promotion protocol:

1. **Candidate:** a worker checks out the Factory source at an immutable base
   revision into an attempt workspace, produces changes, tests them, and emits a
   candidate commit plus dependency lockfiles.
2. **Build:** an isolated builder produces a versioned image/binary and SBOM,
   records source/toolchain/dependency/image digests and SLSA-style provenance,
   and signs or otherwise authenticates the release metadata outside the worker.
3. **Migration rehearsal:** N copies or snapshots durable state. N+1 performs
   migration and recovery tests only on the copy. Every schema change needs an
   explicit compatibility/rollback rule; append-only events remain readable.
4. **Shadow/canary:** launch N+1 with no promotion credentials and either a
   read-only/copy of state or a separate namespace. Replay recorded Work atoms,
   run deterministic conformance tests, crash/restart/fault tests, and compare
   decisions against N. The candidate cannot certify its own result.
5. **Stage:** place the immutable candidate beside N. Never overwrite N's
   executable, image, current configuration, or database in place.
6. **Promote:** an external minimal launcher verifies release metadata and
   digest, drains N, snapshots state, atomically switches a symlink/image digest
   or generation pointer, and starts N+1. Health must be determined by an
   external probe with a bounded deadline.
7. **Rollback:** on startup, schema, reconciliation, or health failure, stop
   N+1, restore the compatible snapshot/pointer, and restart N. Preserve the
   failed candidate and all evidence for a new Work atom.

Automatic promotion is appropriate only when the human has pre-authorized the
release channel, gate set, migration class, and rollback conditions. Changes to
the root policy, updater, signing trust, sandbox escape controls, credential
broker, or the gates that would approve the same candidate should require a
separate higher-trust path; otherwise a generated patch could remove the guard
that judges it.

For network-distributed updates, use TUF-compatible signed metadata and pinned
release digests. For a single local checkout, immutable Git commits plus an
offline/trusted local release key can be the first implementation, while keeping
the versioned/expiring metadata and rollback protections as an architectural
requirement.

## Consequences for the autonomy contract

- Q15 should be revised to: **download and execute are allowed only inside a
  disposable attempt boundary after capture/digest; direct stream-to-shell and
  host execution are forbidden.**
- Q11's ordinary resource limits can be configurable or disabled, but the
  controller retains an external watchdog and a host reserve. “Unlimited” means
  no task-level quota, not authority to exhaust the machine.
- General web access is allowed, but authenticated access is brokered and
  private-network/metadata access remains denied by default.
- The Factory may run in containers, but it should not be one self-writable
  container. Use a persistent, separately protected controller and disposable
  workers; a stronger sandbox or microVM is available by risk profile.
- Self-development is allowed. Self-corruption is prevented by immutable
  generations, independent verification, staged promotion, and rollback under
  the old generation or an external launcher.

## Residual risks

No local sandbox eliminates kernel/runtime escapes, hardware side channels, or
denial of service. Broad egress enables source exfiltration and interaction with
malicious Internet content. Provenance proves where an artifact came from, not
that it is safe. Rootless mode narrows consequences but does not validate code.
An unattended updater can faithfully promote a malicious change if its gates or
trust roots are compromised. These are reasons for layered controls, immutable
evidence, host patching, and occasional adversarial evaluation—not reasons to
prohibit the script execution required to build software.
