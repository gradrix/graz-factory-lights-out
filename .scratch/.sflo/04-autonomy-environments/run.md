# Supported execution environments

Executor: markdown
Unit: .scratch/autonomy/delivery/04-environments.md
Contract: sha256:2f0f083ced4a23de3f97ad58f1ab970764041e65f39d63855f820878a1660ebb (contract.md)

## Execution

Status: active
Owner: /root
Candidate: 25f75c3; all three recipes implemented; rechecks and target model qualification pending
Next: finish 25f75c3 rechecks, remaining failure coverage and three frozen rig model tasks. Stage3 remains active.

## Checks and repairs

Stage2 accepted with exact candidate/evidence links in its unit. Independent archive corpus and three model-task fixtures are prepared; use protected environment-codingv2, not the flawedv1 oracle. Preparation research is evidence, not source code to transplant. One maintained mutation unit active. No Stage3 acceptance yet.

## Completed slices

- Archive validator 0c9c7c8: 66 independent probes and five tests pass; implicit-directory amplification repaired. See security-artifact-recheck.md.
- Immutable store edc7d71: 68 independent probes and seven tests pass, including actual owner SIGKILL, failed synchronization plus failed retirement, and late cancellation. See security-environment-store-final.md. Pending failed IDs remain non-runnable.
- Guardian 5295522: binary transport and inspection tests (2), sandbox/lifecycle tests (5) pass. Independent security review active.
- Stdlib preparation: behavior-first tests passed after canonicalizing Docker environment ordering; CLI prepare/inspect/twice-offline-check works without model configuration. Bound sandbox rejects tree tampering and ignores changed config image. Frozen task survives controller restart; altered dependencies block before another worker call. Whole existing suite running before freeze. No supported-profile acceptance yet.

## Integrated preparation

- 841dad8 stdlib path: 79 tests passed. QA found accepted terminal status bypassed environment validation; f5b5491 repaired shared status/Observer/resume validation. Independent recheck passed (qa-stdlib-recheck.md).
- 51479e9 all profiles: 86 tests passed, plus profile inference and CLI checks. Independent QA passed three cold preparations, six realistic offline reference scenarios and bound restart/config-change checks (qa-profiles.md).
- Actual rig 51479e9: Python and Node immutable bases provisioned; three empty package-cache preparations and two fresh offline smoke checks each passed. See rig-preparation-51479e9.json. Isolated checkout /home/gradrix/gflo-stage3-51479e9; accepted runtime remains untouched. No model exposure yet.
- dcd3df7: API generated regressions now build/install a wheel offline; reproduced src-layout import failure before repair. One API behavior check and 22 worker/review tests pass.
- Source review found outer scratch cleanup happened after receipt publication. 25f75c3 closes archive and successfully cleans scratch within the publication verifier, before commit. Reproduced failed-cleanup reusable-ID defect; repaired check plus normal stdlib path pass. Independent rechecks pending.
- The initial full preparer security-agent turn failed with a provider content flag; a narrower read-only source review is active. Earlier store/archive/transport independent evidence remains valid within its scope. Full Stage3 security qualification is not claimed.

## Active target qualification

- Runtime candidate 25f75c3, driver ebc6b2a, isolated rig directory /home/gradrix/gflo-stage3-25f75c3. Three new cold preparations and six offline smoke checks passed. Config doctor confirms local flash-next-coder and 131072 context.
- Independent repair QA passed (qa-profiles-recheck.md). Real local Docker timeout/cancellation/controller SIGKILL and scratch/memory/PID tests passed (qa-preparation-lifecycle.md). Source security recheck found no remaining actionable defect in its scope (security-preparer-code.md); live failure evidence is separately attributed to QA.
- Three frozen v2 model tasks started, serialized. State .gflo/stage3-model on the isolated rig checkout. Stdlib run d535632d4d5f is active; acceptance and source fixtures unchanged. No result claimed yet.
- Read-only observer unit gflo-stage3-25f75c3-view.service, rig loopback8788, SSH forward local8788; shared existing Stage2 observer untouched.
- Remaining before acceptance: input/registry error probes; completion and independent semantic assessment of all three model tasks; final scope reconciliation. Source/evidence pushed through bfb8084; driver and latest reports still need publication.

## Latest checks

- Integrated security assessment PASS within the documented trusted-controller/ordinary failure scope (security-environments-final.md), incorporating real executor lifecycle/resource tests and phase interruption. The external outage conditions are controlled simulations, not disruption of public registries or the shared Docker daemon.
- Slop sweep: no material finding (slop-environments.md); two optional cleanups are deferred to avoid unnecessary candidate churn.
- Stdlib model run d535632d4d5f accepted on attempt1 in482.71s; independent recheck and semantic QA passed (qa-model-stdlib.md). Its 20 generated tests, relocated path with spaces,200 additional seeded ledgers and invalid/extreme cases passed. Median coder decoding18.91tokens/s, maxprompt18902; throughput investigation is a separate queued prototype.
- API run70a187241924 entered attempt2 after a generated test incorrectly asserted JSON whitespace. Failure retained; no manual workspace repair and no acceptance claimed while it runs. Node task follows automatically.

## Continuation: maintained regression gate

`make coverage` passed:88 tests in97.040s, aggregate branch-aware coverage85%, exit0. Runtime source remains25f75c3; qualification driver isebc6b2a. Coverage report:coverage-25f75c3.txt. Container-executed recipe helpers are exercised by offline preparation and independent probes; host coverage does not measure all of that execution. No additional broad rerun is needed without a relevant candidate change.

API original70a187241924 remains interrupted at900.03s. Independent diagnosis reproduced a genuine wrong documented Uvicorn target and a separate unsupported oracle `pip` token condition; endpoint behavior and13tests passed. A disposable documentation repair passes the untouched oracle, but is diagnostic and is not a factory-produced acceptance. Fresh follow-up fixture awaits independent pre-exposure QA.

## Original three-profile model cohort completed

Frozen source25f75c3, driver ebc6b2a, fixturev2. Overall gate FAILED:1/3 accepted. python-stdlib: accepted, 482.71s, 1 attempts. python-api: interrupted, 900.03s, 2 attempts. node-ts: interrupted, 900.03s, 1 attempts. Full identities and results:rig-model-25f75c3.json. TypeScript interruption is preserved and independent diagnosis is pending. No environment or model profile was changed during this cohort. A separate fixed-input throughput probe began only after all three tasks stopped.
