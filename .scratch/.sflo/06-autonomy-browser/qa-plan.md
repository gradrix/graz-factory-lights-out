# Independent local-browser acceptance inputs

**Frozen inputs ready; browser qualification pending.** Public `evaluations/local-browser/manifest.json` SHA256 `20d07c59c1af28f5728847179406560787b579b86c20c030e30032492f16ac10`; private `.gflo/browser-qualification/manifest.json` SHA256 `d73bdfd54129777d2790529457e7b69b7e3ba399a23175633564e99190d6332a`. Bound contract SHA256 `ab3ba1d7aa4d11237de3914f2a1ed40d3dcb47a680ee181465ef8fba6b875f13`. Applied s-qa acceptance preparation; no implementation verdict.

## Fixture and reviewed oracles

Known-good Node-builtins stock reservation app, fixed loopback3210, immutable case seed via `GFLO_SEED_FILE`; in-memory state only, no external dependencies or admin reset endpoint. Journeys export ordinary JavaScript using the builder-agreed `{page,context,request,baseURL,screenshot,newContext}` interface. Restricted newContext and screenshot filenames/trace are trusted-helper responsibilities.

| Journey | Browser plus independent state acceptance | Focused state mutant |
|---|---|---|
| create-reload | Reserve2of5; remaining3 and exact row persist after reload; exactly one server record | omit record while decrementing stock |
| validation | Blank/fraction/zero/overstock show accessible errors without changing stock/records; then valid submission works | decrement stock on invalid input |
| edit-cancel |2→3 consumes only1; visible row updates; confirmation cancels and restores5; no active record | subtract full edited quantity |
| conflict | Two fresh contexts load2; first reserves2; stale second gets error and refreshed0; exactly one record | permit overbooking |
| failed-save-retry | Seeded503 leaves state/input unchanged; keyboard reaches error then explicit retry; exactly one successful record | mutate stock before503 |

Labels select actual controls; no success-message/prose keyword matching is used as acceptance. Errors require nonempty accessible feedback. Final screenshots are requested by each case; helper must also produce complete trace. Scripted fixture authorship is independent of runtime implementation and does not claim a local model built the app.

## Completed preflight

`python3 .gflo/browser-qualification/preflight.py`: five conforming HTTP controls pass and five mutants reject at intended state assertions. These run inside actual pinned Node22 image88f8…, runc/network-none/nonroot, read-only mounts,128MiB memory=swap,0.25CPU,64PIDs and16MiB scratch. Every app instance is fresh and terminated. All app/journey `.cjs` files pass `node --check`, including final strengthened exact visible-row checks. Receipts/commands in private `http-results.json` and `preflight.log`; this is HTTP/syntax evidence, not browser execution.

## Next candidate gate

Coordinate with cohort_c when exact pinned Playwright support and assessed seccomp are ready. Run all five positive journeys using frozen inputs under the candidate's real helper; rerun corresponding mutants through the actual journey assertions, not just HTTP preflight. Preserve every result and any fixture defect before versioned repair. Confirm screenshots/trace inventory, fresh contexts/app state, final UI and independent HTTP state.

Then independently inspect runtime/shared-memory/sandbox facts and phase-specific cancellation/ownerdeath, cleanup readback, source/support tamper, artifact bounds/incompleteness, full-store admission and offline inspection. Separate security assessment owns boundary attacks; no change to contract budgets is implied. Actual rig gates remain required, and model/web-app implementation quality remains outside this scripted fixture qualification.

No model, browser, GPU, network target, runtime code or service changes during preparation. Only owned fixture trees and this requested report were written. FullStage4 remains pending.
