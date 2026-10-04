# Frozen browser v2 functional QA

**PASS within independent local functional scope**, commit `c201083d64810bc7767007e37a3fc8912e6d1c50`, candidate manifest `44e94609e0174950894d2008649fe93a247abf9eacf4f7a3411144b011e9e0c3`. Candidate and frozen fixture hashes verified before/after, including after seam probes. Original primary-context-only trace finding remains preserved; this verdict applies to v2 only. Independent security and rig gates are separate.

## Five controls and discriminating failures

| Journey | Known-good result | Corresponding mutant |
|---|---|---|
| Create/reload | PASS: stock3, exact reservation persists | Missing server record rejects |
| Validation/recovery | PASS: errors do not mutate state, valid recovery succeeds | Overstock rejection that decrements stock rejects |
| Edit/cancel | PASS: edit consumes delta only, visible quantity3, cancel restores5 | Full-quantity subtraction rejects |
| Conflicting sessions | PASS: stale second session conflicts, refreshes0, retains input; one reservation | Overbooking rejects |
|503 explicit retry | PASS: input retained, keyboard reaches error/retry, exactly one record | Mutation before503 rejects |

All ten expectations confirmed in32.191s. Every mutant failed in the journey phase with confirmed cleanup, not due to an unrelated launch/artifact error. The validation browser mutant deliberately targets409; the earlier HTTP-only422 mutant remains recorded but would be intercepted by frontend checks and is not claimed as this browser negative.

## Evidence completeness and seams

- Five1280×800 PNG headers independently checked; conflict screenshot visually inspected and agrees with final state assertions. Screenshots do not replace assertions/HTTP state.
- Every positive has a complete outer trace ZIP; four ordinary cases have one context and conflict has two. Bounded in-memory archive inspection verifies nested bytes/hashes against the manifest and runtime receipt. Second-session trace contains actual `fill` value `Second` and Reserve `click`; no archive was extracted to the host or rendered.
- Actual Nodev24.20.0, Playwright/core1.63.0 and Chromium153.0.8010.12 receipts. Positive measured `/dev/shm` peaks9,142,272–17,649,664bytes with6–12samples. This is real altered-launch use, not inference from configured allocation; rig measurement still required.
- New-instance CLI inspect works with nonexistent model config and executor/model construction set to fail. Stored receipt/artifacts remain unchanged.
- Actual cancellation after entering a deliberately hung journey removes both owned containers, publishes a failed result and preserves a copied prior-good record byte-for-byte. Docker label readback finds no remaining pair. No model/service/rig changes.
- Fifteen affected browser public-seam tests pass, including snapshot/input bounds, preparation image checks, support/artifact tamper, incomplete output, cleanup fencing and publication failure controls. These controlled regressions do not substitute for the parallel adversarial assessment.

Support receipt `f6dba2d707f42e5575d6bbd285f8db6041093861d47664c09276661a423f8c76` and full copied support contents/modes resolve unchanged before/after. Fixture manifest remains `20d07c59c1af28f5728847179406560787b579b86c20c030e30032492f16ac10`. No fixture correction was needed or silently applied after execution.

## Reproduction/evidence

Driver and exact invocation: [qualification-driver.md](qualification-driver.md), `.scratch/autonomy/qualify-browser.py`; choose a new output directory when rerunning. Complete inputs/requests/receipts/artifacts remain `.gflo/browser-independent-v2`.

Compact evidence: [control-summary.json](qa-browser/control-summary.json), [conflict trace audit](qa-browser/conflict-trace-audit.json), [seam probe](qa-browser/seams.py), [seam results](qa-browser/seams-results.json), [unit log](qa-browser/unit-tests.log), [driver log](qualification-v2.log). No maintained source or frozen fixture changes, model/GPU/rig calls, or broad Stage3 retesting. Known-good scripted app success does not establish local-model application-building quality or full Stage4 acceptance.
