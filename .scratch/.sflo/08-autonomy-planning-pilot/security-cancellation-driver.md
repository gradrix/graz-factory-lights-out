# Cancellation driver independent controlled review

2026-10-04. **PASS for the bounded cancellation driver controls; actual serving cancellation remains unmeasured.** No model, rig, Docker or network calls. Only the prototype test file was written; root owns driver repairs and builder owns the evolving harness. Contract SHA256 `992ed9637b164e68cf3093cca817938ccd7ec31593813b789e69927964c8d7c9`.

## Exact reviewed source

- `ops/cancellation_probe.py` SHA256 `eef6fba8f02498c2c247f2d264a1dca5bbf2bb5caec5521db97f63a29b443128`
- `ops/test_cancellation_probe.py` SHA256 `3ecdfad0418381d6a547466c840a875ebeea09a9db8cb02dbf9a734a9ded4591`
- `ops/planning_pilot_prototype.py` SHA256 `e4cf696ebe0e1a1fe363cd35677c590013b363214edb876fe71b78232fd9a48b`

The planning harness hash identifies the imported version at this test run; its full independent security assessment remains separate. Driver tests stub its strict probe for lifecycle experiments and exercise its real lease. This report cannot qualify an altered driver or evolving probe implementation by implication.

## Independent measured controls

[Final output](cancellation-controls-final.txt): **16 tests passed in3.841seconds**. Reproduce from the prototype with `python3 -m unittest discover -s ops -p test_cancellation_probe.py -v`. The test file belongs to the disposable prototype branch, not maintained tests.

- Positive fake busy→deliberate signal→idle route passes; every controlled launched process is local sleeping Python without credentials or inference.
- Unknown preflight prevents launch/debit; unknown active state does not count as busy; unknown cleanup never passes.
- Normal completed-response race is inconclusive. Deadline during busy observation and actual SIGTERM cancellation do not pass. Cancellation delivered during durable debit prevents client launch.
- Actual owned process group termination and a parent/descendant group control confirm absence. The latter parent reaps its child; no orphan is intentionally left. These are local OS lifecycle measurements, not llama.cpp cancellation measurements.
- A main-entry control confirms the real pilot lease is held during preflight and cleanup observations. One control uses real wall-clock sleeps to verify at least one second between the two final idle observations and at least three seconds overall. Other controls shorten polling sleeps and cleanup allowances to exercise branches efficiently; they do not claim a full60/150second endurance run.
- Consumed admission refuses a fresh output path without launching another client, persisting `failed`/`FileExistsError` after root's exception-handling repair.
- Actual `validate_admission` checks use the real contract plus private hashed code/evidence/identity/config fixtures, independently rejecting code, request, controlled-test evidence, security-review evidence, identity, public endpoint and lease-path drift. Lifecycle branch tests mock validation to isolate those branches; this separate admission test does not.
- Oversized evidence refuses. A controlled transport exception containing a private sentinel persists only its type, not the secret message. The child makes one request-seam invocation with1MiB response cap; no actual transport occurs.

## Findings and repair rechecks

Early source review identified cancellation after debit still permitting launch, incomplete admission evidence/identity/profile binding, and admission reuse under a different caller-selected lease parent. Root repaired these seams; the final controls verify refusal. The consumed-admission outcome now persists a safe error type. No open driver finding remains in this scope.

Initial logs are preserved: `cancellation-controls-initial.txt` contains fixture failures caused by an admission-marker change landing during the first run (missing temporary admission fixture), not product defects. `cancellation-controls-1.txt` and `cancellation-controls-2.txt` record intermediate13/16case passes. The final log and source hashes above supersede their tested identities.

## Limits and next gate

Strict probe endpoint parsing/binding, full planning harness, fixture isolation and Git checkpoint security remain separate frozen review obligations. The current driver requires a valid same-identity busy classification and later settled idle; fake probes demonstrate its decisions, not the truth of actual endpoint data. No real request cancellation, model queue drain, server restart, daemon outage or abrupt SIGKILL of this supervisor was exercised. A supervisor SIGKILL is not handled by its Python finally block and is not claimed as a supported cancellation path here.

Only the separately frozen/admitted one-request experiment may measure actual service transition. This PASS does not authorize that execution by itself or any project arm.
