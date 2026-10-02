# Stage 3 preparation boundary: measured options

Checked on `monster-gaming-pc.lan`, 2026-10-02. Decision research and disposable probes only; no maintained preparer implementation or Stage 3 acceptance. Evidence and runnable probe sources are in `.gflo/environment-build-probe/`.

## Recommended route

Use an immutable base image plus a content-addressed, read-only dependency snapshot. Fetch and assemble dependencies in ordinary resource-limited containers; freeze image ID, exact runtime versions, lock and snapshot digest into one environment receipt. Controller code resolves that receipt to fixed mounts. Workers never choose arbitrary mounts or receive Docker access.

This avoids custom image building/loading for the initial three profiles. It delivers a repeatable environment, but dependencies are **not baked into the image**. Adopt this explicitly as a roadmap interpretation/update before claiming the original image-based design has been implemented. An image digest alone is insufficient to identify this environment; the snapshot digest is equally mandatory.

- Stdlib Python uses the already available immutable Python image and an empty dependency snapshot.
- Packaged Python uses wheel-only, fully hashed installation with `pip --target`, then mounts the frozen dependency tree at `/opt/deps` and sets `PYTHONPATH=/opt/deps`. Use `python -m ...` rather than relocated entry-point scripts. Project wheel construction remains offline with a pinned backend and separate project source/wheel identity. [pip target directory](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-t).
- Node/TypeScript mounts the frozen dependency tree at `/node_modules`. Invoke `node /node_modules/typescript/bin/tsc` directly, avoiding `.bin` symlinks. CommonJS resolution ascends through ancestor `node_modules` directories, so `/workspace` and `/tmp` outputs can find `/node_modules`. This is documented behavior, **not yet a target-host Node/tsc experiment**: no Node image or host Node executable was available in the inspected set, and none was pulled. Restrict the first profile to the frozen CommonJS fixture; independently qualify TypeScript type resolution and runtime imports. [Node module lookup](https://nodejs.org/api/modules.html#loading-from-node_modules-folders).

Ordinary preparation containers get an immutable base, read-only root, no capabilities, no-new-privileges, non-root UID for the production design, no socket/credentials, fixed memory+swap/CPU/PID limits, capped tmpfs scratch and bounded logs. Only fetch has network; installation/building of project code runs offline. Export an uncompressed dependency archive while the executor is alive, with a strict byte cap on the receiver; do not rely on `docker export`, which excludes mounted volumes. Validate entry count, total expanded size, names, file types and duplicate paths before extraction into a private staging directory. Reject absolute/traversal paths, devices, hard links and symlinks initially; omit npm `.bin` and use explicit executable paths. Preserve the standard package layouts and reject unsupported packages rather than silently dropping required files. Atomic publication follows validation and checks. Neither this archive transport nor package installation was implemented/tested in this probe.

## What was actually measured

| Boundary | Evidence |
| --- | --- |
| Ordinary executor cgroups | `memory.max=134217728`, `cpu.max=50000 100000`, `pids.max=24` inside the container |
| Memory exhaustion | Allocating 256 MiB under a 128 MiB limit exited 137 with `OOMKilled=true` |
| Scratch disk exhaustion | Writing 20 MiB to a 16 MiB tmpfs returned `ENOSPC` |
| PID exhaustion | Bounded child spawning returned `EAGAIN`; cleanup removed the container |
| CPU enforcement | Two-second busy loop recorded 21 throttled periods and 1,028,464 throttled microseconds |
| No GPU request in ordinary executor | `DeviceRequests=null`, `Privileged=false`, runtime `runc`; `/dev/nvidia*` list empty |
| Owner death | Existing `gflo.guard` copied into a private probe; controller killed with SIGKILL; pipe EOF removed the running preparation-style container in 0.125 seconds |

The ordinary probe used the existing image ID `sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578`. It used the image's default user; non-root dependency assembly remains to be qualified. Output went to the attached client with Docker logging disabled. These are boundary tests, not complete profile qualification. Source and full evidence: `limits.py`, `limits.log`, `owner-death.py`, `owner-death.log`.

Docker documents that tmpfs memory counts against the container memory limit. Equal memory and memory-swap values disable extra swap allowance. Size scratch and process memory together. A root read-only mount plus explicitly capped writable mounts prevents work from spilling into an unbounded writable image layer. [tmpfs](https://docs.docker.com/engine/storage/tmpfs/), [resource constraints](https://docs.docker.com/engine/containers/resource_constraints/).

## Buildx experiment: useful evidence, rejected default

A disposable Buildx v0.29.1 builder used pinned BuildKit `moby/buildkit@sha256:ddd1ca44b21eda906e81ab14a3d467fa6c39cd73b9a39df1196210edcb8db59e` (tag used only to obtain the digest: `v0.23.2`). Its native snapshotter successfully built a scratch image containing one text file and exported a 7,168-byte OCI archive.

Precreating `buildx_buildkit_gflo-env-boundary-202610020_state` as a local-driver tmpfs volume worked: Buildx reused it, mounted it at `/var/lib/buildkit`, and filling the 256 MiB filesystem returned `ENOSPC`. Builder cgroup reads confirmed 512 MiB memory and 0.5 CPU. `docker update --pids-limit 64` applied to the builder after bootstrap and before work. Docker's documented driver options include memory and CPU controls, but no PID option. [Docker container driver](https://docs.docker.com/build/builders/drivers/docker-container/), [volume driver options](https://docs.docker.com/engine/storage/volumes/).

However, this builder was privileged and had an all-GPU device request despite no explicit GPU arguments. No GPU workload was submitted; the builder was removed and no further privileged builder was started. This was traced to **the installed Buildx source**, not a guessed host runtime policy: v0.29.1 `factory.go` lines 54–57 sets GPU options to `all`; `driver.go` lines 185–186 applies them after a capability test. The host command is `/usr/bin/docker` and default runtime is `runc`. [Pinned factory source](https://github.com/docker/buildx/blob/v0.29.1/driver/docker-container/factory.go#L54), [pinned driver source](https://github.com/docker/buildx/blob/v0.29.1/driver/docker-container/driver.go#L185).

The state volume bounds that filesystem only. The builder's root remains writable and privileged; the tiny export went to host `/tmp` without a per-job export cap. Consequently **this experiment does not establish a fully bounded build or export boundary**. Rootless BuildKit with native snapshotter was not attempted; it remains an alternative requiring its own actual cgroup, mount, GPU absence and owner-death evidence. The snapshot route avoids needing it for these profiles.

## Image load and remaining limits

If custom images are later required, bounded trusted assembly can produce a validated archive, but `docker load` executes in the shared Docker daemon. Limiting the CLI or builder does not bound that daemon's memory, disk consumption or cancellation. Archive byte/expanded-size limits and trusted COPY-only contents reduce input risk; they do not provide executor cgroup containment. Full containment would require a separate bounded image service/store or daemon, beyond this small proposal. No daemon image load was attempted here.

For the recommended snapshot route, finish qualification by proving capped archive transport/extraction, immutable snapshot readback, non-root installation, lock tampering rejection, cold fetch, two offline runs for each fixture, cancellation in every phase and cleanup failure behavior. Reuse the owner-pipe guardian for each actual preparation container; do not merely kill the Docker CLI. Confirm no late artifact publication after cancellation. Daemon outage remains an explicit cleanup failure that blocks reuse.

## Cleanup and retained artifacts

All named probe containers, the Buildx builder and its state volume were removed; final Docker listings showed no `gflo-env` containers/volumes. Existing images and the default builder were left unchanged. The newly pulled BuildKit image remains cached under the digest above; it is a retained image, not a service. Remote private directories `/tmp/gflo-env-boundary-20261002` and `/tmp/gflo-env-owner-probe` contain the tiny export/guardian evidence and are listed for deliberate cleanup. No persistent service was added, no shared daemon configuration changed, and no pruning was performed.
