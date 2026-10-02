# Stdlib environment slice QA — BLOCKED on accepted-run reuse

Frozen candidate `841dad8c7341f2212562771b2e9ece0e215a0b9c`. Scope: stdlib preparation → frozen task → execution/restart/context/readback, against `contract.md`. Pinned source reconstructed independently. No live model/GPU calls, rig changes, or maintained edits. Stage 3 remains unaccepted; API/Node excluded.

## Confirmed defect

**Accepted-run status and resume bypass frozen environment integrity.** Independent probe prepares a valid snapshot, creates and accepts a bound task using real Docker checks, confirms unchanged reuse, then changes the dependency root from 0555 to 0755. `EnvironmentStore.resolve` rejects the changed root, but `Factory.status`, `Factory.resume`, and `Observer.status` still return **accepted**. `resume` returns from its terminal-status fast path before `resolve_binding`; accepted-artifact validation does not include environment validity.

This can advertise accepted/reusable execution evidence after its environment is unavailable or changed. Validate frozen bindings when assessing accepted integrity and before terminal resume reuse; retain legacy-unbound behavior. Preserve historical receipts while returning an honest invalidated/unavailable state. Controls: original bound run accepts and unchanged resume accepts; direct resolver rejects the same tampered environment. Evidence: `qa-stdlib/result.json`, `context-result.json`, executable `probe.py` and `context.py`.

## Passed coverage

| Check | Observation |
|---|---|
| Public environment CLI without model config | prepare, inspect, check --repeat 2 all succeed with nonexistent config path |
| Stable identity | Two preparations return the same ID; receipt and repeated check outputs saved |
| Actual preparation executor | Receipt records explicit runc, network none, readonly dependencies and capped resources |
| Frozen binding after restart/config change | Reopened Factory uses frozen image despite Sandbox configured with nonexistent image |
| Worker/check environment | Real Docker worker command and independent check both execute in bound3.12.13 image; writing /opt/deps rejects |
| Actual worker facts | Python3.12.13; no /dev/nvidia* or /dev/dri*; memory1GiB, swap0,128PIDs,2CPU cgroup |
| Worker/reviewer context | Captured model requests include frozen profile/image/runtime; no target-model call |
| Legacy handling | Explicit legacy-unbound context; existing unbound runner regressions pass |
| Nonterminal tamper rejection | Existing focused runner regression rejects changed dependencies after interruption |
| Focused suites | 4 preparation +14 runner tests pass |

No other defect identified in this bounded slice. Resource facts above distinguish preparer settings from worker settings. Broad archive/publication/owner-death qualification is separate and was not rerun. Current frozen receipt metadata checks runtime facts but this slice does not establish every future profile's behavior.

Reproduction from repo: `python3 .scratch/.sflo/04-autonomy-environments/qa-stdlib/probe.py`, then `python3 .scratch/.sflo/04-autonomy-environments/qa-stdlib/context.py`; both exit0 when expected positive behavior and known defect reproduce. Scripts/results/logs and receipts are in `qa-stdlib/`; disposable task/store path is recorded in result.json. Context probe restores its private snapshot mode after demonstrating direct rejection. Suite commands use `qa_pinned.py 841dad8c7341f2212562771b2e9ece0e215a0b9c -m unittest discover -s tests -p test_prepare.py` and `test_runner.py`.
