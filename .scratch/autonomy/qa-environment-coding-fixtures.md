# Environment coding fixture QA — v1 BLOCKED before exposure

Public manifest `c479e671e6a4bdc06f8b58cfcf8a5f520c50f2859387ec7894f97039f43ab374`; private manifest `9b944ac5efc83e89d54e22843fd2425ae6ca7fe227bb117870fa54ff3fcb9c8c`. Both manifest/file sets verified before probes. No model/GPU calls, rig/runtime changes, maintained test edits or Stage 3 acceptance claim.

## Confirmed findings

1. **Node filtering bypasses required validation without oracle rejection.** Add `if(p.events.length<p.minAttempts)return [];` after request-level validation in the reference. The complete protected oracle and generated tests still pass. Counterexample: `{action:'report',events:[{service:'x',durationMs:-1,outcome:'success'}],minAttempts:2}` must throw by the explicit validate-every-event-before-filtering rule, but mutant returns `[]`. Add this rejection across API, CLI and input-immutability checks. Reference passes existing checks; mutated reference also passes, demonstrating a coverage defect.
2. **Changed approved Node lock passes.** Changing only `5.8.3` to `5.8.4` in copied `package-lock.json` passes the complete oracle, despite the explicit unchanged-lock requirement. Compilation uses prepared `/node_modules` and therefore does not validate the submitted lock. Bind approved package/lock bytes in independent checks; similarly preserve Python declared dependency/build versions when checking pyproject. This finding does not show that the preparer would resolve the changed lock: it shows acceptance currently fails to reject an explicitly forbidden delivery.

Builder was notified to preserve v1 and prepare a new frozen revision before any exposure.

## Passed coverage and limits

| Check | Observation |
|---|---|
| Three reference controls | All pass in explicit runc/network-none containers at `/different-source`, started from `/tmp` |
| Python API | Real offline wheel build/install plus loopback HTTP checks pass; deliberate partial-stock result on rejected preview is rejected |
| Python stdlib types | Deliberate boolean-to-integer over-budget result is rejected |
| Runtime/dependency requests | Public exact versions align with prepared inventories and locks; stdlib has no dependencies; Python build/API/test versions and Node compiler/types are available |
| Portability | Protected checks use supplied project path or installed package; relocated API/CLI/tests pass; profile dependency paths remain intentionally controller-selected |
| Other expected values | No contradictory reference/oracle expected result identified in bounded inspection |

Meaningful test content, documentation completeness and exhaustive invalid shapes remain semantic-review work. Public task metadata does not itself constitute an accepted environment receipt. Profile preparation, immutable publication and security/lifecycle gates remain separate.

Evidence: `.gflo/environment-coding-qa/probe.py`, `probe.log`, `results.json`; corrected strict-type probe/result under `strict-type.py` and `strict-type/results.json`; lock mutation under `lock-change.py` and `lock-change/results.json`. Initial `integer-over-budget` entry in the first results file was a no-op string replacement and is excluded; the corrected probe changes the exact expression and rejects with exit1. Reference and false-pass results are unaffected. Scripts bind the original manifests; after fixture revision use preserved v1 paths for reproduction or deliberately adapt to the new frozen identity.
