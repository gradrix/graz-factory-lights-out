# Supervised browser verification of owned applications

Status: chosen for implementation; capability acceptance pending.
Decision maker: agent under the user's2026-10-02 authorization to progress local autonomy through tested increments.

Use one disposable Node application and one pinned Playwright browser for each reviewed journey. The app has only a network-none namespace; the browser joins that exact namespace and reaches the app through loopback. Neither receives a host port, credentials, writable project mount, Docker socket or GPU. The controller freezes inputs, owns deadlines/cleanup and validates evidence. Ordinary Playwright assertions remain trusted acceptance code; page text cannot grant tools or change a check.

The earlier isolated prototype demonstrated the loopback boundary and active Chromium renderer namespace/seccomp isolation. Dropping all outer capabilities required one assessed change to the official seccomp profile: allow the chroot syscall without the outer CAP_SYS_CHROOT condition. Kernel namespace privilege checks remain; this is not a path-specific permission or a claim of arbitrary hostile-public-site safety. Preserve exact image/package/profile identities and fail closed on a mismatch or sandbox startup failure.

Prepare the two fixed Playwright packages with mandatory hashes and immutable support records. Export bounded screenshots, traces and diagnostic events into private verified records; no browser writable host artifact mount or automatic trace extraction. A failed assertion, missing evidence or uncertain cleanup cannot become a passing result. Saved inspection is offline. Existing guardian/artifact mechanisms are reused where their contracts fit, with explicit ownership of the application/browser pair.

The prototype retained Chromium's disable-dev-shm-usage default. The implementation will explicitly omit it and must qualify the altered launch and actual shared-memory behavior, rather than inheriting an unmeasured memory claim. Container and artifact limits are agent-chosen first-profile values in the frozen contract, not user guarantees.

Five independently checked stock-reservation journeys will qualify the first path. This establishes browser verification, not local-model app generation, public browsing, search, arbitrary framework support or fullStage4 completion. A later generated application can use these checks after the capability itself passes.

Evidence: [prototype](../../../.scratch/autonomy/browser-boundary-prototype.md), [independent assessment](../../../.scratch/autonomy/browser-boundary-prototype/security-assessment.md), [proposal](../../../.scratch/autonomy/local-browser-unit-proposal.md), [active unit](../../../.scratch/autonomy/delivery/06-local-browser.md), [frozen contract](../../../.scratch/.sflo/06-autonomy-browser/contract.md).

## Multiple browser contexts

A journey may use up to four fresh contexts. The one opaque trace.zip artifact contains a manifest and one Playwright trace ZIP per context, within the existing aggregate16MiB cap. Every approved context is recorded, including the losing session in the conflict journey. Opening a particular inner trace is an explicit offline operator action; the factory does not extract or render it on the host. This agent decision fixes a pre-freeze primary-context-only recording gap without increasing the frozen artifact budget.

## Redirect and WebSocket restriction

Independent review of candidate c201083 demonstrated that ordinary HTTP routing did not prevent redirected fetches or WebSockets from reaching a second endpoint in the owned app namespace. On 2026-10-04 the agent chose to reject every HTTP redirect before delivering it to Chromium and block all WebSockets in this first profile. Applications requiring either are unsupported. This keeps ordinary exact-origin HTTP flows usable with a small preventive policy; the network-none namespace remains the outer boundary. Repair and independent recheck are required before acceptance.
