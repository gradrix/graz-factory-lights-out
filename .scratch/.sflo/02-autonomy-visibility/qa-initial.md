# Independent slice QA — initial candidate

**Candidate:** `3c3a834b9a33a8114ab44c2baf8c4bf11383f182` (GFLO product files). Checked 2026-10-02. **Verdict: repair required.** Product and maintained tests were not changed by QA. Parent subsequently changed tooling/docs, which were outside this frozen product check.

| Acceptance / risk | Observation | Verdict / evidence |
|---|---|---|
| Regression, repair, recovery, stall heartbeat | 29 tests pass; suite includes live process death and model wait heartbeat/elapsed distinction | Pass: `qa-evidence/suite.log` |
| Actual writable Docker child on SIGKILL and cancellation | Real pinned Python container wrote a counter; kill/cancel stopped container and further writes. Each recovered on attempt 2 and accepted exactly once; replay added no accepted event | Pass: `qa-evidence/probe.py`, `probe.log` |
| Second client, three runs, durable cursor | HTTP observed three accepted runs; cursor reconnect returned only newer events | Pass: same probe; workers here are deterministic, not local-model qualification |
| Read-only/path/secret bounds | POST/PUT/PATCH/DELETE rejected; hostile Host rejected; traversal, task/input/Git files and symlinks rejected; common secret patterns redacted; artifact capped at 1 MiB | Pass: same probe |
| Acceptance honesty | Changing accepted workspace invalidated HTTP status | Pass: same probe |
| Rendered page | Chromium desktop light and 375px mobile dark; empty/accepted views; patch link navigates; no horizontal overflow; disconnected page retains snapshot and reconnects | Pass: `qa-evidence/browser_probe.py`, `browser.log`, four PNGs; mobile screenshot visually inspected |
| Start observer before first run | Uninitialized SQLite causes uncaught OperationalError and HTTP disconnect; initialized empty-state control correctly displays No runs yet | **Defect D1**: `browser.log` |
| Cancel during startup | During startup cleanup, process exits but observer reports pending/starting, owner false, cancellation requested true. Inactive pending cancellation control correctly reports cancelled | **Defect D2**: `startup-cancel.log` |

## Defects

**D1 — fresh installation appears disconnected.** `Observer.connect` opens only an existing database, and the HTTP handler does not handle SQLite errors. `serve` can start before any run, but its first API poll aborts the connection. The rendered empty state is therefore unavailable in this ordinary initial state. Return an empty run list for absent storage (without creating state through the read-only interface), while handling genuine read failures explicitly.

**D2 — startup cancellation retains false pending/starting state.** `_resume` calls cleanup before the attempt-level exception handler. SIGINT during that work escapes without recording cancelled; `Execution.__exit__` clears ownership. The observer's interruption correction only covers running/repairing. Extend lifecycle exception handling to startup and preserve explicit cancellation state. Probe uses a sleeping cleanup adapter to deterministically reproduce the same startup boundary; no active Docker writer is needed for this finding.

## Reproduce

Run from `/home/gradrix/repos/gflo`:

```sh
python3 -m unittest discover -s tests -v
python3 .scratch/.sflo/02-autonomy-visibility/qa-evidence/probe.py
/tmp/gflo-browser-check/bin/python .scratch/.sflo/02-autonomy-visibility/qa-evidence/browser_probe.py
python3 .scratch/.sflo/02-autonomy-visibility/qa-evidence/startup_cancel_probe.py
```

First three commands exit 0 (browser probe prints D1 separately); startup probe exits 1 on the failing contract assertion after its conforming control passes. Probes create isolated temporary repositories/state and clean up their own containers. Docker used local image `sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578`, no GPU or network inference.

## Boundaries

This is slice acceptance, not final destination acceptance. Real local-model three-project qualification belongs to the separate rig receipt. Daemon outage/host reboot, container creation race, unusual secret encodings, full accessibility audit, and all theme/viewport combinations were not exercised. Current unit suite supplies model-stall timing evidence; independent Docker probes exercise active writers rather than simulated container calls. Repairs require a new candidate identity and focused independent recheck.
