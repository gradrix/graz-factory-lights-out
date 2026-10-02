# Initial acceptance

Status: accepted scope, 2026-10-01.
Decision makers: user requested minimal requirements, gradual acceptance, real scenarios, tests/docs/coverage and removal of unnecessary complexity. Agent supplies the concrete first acceptance below.

First release: doctor, run, status and resume commands; one repository task with frozen acceptance checks; isolated edits; bounded tool/model requests and attempts; deterministic verification; repair from actual failure evidence; durable attempt history and interruption recovery; exportable patch; actionable errors. No automatic integration into the original repository.

Prove on a small existing-project bug, a multi-file feature and a small new application. Exercise failure/repair and restart recovery with deterministic fault injection as well as live model tasks. Report real-model successes and failures without selecting only passing runs. Compare long-context suitability without assuming retrieval means coding competence.

Quality gates: behavior tests for acceptance/repair/recovery and isolation; measured coverage with explained gaps; real offline sandbox runs; usable README and operational rollback; review for unnecessary layers, dead code and inflated claims. Independence requires a fresh checker context when available. Model-written reports cannot alone pass a task.

This records the accepted first release, not the eventual product limit. The 2026-10-02 autonomy destination is defined in 002-autonomous-delivery.md and docs/roadmap.md. Reliable large-project autonomy remains unproven; each new capability needs its own acceptance.
