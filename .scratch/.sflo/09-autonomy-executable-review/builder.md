# Executable-review prototype builder handoff

Scope: new isolated `ops/executable_review_prototype.py` and builder controls only, in `/home/gradrix/repos/gflo-review-prototype`. Mechanism SHA256: `ede30d388c75b1c69c683dbd4c61cae408afc73cd5d35f84c1748d0ab281ecaa`. No maintained changes, prior prototype changes, rig calls, model calls or installation by the builder. All32 carry-forward source/assets were rehashed and match `carry-forward.json`; all44 public fixture hashes and60 file/directory modes validate.

## Mechanism

A new explicit case ledger owns eight completion attempts,12 commands and the shared300-second work deadline. It records debit before transport/dispatch and reloads existing state on reconstruction. Limits are not changed through prior-module globals. One reviewer context receives the complete public objective and bounded source text; only run(command) is available. Existing grounded `gflo.review.validate` validates final pass/repair/needs_input. A no-tool verdict or malformed/unsupported response ends incomplete without automatic repair calls.

New prompt wording replaces the old text-only tool prohibition. It requests checking implementation, generated tests, documentation and representative counterexamples without case-specific hints. Documented project-root locations may be adapted to `/candidate`; candidate source remains unchanged. This is a new prompt/workflow; no model-quality qualification is inherited from historical static reviews.

Each command has fresh bounded `/tmp` and processes, read-only `/candidate` and approved dependencies, no `/workspace`, nonroot UID, runc, no network/devices/socket/GPU, dropped capabilities and no-new-privileges. Resource receipts require1GiB memory/swap,2CPU,128pids,16MiB shm and128MiB temporary space. Commands are at most16384characters and60seconds shortened to remaining work time. Complete-byte stdout capture and bounded diagnostics prevent unbounded tool feedback; model-visible combined output is capped at16384bytes with an explicit limited flag.

Security found P09-START during construction: a successful create/inspect receipt did not prove the shell started. The corrected fixed wrapper emits a random controller marker before executing the requested command. The marker must appear at the beginning of captured stdout, is saved as separate start evidence, and is removed from model feedback. Actual failing commands can count as executed; creation-only failures cannot. Creation boundaries, exact owned-container absence and unchanged candidate identity are also required. Uncertainty leaves a sticky fence and aborts dispatch.

The unchanged08 supervisor enforces the outer deadline and owned process-group cleanup. Reused shared lease, strict same-identity idle probe and150-second aggregate cleanup gate separate cases. The reused publication helper fences success after temporary-file fsync and immediately before atomic replace. **Internal status `accepted` means a structurally completed executable review; it does not mean the candidate is correct or the classification independently passed.** The verdict and independent expected classification remain separate.

## Behavior-first checks

The initial builder tests failed because the new mechanism was absent; the ledger, tool authority and final-verdict slice then passed. Six final builder controls pass, covering reconstruction through eight failed debits and denial of ninth dispatch,12-command cap/deadline refusal, invalid/no-command verdicts, tool schema/duplicate/length refusal, untrusted tool output remaining in its tool-role message, and an actual local Docker command.

The actual local approved-image command proves nonroot execution, `/workspace` absence, writable temporary space, read-only candidate-write failure, unchanged source and positive start/cleanup evidence. Its nonzero application exit is correctly attested. It uses a disposable empty stdlib dependency mount to test the executor boundary; canonical prepared-environment wiring on the rig is a separate independent gate. No target-model call occurred.

Independent security reports18 passing controls including P09-START negative/positive controls, actual boundary mismatch, missing cleanup, UID0 refusal, shared-budget failures and cancellation/deadline at publication. Original red evidence is preserved under `security/`. Final QA and combined-run binding follow in the candidate manifest when those owned test files are stable.

## Invocation and limits

```sh
python3 ops/executable_review_prototype.py run --manifest evaluations/executable-review/manifest.json --manifest-sha256 05de766048d96216865b8e5d0c817166ac1635391a6ed496b9ce6c3b0b6bdb37 --config PRIVATE_CONFIG --bindings CANONICAL_BINDINGS --identity EXPECTED_SERVING_IDENTITY --output NEW_PRIVATE_OUTPUT
```

Root owns admission and actual execution. `_case` is internal wiring. Existing outputs cannot resume/reset. The shared lease defaults to `~/.local/state/gflo-planning-pilot/lease`; endpoint ownership still requires excluding unrelated clients because an idle snapshot is not a reservation. Credentials stay in transport; evidence contains bounded raw bodies, usage (null when unavailable), commands, creation/start/cleanup receipts, source hashes and verdicts.

This four-known-case discriminator is not held-out qualification, a reliability estimate or equal-cost comparison with historical static reviews. Successful completion only permits independent defect/control scoring and a subsequent fresh-case decision. No maintained reviewer, planner or integration framework is introduced.

## Final freeze

Committed exactly five new ops files at `37b7f1d1416d5497ca38291b47b364882d2d44ef`; no prior file changes. Combined gate `GFLO_REVIEW_LOCAL_DOCKER=1 python3 -m unittest discover -s ops -p "test_executable_review_*.py" -v` passes31 tests in0.911s, including the actual local Docker control; log `combined-controls.txt`. Independent QA7 and security18 plus builder6 all pass together. All32 reused identities match. Candidate manifest SHA256 `cbfe1fb7556f62dc454dd3fdaf937aba6e2a11ae1b9bee455cdce36ee4054cb6` binds source/test/fixture/contract/limit identities. Actual rig synthetic wiring and any later model calls remain root-owned admission gates.
