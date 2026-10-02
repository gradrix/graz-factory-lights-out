# Preparation lifecycle and resource QA

**PASS for ordinary process-failure scope**, frozen `25f75c3275739cc7cc2a4fc5a4e16580b81511d1`. Independent s-qa with real local Docker containers, private stores and no network targets.

| Probe | Measured outcome |
|---|---|
| Preparation timeout | Delayed stdlib assembly stops with code 124 after 3.12s; owned container absent; no reusable receipt. |
| Preparation cancellation | Event cancellation stops delayed assembly with code 130 after 2.11s; owned container absent; no reusable receipt. |
| Actual controller SIGKILL | Waited until its assembly container was running, then SIGKILLed the owner. Guardian removed that exact container in 0.17s; no reusable receipt. |
| Restart after SIGKILL | Next real preparation removes stale private scratch, completes smoke/publication and resolves its fresh receipt. |
| Scratch capacity | Finite 20MiB write to configured 16MiB `/tmp` fails with ENOSPC (28); process handles the failure and exits successfully. |
| PID capacity | Finite attempt to launch at most 150 sleeping processes fails with EAGAIN (11) at 126 children, consistent with configured 128 total PIDs. Children explicitly terminated/waited; container removed. |
| Memory capacity | Finite 1,200MiB allocation under actual 1GiB memory/no-extra-swap cap terminates with code 137 in 0.62s; container removed. This is observed limit termination, not a separately captured kernel OOM event. |

All resource probes used the unchanged preparation executor: pinned Python 3.12.13 image, explicit runc, network none, nonroot, dropped capabilities, read-only root, 1 CPU and 128 PIDs. Actual inspected configuration is retained. No resource test exceeded its configured container boundary. Scratch coverage measures `/tmp`; the separate 480MiB `/work` setting is inspected, not independently filled.

Fault injection changes only the disposable Python process's stdlib assembly command to a bounded sleep, allowing timeout/cancellation/kill during actual preparation. No maintained code or protected recipe was edited. Abrupt death intentionally leaves unpublished private scratch until restart; its container is removed immediately and no environment is reusable.

## Reproduction and evidence

```sh
python3 .scratch/.sflo/04-autonomy-environments/qa-preparation-lifecycle/probe.py
python3 .scratch/.sflo/04-autonomy-environments/qa-preparation-lifecycle/recovery.py
```

[Probe](qa-preparation-lifecycle/probe.py), [results/configurations](qa-preparation-lifecycle/results.json), [log](qa-preparation-lifecycle/probe.log), [recovery probe](qa-preparation-lifecycle/recovery.py), [recovery result](qa-preparation-lifecycle/recovery-result.json). Run recovery immediately after the main probe to exercise its preserved SIGKILL scratch.

Prior [publication cleanup recheck](qa-profiles-recheck.md) independently proves failed outer cleanup cannot publish/reuse a new environment and preserves an existing valid receipt. Existing guardian transport fault evidence remains separate; shared Docker daemon failure was not induced. This does not exhaust every publication kill point or constitute security/Stage 3 acceptance. No models, GPUs, rig calls or shared-service changes.
