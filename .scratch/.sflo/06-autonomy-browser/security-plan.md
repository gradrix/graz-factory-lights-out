# Local-browser boundary: independent security plan

2026-10-02. Skill: security-check. Read-only design review of [contract.md](contract.md), SHA-256 **`ab3ba1d7aa4d11237de3914f2a1ed40d3dcb47a680ee181465ef8fba6b875f13`**, the [unit proposal](../../autonomy/local-browser-unit-proposal.md), existing guardian/artifact/store source and the [prototype security assessment](../../autonomy/browser-boundary-prototype/security-assessment.md).

## Outcome and scope

**The bounded owned-app design is suitable for implementation, with the concrete obligations below. No implemented candidate has been security-qualified.** No maintained changes, model calls, dynamic probes, container/rig operations or system changes were performed for this plan. The assigned browser builder remains sole maintained-code owner.

Assets: host/serving credentials and devices, controller availability, immutable support/input/check bytes, prior complete results, and truthful pass/fail evidence. Trusted: controller approval, fixed helper/profile and independently reviewed journey bundle, Docker daemon and controller-owned store. App/page content is untrusted; it receives no capability to choose containers, targets, input paths, output paths or acceptance. Arbitrary hostile host writers, browser/kernel exploit resistance and power-loss persistence are not established by this design. Five scripted journeys qualify this owned-app verifier, not generated application quality or public browsing.

## Early gaps and builder decisions

I notified the builder and coordinator of these implementation risks before source freeze. The builder supplied the proposed resolutions; these are design commitments, not measured fixes.

| Concrete risk | Required invariant / proposed resolution |
| --- | --- |
| Existing `guard.run` supervises one container. Two unrelated calls do not establish one app/browser lifetime, app death detection during capture, or correct namespace identity. | Builder proposes one dedicated pair guardian: sequential bounded create/start, inspect the app's actual ID, join exactly that ID, monitor app through artifact completion, remove browser then app. Parent EOF must remain meaningful during partial startup as well as steady execution. |
| Nonzero `docker inspect` is not proof of absence: daemon timeout, connection or permission failure can look like a missing object if callers check only return code. | Pass requires explicit absence from a successful bounded daemon query or a narrowly classified missing-object response for each exact owned object. All other responses retain the recovery fence. Simulated daemon errors must prove this distinction. |
| Retained raw 24 MiB transport + another 24 MiB validation spool + 24 MiB extracted output exceeds the 64 MiB reserved staging allowance before copied inputs. | Builder proposes one bounded temporary spool followed by sequential fixed-file decoding: <=24 MiB spool +24 MiB output + approximately5 MiB inputs, leaving headroom for protocol/receipt overhead. Verify all simultaneously live disk representations; memory transport must also have a stated bound. |
| Existing USTAR limits alone do not enforce this browser's exact artifact set, PNG dimensions, per-file caps or opaque trace type. | Builder proposes a fixed manifest/files stream with strict names, exact lengths/hashes and EOF, plus PNG signature/IHDR dimensions, count and per-file caps. No generic archive extraction is needed. Freeze the small framing schema and reject duplicate/extra/missing files. |
| Document D1/D2 failures can recur in a new store/guardian adapter. | Retain prelaunch admission fence; do not infer cleanup success from primary timeout/cancel code. Validate/sync/render privately, make final rename the last fallible publication operation, and avoid postcommit stat/cleanup. Prior-good results survive every failure. |

The staging calculation must include bounded app/browser diagnostics, input/seed copies, collector metadata, and any support preparation done in the same store. Disk reserve is not a bound on browser tmpfs or controller memory; each must remain separately capped. No limit increase is proposed here.

## Pins, support and input ownership

The trusted recipe must bind the exact app/browser image IDs, Playwright/core1.63.0 archive digests, browser revision, helper and copied seccomp profile bytes listed in the frozen proposal. The assessed profile hash is `322b86b4f7f5b597ed6a9c2cfd6193a4b249a51c8bc9cfba8ff1a485070b24e8`; original is `cc3e61cabda6bbc1e53e54d27ba4d55a9d3be829b6dd1a596f4a7b31b1cc7849`. The only profile delta is the unconditional chroot allow. It exposes that syscall to all outer-profile processes subject to kernel checks; it is not a path-specific Chromium privilege. The [earlier assessment](../../autonomy/browser-boundary-prototype/security-assessment.md) explains that measured boundary and its primary sources.

Verify the full prepared support tree before app launch. Package acquisition remains fixed HTTPS/hash code; compressed package unpacking/assembly must be bounded and offline, with no lifecycle/browser-install scripts or host extraction shortcuts. A matching package version string alone is insufficient against altered support bytes. Freeze/check support paths, content, modes and helper identities under the controller ownership assumption.

Copy app/check/seed inputs into private staging before launch. Enforce byte/count limits while reading rather than only trusting pre-copy stat. Refuse links, special files, noncanonical paths and detectable mutation; bind the exact copied content. Directories/implicit ancestors and path lengths need bounds as well as file count, so a deeply nested tiny input cannot amplify filesystem objects. The container mounts the frozen copies, not caller paths. Capture changes between inventory/copy and final validation rather than silently approving a different input tree.

