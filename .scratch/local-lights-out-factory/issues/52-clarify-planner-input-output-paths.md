# Clarify planner input/output paths and identify missing-input failures

Type: task
Status: resolved

## Scope

Retained color plan reads its own not-yet-created test output. Preserve rejection;
explain read_paths versus writable_paths, expose bounded allowed-path presence from
whole snapshot metadata, and report exact task/path plus self-output guidance.
Do not infer existence from bounded context or silently normalize invalid plans.
Qualify against retained trace and a fresh planning-only call with unchanged model.

## Answer

Added bounded allowed_path_state using full snapshot metadata and explicit input/output
rules to planner briefs. Missing-input errors identify task and path and explain
self-output misuse. Replayed retained invalid plan remains rejected. No changes to
structural acceptance, no silent normalization, no loaded omitted source bytes.

Fresh same-request/model/budget planning returned a valid proposal first response
(2910 prompt/1902 output, 31.61s), compiled under unchanged policy. No worker runs or
product changes. All 451 tests/25 subtests pass with Docker enabled; ruff/mypy pass.
[Results](../planner-paths-results.json) retain historical rejection and new proposal.

Reconstruct source with leds-color-v2-fixture.json; call draft_feature with policy's
plain planning profile, deployment and planning paths. Raw .gflo/evidence/planner-paths-v1.
Next broaden prospective end-to-end features; no reliability claim from this seen case.
