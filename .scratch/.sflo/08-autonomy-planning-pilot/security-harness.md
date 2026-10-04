# Planning prototype independent security assessment

2026-10-04. Contract `d52ae8c2f322f417fed6c8cf6ace5343720cc40f86f0d0aeb6b9294e2fc33bea`. Disposable prototype worktree `/home/gradrix/repos/gflo-planning-prototype`; maintained baseline92deaab remains unchanged.

**Outcome: PASS on successor harness SHA256 `b4e7beaab66c480f6e5f6a9a6daad6f57dbbdea6ce6b3ec4c88bafad599aafa9`.** Eighteen independent security controls passed; no open finding remains in this scoped review. Actual serving cancellation, prepared-profile functional QA, frozen admission and project-arm acceptance remain separate gates. This report does not authorize inference by itself.

## Scope and authority

Reviewed shared completion capture/budget, plan authority, Git checkpoint and archive handoff, pending-only mode restoration, serving observation, outer process supervision and executor uncertainty. Wrote only `ops/test_planning_security.py` in the prototype and main coordination evidence. No model, rig, Docker or network calls in these controls. Git and local process controls use owned temporary directories/processes only.

## Independently measured boundaries

`ops/test_planning_security.py` contains18test methods. [Final result](security-harness-final.txt): **18passed0.588seconds**. Source SHA above was read before and after the final run and remained unchanged. Original isolated-test SHA256 `0a635f3182a8b621fa0cb5f2c1acf91a472498fc9b85861178918c334936b9aa`; final test-isolation revision SHA256 `d0d8597a4d715ae7d44a239091ecf7d94959d6f610ad3c70b8391bb3fab6a559` passed within the52-test combined recheck below. Reproduce from the prototype with `python3 -m unittest discover -s ops -p test_planning_security.py -v`. [Binding](security-harness-binding.json) records exact files. Intermediate logs remain preserved.

- Real Git positive controls activate a harmless inherited global clean filter, global pre-commit hook and template hook, each writing only a temporary sentinel. Prototype initialization under the same settings suppresses all sentinels. Injected Git config/repository-selection environment is also neutralized. Conforming content remains byte-exact.
- Model-created `.git/config`, hooks, nested `.git`, `.git` indirection, `.gitattributes`, `.gitmodules`, `.gitignore` and case variants reject before host Git invocation. Snapshot indexing separately rejects reserved controls before the private index command. Source review confirms clean Git configuration and hooks/templates apply to prototype helper and snapshot commands; arm startup sanitizes inherited environment for unchanged Factory Git operations.
- Exact200000byte source copy succeeds with matching fingerprint/modes;200001rejects. Symlinks, hardlinks, FIFO and special file/directory permission bits reject. Controls preserve an outside sentinel.
- Real Factory create/accept/checkpoint/create establishes task1 and pending task2 using controlled worker/verifier callbacks (no executor/model). Non-executable file and directory permission normalization is restored to the frozen map. Mode-map SHA, target fingerprint, Git tree/base, contract bytes and task1 acceptance remain intact. Modified content, extra path, executable-bit change, nonpending status and prior attempt refuse. An original0750executable archived as0755 is intentionally unsupported under the exact executable-bit guard; initial control was corrected to conforming0755, preserving the restrictive rejection rather than weakening it.
- Strict slot parsing rejects empty/extra/non-dictionary slots, absent fields, bool-as-int IDs, float context and nonboolean processing values. Genuine false/true classify idle/busy; changed identity and unhealthy service reject. Probe wrapper refuses malformed/oversized/nonzero responses and expired deadline before spawning.
- Controlled daemon results establish exact workspace-label removal plus final absence. Malformed IDs and daemon timeout refuse. Even two empty current queries cannot clear an existing uncertain-executor fence.
- Missing guardian creation attestation preserves uncertainty for exit0and every tested nonzero status and raises RuntimeError to abort request production; subsequent execution refuses without invoking Sandbox. A trusted private creation receipt plus successful bounded absence readback allows an ordinary application exit1; failed absence retains the fence.