The journey bundle is executable trusted check code. It can use ordinary Playwright APIs; page text cannot modify the bundle, case/seed, checks or launch options. Do not claim general hostile-JavaScript isolation for controller-approved journey code. An unreviewed model-generated test is not equivalent to that approval.

## Pair, network and sandbox invariants

- Install the recovery fence before creating either container. Use fresh identities bound to this store; record exact created IDs as soon as available. Cancel/EOF before, during and after each create cannot strand a late-created writer. A completed browser run with a dead/failed app cannot be promoted without accounting for app state.
- Browser joins only the just-created app's network-none namespace; no published ports, bridge, host-gateway entry, host network or unrelated shared namespace. Read back actual namespace/network settings. Monitor the app while browser executes and finalizes artifacts. Cleanup removes browser then app when the supervisor is alive; owner-death handling still needs bounded independent cleanup.
- Use the fixed origin `http://127.0.0.1:3210`, including exact scheme/host/port comparison. Every fresh context blocks service workers and unexpected popups, external/private redirects, downloads and uploads. Navigation to file/data/javascript or another loopback port must not evade origin policy. Event handlers alone that fire after an action are insufficient to claim prevention; record whether it was prevented or merely detected and rejected. Network namespace denial remains authoritative for external destinations even if hooks miss a request.
- Retain runc/nonroot/read-only root and input mounts, all outer capabilities dropped, no-new-privileges, private IPC, exact resource limits and no devices/socket/credentials. Browser DevTools transport stays private inside the container; no host listening control port. `chromiumSandbox:true` is mandatory and a failed launch cannot retry with weaker flags/profile.
- Prototype renderer facts do not qualify the new launch. Omitting `--disable-dev-shm-usage` must be visible in actual process arguments. Observe renderer user/PID/network namespaces, effective capabilities/no-new-privileges and additional seccomp filtering, separating renderer from utility/software-GPU processes. Do not require every descendant bounding mask to be zero: child user-namespace capabilities have distinct meaning.

Shared-memory measurement must include actual activity under the five frozen journeys and bounded memory/`/dev/shm` observations during rendering/capture, with container caps read back. A configured256MiB allocation or a zero-usage sample alone is not measured adequacy. Record peak/sample limitations; if this workload does not exercise shared-memory behavior, retain that gap explicitly rather than inheriting the old counter prototype's claim. No host IPC or capability change is an allowed workaround.

## Artifact and result integrity

Use fixed finite filenames, complete-byte stream caps and a small bounded metadata schema. Check exact output set, count, declared and actual lengths, hashes, per-artifact caps and final EOF before exposing a record. Bound metadata entries/strings independently of body size. PNG signature/dimensions support the viewport contract; they do not prove the screenshot depicts a correct application. The trace ZIP is opaque evidence: enforce size/hash/presence, never extract it or render bundled HTML on the host.

Events are untrusted page-derived strings. Cap both count and encoded total bytes; avoid spreading app cookies/request bodies/secrets into unrestricted logs. Screenshots/traces stay private with synthetic fixture data. Run output flooding, artifact overflow, malformed framing and incomplete capture controls. An empty or malformed required screenshot/trace, lost error events or unfinished collector cannot count as complete passing evidence. A bounded failure receipt may preserve diagnostics while explicitly recording missing artifacts.

A controller-owned receipt binds copied inputs/checks/seed, support and helpers, actual executor identities/configuration, timings, terminal reason, check results, artifact identities and pair absence evidence. Verify store admission and prior-good integrity before new work. Offline inspect validates record identity/content and performs no browser, script, model or network activity. A rerun creates a distinct record; it must not update bytes behind an existing ID.

## Focused frozen-candidate security checks

Coordinate with independent five-fixture QA: QA owns visible/domain correctness and paired app mutants; security owns failures at the new trust boundaries. Each negative has a conforming control.

1. **Before launch:** altered support/package/profile/image, input link/special/deep/oversize/mutation, changed journey and malformed request. Assert refusal precedes app creation.
2. **Pair ownership:** owner SIGKILL/cancel during first and second startup and artifact capture; app death during journey/capture; hung journey. Inspect exact objects removed, no late-created pair, bounded exit and honest failure result. Keep shared services untouched.
3. **Cleanup uncertainty:** controlled create/inspect/remove timeout/error and masked timeout/cancel results. Failed absence query is never “absent”; no passing publication/new admission until explicit recovery succeeds; prior good remains intact.
4. **Network/authority:** actual loopback positive plus denied gateway/LAN/publicIPv4/IPv6; cross-origin/private redirect, popup, file chooser/download and visible hostile instructions. Confirm unchanged checks/approval/options and no host/device/credential mounts.
5. **Artifact/publication:** exact limits and +1 controls, duplicate/missing/extra/type/length/hash/trailer failures; bounded stdout/stderr/event flood; corruption after publication; private sync/cleanup/rename failure, final cancellation and owner death around commit. No failed run can yield a valid passing receipt.
6. **Altered sandbox launch:** original-profile negative and exact copied-profile positive; no fallback; actual renderer facts and shared-memory activity/caps on the target rig. Preserve any failed budgets before proposing a versioned contract change.

Later verification will bind outcome separately from coverage to exact frozen source hashes. Five local-app journeys, even with these controls, do not accept search, public browsing, ten research answers or full Stage 4.
