# Fresh local core

Status: accepted starting design, 2026-10-01.
Decision makers: user authorized the reset and local-first incremental factory; agent chose the initial implementation details below.

Replace the previous implementation and roadmap with the current small core. The user superseded the initial archive choice on 2026-10-02: delete previous-factory files and the reset archive. That archive has been deleted. Current model measurements and first-version qualification remain relevant evidence.

Use Python standard library, SQLite and artifact files in one CLI application. Runner owns transitions and attempts; worker owns the model/tool loop; verifier owns sandboxed executable checks. A Docker adapter supplies offline execution. No plugin framework, roles hierarchy or workflow DSL. Keep interfaces narrow and introduce further seams only when behavior varies.

Use one local inference endpoint and serialize runs. The proposed serving default is the previously tested Flash Coder 131072/Q4 profile, subject to live repository qualification. Keep original vLLM as an explicit rollback. Weights, runtime and sandbox image must be installed locally; running a prepared task must not download dependencies or contact cloud services. Model service and Docker still depend on the host/WSL being alive.

Acceptance code is supplied by the operator and snapshotted outside the worker mount. Source repository remains unchanged; accepted output is a patch and isolated candidate. Containers receive no network, credentials or Docker socket. Container isolation is a practical execution boundary, not a proof against malicious code/kernel exploits.

Evidence: docs/model-profile.md, docs/pilot-results.md and the reset request. SFLO/Gas City inspire durable work and bounded gates; no runtime or storage format is imported. Assumption: Python standard-library projects are sufficient for the first pilot; broader stacks need prepared sandbox images later.
