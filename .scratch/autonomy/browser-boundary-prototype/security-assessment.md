# Independent security assessment: Chromium chroot allowance

2026-10-02. Skill: security-check. **Source assessment supports the one-rule experiment; recorded results support limited owned-local-application feasibility. Full browser/Stage 4 acceptance remains incomplete.** No maintained code edits, dynamic probes, reruns or system changes were performed by this reviewer. Browser measurements belong to the separate prototype agent; I inspected its [final report](../browser-boundary-prototype.md) and [receipt](receipt.json), including raw renderer facts.

## Exact assessed inputs and delta

| Input | Identity |
| --- | --- |
| Official Playwright 1.63.0 seccomp profile | SHA-256 `cc3e61cabda6bbc1e53e54d27ba4d55a9d3be829b6dd1a596f4a7b31b1cc7849` |
| Local copied chroot-only profile | SHA-256 `322b86b4f7f5b597ed6a9c2cfd6193a4b249a51c8bc9cfba8ff1a485070b24e8` |
| Official Linux amd64 image manifest | `sha256:bc6ab0d6d44ff4826e4cb8c1e6d801e185bfc42bb0753f8e2a30efc70db054c7` |
| Recorded actual image ID | `sha256:2c1f4e0fd6450f43ddb46d60c2a6df30855a8588e165b1f2559fb0eda8d7ff35` |
| Recorded package/browser | Playwright/core `1.63.0`; Chromium headless shell `153.0.8010.12`, revision `1243` |

I independently hashed and parsed both local profiles. Both contain 27 syscall rules. Only zero-based rule 18 differs:

```json
{"names":["chroot"],"action":"SCMP_ACT_ALLOW","includes":{"caps":["CAP_SYS_CHROOT"]}}
```

becomes the same rule with `"includes": {}`. Its empty arguments/excludes/comment, all other rules, `SCMP_ACT_ERRNO` default and architecture map are unchanged. This is a local adaptation of the [release-pinned official profile](https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/utils/docker/seccomp_profile.json), not an upstream-supported modified profile claim.

## Cause and concrete security implication

Moby builds conditional syscall rules from the container capability bounding set. Its implementation skips an included rule when the requested capability is absent. Thus dropping ALL capabilities removes the original chroot allow rule. This decision occurs when constructing the outer filter; a later Chromium child user namespace does not retroactively change it. [Moby filter construction](https://raw.githubusercontent.com/moby/profiles/main/seccomp/seccomp_linux.go)

Chromium's namespace sandbox uses a helper that calls `chroot("/proc/self/fdinfo/")`, changes working directory, and exits to leave a safe empty root. The observed original failure names that exact operation. The linked Chromium revision explains the mechanism; it is not a verified source-to-binary mapping for this image. [Chromium credentials implementation](https://chromium.googlesource.com/chromium/src/+/aa99e0990143359527b93a52c69dc2ec1a939fb3/sandbox/linux/services/credentials.cc)

The copied rule removes one outer syscall denial. **It grants no host capability**, and the kernel still requires `CAP_SYS_CHROOT` in the caller's user namespace. A process creating a child user namespace can acquire capabilities there without acquiring privileges in its parent namespace. [chroot permissions](https://man7.org/linux/man-pages/man2/chroot.2.html), [user-namespace capability semantics](https://man7.org/linux/man-pages/man7/user_namespaces.7.html)

The exposure is real: every process under the outer profile can now reach the chroot kernel operation if its namespace credentials permit it. This is neither a Chromium-only nor a path-specific allow. The already-permitted user-namespace operations and this additional syscall remain kernel attack surface. Under the assessed owned-app setup, nonroot execution, dropped outer capabilities, no-new-privileges, read-only root, no host writable mounts/socket/devices, private IPC and network-none isolation remain intact. The one-rule change is proportionate for the narrow feasibility experiment; it does not authorize other syscall/capability changes or arbitrary public browsing. Chroot alone is not a complete security boundary.

## What the final measurements establish

The original profile failed closed at chroot/zygote startup. Changing only this rule allowed `chromiumSandbox: true` launch and the owned application's title/click/count journey. That A/B result supports the diagnosed cause. The first modified run still exited 1 because headless shell rejected `chrome://sandbox`; that diagnostic failure remains preserved. A separately authorized reporter-only replay, with identical profile/configuration, exited 0.

In `receipt.json` → `reporter_only_readback.events`, renderer PID 66 has UID 1000, zero effective/permitted capabilities, NoNewPrivs 1, seccomp mode 2 and **three filters**, compared with two for the outer browser/reporter. Its user, PID and network namespaces differ from the reporter; UID/GID mappings contain only `1000 → 1000`, and NSpid is `66 / 4 / 1`. These corroborate active renderer isolation beyond merely observing Docker's filter or a successful launch. The mount namespace is shared with the browser container; no separate renderer mount namespace is claimed.

Do not describe all descendant capability masks as zero: zygote PID 26 records namespace-local effective/permitted `0x200000`, while the renderer bounding mask is nonzero despite zero effective capabilities. Likewise, the network utility process explicitly has `service-sandbox-type=none`, and the software GPU process has only the outer two filters in this observation. They remain inside the outer container/network boundary; renderer evidence cannot be generalized to every subprocess.

The app and browser shared the app's network-none namespace, with only loopback and no IPv4 route. Recorded gateway, LAN, public IPv4 and IPv6 connection attempts returned ENETUNREACH; the owned loopback app returned 200. These are targeted denial measurements, supported by namespace configuration, not an exhaustive destination test. The report records both owned containers removed after each run, no physical GPU devices/socket, retained resource caps and no host changes.

## Coverage verdict

**Sufficient for limited local-app feasibility; insufficient for browser capability acceptance.** This reviewer did not rerun the experiment or inspect generated BPF instructions. Additional renderer filter count/namespace facts support sandbox activation but do not audit filter completeness or prove resistance to browser/kernel exploits. Playwright used `--disable-dev-shm-usage`, so the configured private 256 MiB shm does not establish realistic shared-memory needs. Browser-specific owner-death/cancellation, hostile pages/downloads, larger journeys, trace/screenshot handling and any public-network policy remain unqualified. Preserve this exact evidence and stop at the tested boundary while document work remains the maintained implementation unit.
