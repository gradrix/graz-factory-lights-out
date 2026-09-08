# Build the execution broker and trusted gates

Type: task
Status: resolved
Blocked by: 15

## Scope

Use disposable candidate and separate clean validation containers through a narrow trusted broker. Capture commands, exit status, logs and candidate identity outside worker control.

## Acceptance

Workers cannot access Docker authority, canonical state, credentials or validators. Timeouts and interruption clean up owned resources. Required resource controls fail closed. Tests distinguish candidate failure from evaluator failure and bind passing evidence to exact inputs/outputs. Actual execution requires the applicable controls in target verification to pass.

## Answer

Implemented the narrow `DockerBroker` and trusted `ProcessGate` runner. Validated immutable text bundles execute in bounded disposable containers with no host mounts/network/GPU/credentials; each validation case uses a separate clean container. Controller-owned expectations never enter containers. Captured image/container/command/input/output/exit/OOM identities bind gate evidence to the exact contract and candidate. Candidate failures and evaluator failures produce distinct non-passing receipts.

Actual target qualification passed before candidate execution: effective security/cgroup controls, bounded memory OOM and PID exhaustion. The live suite also verifies environment separation, missing-control refusal, timeout/output bounds, interruption cleanup, ownership-safe stale-resource reconciliation and durable passing acceptance. One live output-flood test exposed blocked Docker kill acknowledgement; detaching capture before kill fixed it, and failed-run evidence is retained.

Validation: 121 tests and 23 subtests passed with all eight live broker tests enabled; Ruff and strict mypy pass. [Verification manifest](../broker-verification-results.json) pins source and local evidence hashes. [Broker documentation](../../../../docs/broker.md) records the narrow Python capability and limitations. Worker views/model transport and full-loop integration are still tasks 17–18.

## Comments

2026-09-08: The user authorized proceeding and asked when actual local-model testing begins. Synthetic inference already passed; real model-driven code changes follow worker/model integration and the durable loop, then the twelve-task pilot.
