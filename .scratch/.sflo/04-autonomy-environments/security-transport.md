# Independent security assessment: guardian transport

Date: 2026-10-02. Skill: security-check. Frozen candidate: `5295522d04df1e34d2826309e2617ac0a6bf46d7`.

Source SHA-256:

- `gflo/guard.py`: `8f623a2ff7f9958ef2e1d0a99686ab83f31ab2100fbf5124097bcf1ae88ace48`.
- `gflo/sandbox.py`: `e018c4722e99895549a6141579e9553a5a302379122981f9ad6a9b5a0baab853`.

## Outcome

**No actionable security finding in the assessed controller logic.** All 19 independent controlled probes passed. Binary-output overflow, interruption, sink failure and create/inspect/cleanup failures could not qualify as successful execution in the tested paths. This supports proceeding with preparer integration.

## Coverage

Completed the controlled process/transport assessment on Python 3.10.12 using the exact frozen guardian and sandbox modules. Both this probe process and real guardian subprocesses load the reconstructed candidate; subprocess working directory and `PYTHONPATH` are pinned. No maintained code was edited.

The probe places a test-owned `docker` substitute first on `PATH`. It implements only create, inspect, start and remove using disposable local state and real controlled Python child processes. The guardian and owner are real processes. The substitute relays child output through its own pipes, so executor descendants do not incorrectly inherit the guardian's output pipes after the substitute CLI is killed. All payload code is fixed test code. No real Docker daemon, container, network, rig or GPU is involved.

| Boundary | Evidence |
| --- | --- |
| Binary fidelity and exact cap | All 256 byte values preserved exactly at a 256-byte cap; separate diagnostic stream stays out of the artifact. A 255-byte control succeeds. |
| Binary overflow | 257-, 65,536- and 1,048,576-byte producers fail with the output-limit flag; the supplied sink never receives more than 256 bytes. |
| Diagnostic bounds | A one-million-byte stderr producer succeeds with a two-byte artifact and only the final 16,384 diagnostic bytes retained. Text-mode stdout/stderr also retains a bounded tail and reports truncation. |
| Timeout and cancellation | Sleeping executors are removed on timeout and callback cancellation; a cancellation callback exception also triggers cleanup. Expected non-success codes or exceptions are observed. |
| Actual owner death | A forked owner is killed with `SIGKILL` after executor start. The surviving real guardian invokes removal for its exact name; test state disappears and the test executor is observed exited or zombie, not running. |
| Owner death during create | The owner is killed while fake creation is delayed. Creation completes, the guardian observes owner EOF, removes the exact object, and never starts an executor. |
| Failure qualification | Create error, inspect error, output-sink `OSError`, existing inspection path and cleanup error all produce non-success. Create/inspect/path failures do not start an executor. |
| Cleanup failure during timeout | Non-success and an explicit cleanup diagnostic are preserved. The test verifies that removal did not succeed; its own harness then disposes of the remaining local executor. |
| Inspection accuracy | The written receipt exactly matches the synthetic inspect input for image, host constraints, effective user/environment/workdir and mounts. Existing inspection files are preserved and execution is refused. This establishes projection accuracy, not real runtime facts. |
| Sandbox refactor | Arguments preserve pinned-image/no-pull policy, runc, network none, read-only root, capabilities/security options, resource limits and two read-only acceptance mounts. Start/finish observations remain paired with the returned exit result. |

Code inspection also confirmed that binary transport counts complete stdout bytes while diagnostic retention is capped separately; artifact overflow causes cancellation and a nonzero result. Text execution intentionally truncates retained output instead of rejecting a successful command for producing logs. The guardian creates the named container before starting a writer, checks owner EOF before start, and attempts exact-name removal in its finalizer. Guardian cleanup failure after ordinary completion produces a nonzero result. The outer wrapper may report timeout/cancellation as its primary code, but the tested cleanup failure remains explicit in diagnostics and cannot return success.

## Coverage limits

**Live execution coverage is incomplete.** These probes establish controller behavior against a controlled Docker substitute. They do not establish actual Docker daemon removal, image/runtime identity, cgroup enforcement, GPU/credential absence, or behavior during a real daemon outage. The synthetic inspection values must not be described as inspected production facts.

The 45-second stalled-guardian fallback and 30-second real CLI timeouts were inspected but not forced to elapse. Abrupt host failure, a blocked physical output device, pipe descendants unrelated to the controlled Docker-style relay, and power-loss recovery were not tested. The output sink and command/name/inspection-path arguments are trusted controller inputs. Live guardian cleanup and blocked transport require their own executor integration evidence before accepting the complete preparer. No Stage 3 acceptance is granted by this report.

## Retrievable evidence

Track this report and these evidence files:

- `security-transport/probe.py`: independent assertions and fixed-candidate reconstruction.
- `security-transport/fake_docker.py`: controlled CLI/process executor required by the probe.
- `security-transport/results.json`: retained final per-case results, runtime and source hashes.
- `security-transport/harness-ordering-results.json`: earlier harness result, retained for transparency. One text-tail assertion assumed stderr would arrive after stdout; separate relay threads do not guarantee that ordering. The corrected assertion checks exact total bytes, bounded retention and truncation without assuming stream order. The candidate code was unchanged.

```sh
python3 .scratch/.sflo/04-autonomy-environments/security-transport/probe.py
```

The script reconstructs the exact trusted commit files with `git show` into ignored `.gflo/security-transport/5295522d04df1e34d2826309e2617ac0a6bf46d7/`. It stores rerun observations there without overwriting the retained JSON. No duplicate frozen source tree needs publication. Reproduction requires Linux, Python 3.10 or later, local candidate Git history, and permission to fork/signal disposable test processes. No network fetch or Docker daemon access occurs. The script returns failure if a probe fails.
