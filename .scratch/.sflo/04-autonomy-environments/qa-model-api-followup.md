# Generated telemetry API semantic QA

**PASS for this generated candidate**, run `0ff5575a451b`, candidate fingerprint `3f13c2ec38dae76fa66e8aa75e6d00f4f9731c0c5b72049fe96d3a3abc4bca25`, patch SHA256 `c87001dac87fa6fd31348204d5b1ca6d399f5a84b6ed1eb7b332edcf77f9c7e4`. Workspace fingerprint, patch and accepted verification/review artifact hashes match the frozen receipt. No new semantic defect found.

| Scope | Independent observation |
|---|---|
| Domain implementation | Validates duplicates before processing, copies groups and sorts without mutating input, tracks immediate predecessor across the window boundary, counts only in-window reset transitions and sorts Unicode device names. No retained cross-request state. |
| Additional cases | 100 deterministic randomized reports match an independent predecessor-search calculation; inputs remain unchanged. Fifteen also pass through an actual Uvicorn HTTP server. |
| Validation boundaries | Thirteen additional HTTP cases reject negative/over-limit/floating/boolean/string/null timestamp or reading values and overlong astral-Unicode names. A 40-code-point astral name succeeds. |
| Generated tests | All six methods pass after offline wheel installation from an unrelated working directory. They meaningfully cover ordinary multi-device/empty results, two resets across window boundaries, rejection classes, retained routes and direct-domain duplicate behavior. |
| Documentation | Actual documented offline pip wheel/install, unittest discovery and Uvicorn target commands succeed with placeholders resolved to the disposable project/wheel/install directory and installed package on PYTHONPATH, as documented. README request/response example matches real HTTP output. |

The model run's reported first-attempt acceptance and 285.71s duration remain historical rig facts from `rig-api-followup.json`; this independent check makes no new inference call. Existing external v2 checks/review complement the semantic probes; they were not presented as independently rerun here.

## Reproduction

```sh
python3 .scratch/.sflo/04-autonomy-environments/qa-model-api-followup/probe.py
```

[Host probe](qa-model-api-followup/probe.py), [inside-container cases](qa-model-api-followup/inside.py), [results/complete commands](qa-model-api-followup/results.json), [log](qa-model-api-followup/probe.log). Actual pinned Python3.12.13 image, prepared locked API dependencies, runc/network-none, nonroot and read-only candidate/dependency mounts; build/install only in disposable scratch. Container removed. No generated candidate edits, model/GPU/rig calls or blanket Stage3 acceptance claim.
