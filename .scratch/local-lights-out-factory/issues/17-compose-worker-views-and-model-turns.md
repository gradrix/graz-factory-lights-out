# Compose bounded Worker views and model turns

Type: task
Status: resolved
Blocked by: 15

## Scope

Build a thin serialized model client and purpose-specific Worker views using versioned profiles. Validate typed WorkerResults and tool requests outside the model; reserve output capacity and retain manifest provenance.

## Acceptance

Deterministic tests cover malformed responses, timeout, context overflow, stale inputs, missing evidence and unsupported tools. Worker output cannot grant authority or mark work accepted. Live transport/structured-result checks use a verified target profile; no automatic cloud fallback.

## Answer

Implemented bounded Python Worker views and the serialized local vLLM client. Exact source/input bindings, required writable-source coverage, selection/omission provenance, explicit diagnostic projections and read/edit scope checks sit outside the model. The client checks the served model/context, tokenizes the actual chat template before generation, reserves output capacity, rejects protocol/schema/tool/scope violations and retains requests/responses/manifests/errors. No authority or acceptance command is exposed through WorkerResults.

Validation: 34 worker/client tests cover malformed and ambiguous responses, timeouts, overflow, serialization, stale inputs, missing evidence, unsupported tools, scope violations and endpoint restrictions. The full default suite passes 147 tests and 23 subtests; eight previously qualified optional broker tests skip without their live-test variables. Ruff/format and strict mypy pass.

Two real local-LLM repair smoke runs passed independent three-case process gates and reached durable acceptance. The final turn used 626 input and 75 output tokens in about 7.15 seconds. The buggy baseline was independently observed to fail. [Verification manifest](../worker-verification-results.json) and [worker documentation](../../../../docs/worker.md) preserve the exact evidence and limitations. This is a fixed coding smoke, not the twelve-task pilot. Task 18 still supplies automatic tool handling, retries and resume.

## Comments

2026-09-08: The user authorized proceeding. Actual local-model coding testing began in this slice; no serving flags, checkpoint or engine were changed and no repository content was sent to inference.
