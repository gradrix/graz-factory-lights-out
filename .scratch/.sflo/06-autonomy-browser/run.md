# Supervised local application browser checks

Executor: markdown
Unit: .scratch/autonomy/delivery/06-local-browser.md
Contract: contract.md sha256 ab3ba1d7aa4d11237de3914f2a1ed40d3dcb47a680ee181465ef8fba6b875f13

## Execution

Status: active
Owner: /root coordinator; /root/cohort_c sole maintained-code builder
Candidate: frozen v3 manifest SHA256 bbcd59aa9ba4223a022eb0c7d0915188b530b5a35308897384d3594fdfa04da3; source91b1e76; not accepted
Next: repair independent SEC-B5 retained guardian facts permission mismatch, freeze v4 and recheck affected recovery before rig qualification.

## Checks and repairs

Unit/run links and contract hash verified at claim. Prior document slice accepted and installed; no browser product capability claimed. Existing prototype isolates renderer and network, but used disable-dev-shm-usage; new explicit shared-memory launch needs qualification. No model request is authorized by browser test execution.

[Independent boundary plan](security-plan.md) reviewed before freeze: pair ownership/exactID, daemon-error versus absence, staging accounting, fixed artifact validation, preventive hooks and actual altered-launch renderer/shm evidence. Builder owns implementation responses. Exact pinned browserimage now preprovisioned locally and read back as2c1f4e0f…; runtime image pulls remain disabled. Additional eight documentation questions run separately against already accepted2049361 with frozen contracts under05/research-cohort; no browser code exposure or acceptance implied.

Independent [fixture plan](qa-plan.md) frozen before browser qualification: publicmanifest20d07c59c1af28f5728847179406560787b579b86c20c030e30032492f16ac10; private d73bdfd54129777d2790529457e7b69b7e3ba399a23175633564e99190d6332a. Five HTTP positive controls and five state-mutant rejections passed on pinned Node; actual Playwright checks still pending. Compact preflight artifacts retained underfixture-preflight.

Pre-freeze conductor findings: B1 domain-inheritance coupling removed (BrowserStore no longer inherits document operations). B2 primary-context-only trace omitted second-session actions in conflict journey; builder assigned all-context capture in one opaque outer traceZIP with per-context traces/manifest, maximum4contexts and unchanged aggregate16MiB. [Architecture choice](../../../docs/decisions/architecture/005-local-browser-verification.md) records format. Unaccepted initial candidate retained; new candidate/relevant evidence pending.

## V2 independent review and repair

[Builder gate](builder.md): 137 tests, 86% branch coverage. [Independent functional QA](qa-browser.md): five positive journeys and five targeted mutants passed expected outcomes, including actual second-context trace actions. These are local results, not rig acceptance.

Security reviewer reported four unresolved findings against c201083; builder assigned all four. SEC-B1: cancellation during final sync can still publish passed receipt (controlled reproduction). SEC-B2: redirected fetch and WebSocket reached a second app-owned origin and passed (actual containers; no host/LAN/public escape demonstrated). SEC-B3: Docker json-file logs have no configured size bounds (inspection; no disk-filling test). SEC-B4: uncertain create timeout followed by current absence clears cleanup fence (controlled reproduction; late daemon completion remains an inference). Candidate-specific report and recheck are pending. Earlier conductor B1/B2 findings above are separate and repaired in v2.

Rig c201083 isolated checkout staged, pinned offline browser support prepared successfully. First prepare used an incorrect archive directory and failed before execution; corrected by copying the two pinned approved archives. No rig browser journey or model call performed for this milestone yet.

## 2026-10-04 continuation

Working tree/source checked: c201083 remains unchanged; interrupted builder had not applied repairs. Execution is available again and cohort_c resumed sole builder ownership. [Independent security report](security-browser.md) and reproduction artifacts now persist. Rig support receipt retained as rig-support-receipt.json. QA prepares remaining rig controls while repairs proceed; no qualification of moving source.

Agent chooses to reject all HTTP redirects and all WebSockets for the initial fixed browser profile. The contract requires external-origin redirect blocking and does not promise same-origin redirects; this explicit supported-app restriction provides a simple preventive boundary. Existing five qualification journeys do not redirect. New candidate must retain successful exact-origin HTTP behavior and demonstrate no second-origin contact.

SEC-B4 repair refinement: classify create transport/nonzero outcomes without a returned ID conservatively, preserve ambiguous-create names, and refuse ordinary fence clearing. Agent authorized an explicit operator acknowledgement for exceptional recovery, durably recorded separately from measured cleanup; architecture record owns the choice. No new user permission is needed for this implementation decision.

V3 freeze: nine manifest paths verified on continuation. Builder reports actual direct-origin control passes and redirect/WebSocket controls reject with zero side hits; logging disabled with attached diagnostics retained. Final full gate pending. Independent security recheck assigned to artifact_security; QA checks rig harness adapters against the frozen v3. V2 failures remain preserved, not overwritten.

[Builder v3 gate](builder-repair-v3.md) completed:144 tests in137.128s,86% branch-aware coverage,exit0; nine frozen paths unchanged. Exact91b1e76 staged on MONSTER-GAMING-PC, CLI help and harness/manifest SHA256 readback matched. Independent security recheck remains pending before rig execution.

Independent v3 recheck reopened recovery as SEC-B5: guardian facts created with inherited umask (0664 under002,0600 under077), while cleanup requires0644. Controlled retained-facts probe confirms refusal before acknowledgement; no actual daemon outage. Builder assigned narrow deterministic-permission repair and umask regressions. V3 remains preserved at91b1e76. Independent unaffected origin/logging probes continue on frozen v3 copy; no rig journey has run.

[V3 independent recheck](security-browser-recheck.md) passes SEC-B1-B4 within measured scope:23 seam observations,9 guardian cases,6 recovery controls,11 actual owned pairs including readiness no-follow and disabled daemon logs with attached diagnostics. Three mode controls preserve SEC-B5 failures at002/077 and022 positive; source/private hashes unchanged, owned containers absent. V4 narrow writer/reader permission repair pending.
