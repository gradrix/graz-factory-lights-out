# Owned local browser boundary: disposable prototype

2026-10-02, actual rig `monster-gaming-pc.lan`. **Feasible for the tested local journey with one narrowly changed seccomp rule; not Stage 4 acceptance or arbitrary-site qualification.** No product implementation, model call, host sysctl/config change, added capability, host IPC, GPU device, Docker socket mount, or unsandboxed fallback was used.

## Immutable source pins

Verified against the official [MCR manifest endpoint](https://mcr.microsoft.com/v2/playwright/manifests/v1.63.0-noble), [Playwright npm metadata](https://registry.npmjs.org/playwright/1.63.0), [core npm metadata](https://registry.npmjs.org/playwright-core/1.63.0), and [release-pinned seccomp](https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/utils/docker/seccomp_profile.json). Downloaded npm tarballs were verified against their registry SHA-512 integrity before extraction. The image was pulled by architecture-specific digest, not the mutable tag.

| Artifact | Pin |
|---|---|
| Official image index | `sha256:eff16c30e6f3f4af0a03fa4b706120d5e9b0891c344a27d64559aff5900a4a27` |
| Linux amd64 manifest | `sha256:bc6ab0d6d44ff4826e4cb8c1e6d801e185bfc42bb0753f8e2a30efc70db054c7` |
| Actual image ID | `sha256:2c1f4e0fd6450f43ddb46d60c2a6df30855a8588e165b1f2559fb0eda8d7ff35` |
| playwright / playwright-core | Both exactly `1.63.0`; complete integrity strings and tarball SHA-256 in sibling receipt |
| Official seccomp SHA-256 | `cc3e61cabda6bbc1e53e54d27ba4d55a9d3be829b6dd1a596f4a7b31b1cc7849` |
| Copied chroot-only profile SHA-256 | `322b86b4f7f5b597ed6a9c2cfd6193a4b249a51c8bc9cfba8ff1a485070b24e8` |
| Measured runtime | Node `v24.20.0`; Chromium headless shell `153.0.8010.12`, revision `1243` |

## Boundary and observed results

The owned app binds only `127.0.0.1:3210` inside a Docker `--network=none` namespace. The browser joins only that app's namespace with `--network=container:gflo-browser-probe-app`. This creates no bridge/gateway route. The namespace had only `lo` and an empty IPv4 routing table. The browser container runs UID 1000, explicit runc, all capabilities dropped (outer capability masks zero), no-new-privileges, read-only root, init, 256-PID limit, 1 GiB memory/swap ceiling, 2 CPUs, private 256 MiB shared memory and bounded 256 MiB temporary storage. The app is separately bounded to 128 MiB, 0.25 CPU and 64 PIDs. No ports are published.

| Observation | Official profile | Copied chroot-only profile |
|---|---|---|
| Owned loopback HTTP | 200 | 200 |
| Gateway `172.17.0.1`, LAN `10.1.1.155`, Internet IPv4 `1.1.1.1` and IPv6 `2606:4700:4700::1111` | All `ENETUNREACH` | All `ENETUNREACH` |
| UID/capability/no-new-privileges controls | Retained | Retained |
| `chromiumSandbox:true` launch | Failed closed: chroot failure, zygote SIGTRAP | Launched successfully |
| Browser local app / click / DOM result | Not reached | Title correct, button increment produced `1` |
| Renderer sandbox introspection | Not reached | First diagnostic unsupported; authorized reporter-only replay captured separate namespaces and added renderer seccomp filter |
| Probe process exit | 1 | First run 1 (diagnostic URL); reporter-only replay 0 |

No run used `--no-sandbox`. The second run's exit 1 is preserved, not relabeled a full pass. The browser launch and application journey nevertheless succeeded before the diagnostic navigation failed. Network denial is enforced by the namespace independently of Playwright routing; this proof is stronger than an internal Docker bridge alone.

## Why the first launch failed, and the exact authorized change

The official profile conditions its `chroot` allow rule on outer `CAP_SYS_CHROOT`. Dropping all capabilities omits that syscall permission. Chromium's child user namespace can hold its own namespace capabilities, but still inherits the outer seccomp denial. The launch error was exactly `sys_chroot("/proc/self/fdinfo/") == 0` followed by premature zygote exit.

After root authorization and independent source assessment by `artifact_security`, one copied-profile A/B run changed only syscall rule 18: `names:["chroot"]`, action ALLOW, `includes:{caps:["CAP_SYS_CHROOT"]}` became `includes:{}`. All other 26 syscall rules, defaults and architecture settings remained identical. The successful launch after that single change supports the diagnosed cause. This exposes chroot to every process subject to the outer profile; it is not a path-specific permission or a grant of host capability. Kernel namespace capability checks still apply. No additional relaxation was attempted.

## Limits and next decision

After separate root authorization, one reporter-only replay kept the identical successful profile/configuration and replaced the unsupported diagnostic navigation with /proc observation. It **passed, exit 0**, repeating the app journey and all network denials. The renderer had UID 1000, zero effective capabilities, NoNewPrivs 1, Seccomp mode 2 with three filters (outer browser/reporter had two), separate user/PID/network namespace identities, a one-UID `1000 -> 1000` map, and nested NSpid `66 / 4 / 1`. These are concrete renderer sandbox observations beyond the outer container filter. No `--no-sandbox` flag was present.

Do not conflate outer dropped capabilities with every child namespace's capability state: the child zygote held a namespace-local capability and the renderer's bounding mask was nonzero, while renderer effective capabilities were zero. Chromium's network utility process reported `service-sandbox-type=none` and remained protected by the outer isolated namespace/container; this is not proof that every Chromium subprocess uses renderer-equivalent isolation. The unsupported diagnostic-page failure remains in the earlier receipt. No further configuration relaxation occurred.

Playwright's default arguments include `--disable-dev-shm-usage`; although private shm was bounded and host IPC absent, this run does not establish adequate shared-memory sizing for realistic journeys. Cancellation/owner-exit fault injection, large pages, downloads, hostile content, public-network policy and full Stage 4 journeys remain untested. Stop at feasibility; do not implement a product browser worker from this report alone.

## Evidence, cleanup and artifact locations

Small scripts, exact profiles/delta, official metadata and sanitized receipt: `.scratch/autonomy/browser-boundary-prototype/`. Full local downloaded packages/raw logs/inspect outputs: `.gflo/browser-boundary-prototype/`. Rig-owned workdir: `/home/gradrix/gflo-browser-probe`; downloaded image remains cached by digest. Both owned containers were removed after each of the three bounded runs and final label query returned none. Other containers were untouched. Scripts `run.sh` and `run-chroot.sh` show complete limits and cleanup behavior; first-failure raw outputs are preserved locally and under the rig workdir's `first-failed/`.