## H1: cancellation before parent result persistence can still publish acceptance

**Observed, high confidence.** [Independent failure](security-harness-publication-red.txt):17tests,16pass/1failure. `run_pilot` computes accepted, then calls `save(arm/result.json, result)`. The probe delivers actual SIGTERM just before that save. The parent handler records cancellation, but the already-computed accepted status is persisted and returned. Equivalent deadline crossing during serialization/fsync was source-supported on the original candidate; a separate deadline control was added for the repair recheck.

This violated the explicit no-parent-success-after-cancellation/deadline gate. Builder repaired only the prototype: `publish_result` prepares/fsyncs private output, checks cancellation/deadline immediately before replacement and rewrites refused success as failed. The aggregate uses the returned committed result. **Recheck PASS:** actual SIGTERM delivered at the final pending-file fsync causes failed persistence; elapsed deadline during fsync also causes failed persistence; normal positive control accepts. Original result input remains unchanged. The original finding/hash/red log remain evidence; no maintained runtime repair occurred.

## Findings during development

The early checkpoint route admitted reserved Git metadata and inherited host Git settings; builder closed these paths before this control run. Initial nonzero-result cleanup could conflate failed Docker creation with ordinary application failure; builder now requires the existing guardian's private creation inspection plus final absence and retains a sticky fence otherwise. These repairs remain prototype-only.

Source review also found missing `bind_environment=sandbox.bind` at actual Factory construction, which would refuse prepared-profile resumes. Builder repaired construction with `bind_environment=sandbox.bind`; source readback confirmed. Independent QA is measuring the actual prepared-profile synthetic-transport path separately. No maintained runtime repair was requested.

`security-harness-initial.txt` preserves the first run. Its errors reflect an updated sticky fence invalidating a multi-operation test setup and the restrictive executable0750→0755guard, not evidence of false acceptance. Final tests use isolated arms for uncertainty cases and a conforming executable mode.

## Coverage and limits

This security slice uses real host Git/files/Factory state with harmless callbacks and controlled serving/daemon responses. It does not claim actual model cancellation, container cleanup, shared-daemon outage, kernel isolation, arbitrary concurrent host writers or semantic project acceptance. Endpoint discovery and driver controls are separately recorded in `serving-lifecycle-plan.md` and `security-cancellation-driver.md`.

Request-budget, final-milestone failure and actual local supervisor tests belong to separate functional/builder reports; their mechanisms were source-reviewed here, but their measured claims are not counted among these18security controls. An idle snapshot is not a reservation against unrelated clients. The pilot requires exclusive endpoint ownership, a shared lease, fresh strict observations and refusal of cleanup uncertainty. Final project outcomes still require independent acceptance and semantic review. Full Stage5 remains outside this disposable experiment.

## Combined-suite isolation recheck

The first combined52run exposed a test interaction, preserved in `combined-controls.txt`: QA invoked `arm_work` in-process and retained its intentionally sanitized Git environment; the security positive control then inherited `GIT_CONFIG_COUNT` overrides disabling hooks/attributes. This invalidated the positive control setup, not product isolation. A direct [reproduction](git-control-isolation-red.txt) with only those environment overrides failed identically.

Test-only fixes: QA restores its pretest environment around `arm_work`; security constructs its positive-control Git environment without any inherited `GIT_*` entries, then supplies explicit hostile controlled settings. The same injected sanitized environment now passes [the focused control](git-control-isolation-green.txt). Product hash remains `b4e7beaab66c480f6e5f6a9a6daad6f57dbbdea6ce6b3ec4c88bafad599aafa9`.

[Final combined output](combined-controls-final.txt): **52tests passed in5.789seconds**, comprising18security,16cancellation,8functional QA and10builder controls. This was one combined rerun, also retained as `combined-controls-recheck.txt`; final is an exact copy. Updated QA test SHA256 `1ff0479a52c567d8d98f4cd19be33973798b29baeb933b6ab3705bdc7cfb1971`. No optional further tests or inference were performed. Scoped security PASS is unchanged.
