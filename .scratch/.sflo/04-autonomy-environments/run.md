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
