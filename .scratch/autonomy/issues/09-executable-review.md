# Can read-only local execution reduce review false acceptance?

Type: prototype
Status: active discovery after unit08 closure
Owner: /root coordinator

[The planning pilot](08-planning-value.md) found two delivered test/documentation defects missed by fresh text-only local review. Independent executable probes confirmed them against conforming controls. The agent selects the next question under the user's continuing local-autonomy authorization: can the same local model use bounded offline execution to find these defects without rejecting their corrected controls?

Compare evidence against the frozen originals and separately labelled conforming copies. The model receives the original public objective and candidate, with general review instructions; it receives no defect hints, private oracle/reference implementation for other cases, or prior findings. Small discriminating gates precede any broader cohort or maintained integration. Preserve every failed/malformed review, timeout and false verdict.

Prototype code stays on a separate branch/worktree and cannot silently replace maintained Reviewer. Reuse measured model profile and qualified lifecycle/capture mechanisms where unchanged. The verifier may execute commands only in an offline, nonroot, resource-bounded container with read-only candidate and dependencies, no credentials/socket/GPU, and disposable scratch. No candidate writes, acceptance edits, network search or original-project integration. The controller owns limits and verdict validation.

An executable reviewer could still choose weak probes or misinterpret evidence. Four known-case reviews cannot establish general reliability. A passing discriminating gate permits a fresh-case qualification, not automatic production promotion. Failed qualification should narrow the repair route instead of adding a management hierarchy.

Decision basis: [planning outcome](../../../docs/decisions/architecture/008-planning-pilot-outcome.md). Contract/delivery and precise limits must be frozen before implementation and real calls.

[Delivery09](../delivery/09-executable-review.md) binds the frozen initial four-case discriminator and isolated execution.

Initial trial completed with one correct valid repair and three incomplete reviews; raw evidence and independent audits remain in the initial run. The [protocol successor](../../.sflo/09-autonomy-executable-review-protocol/run.md) reserves a strict finalization request and one bounded truncation recovery under a new contract. This is an agent-defined repair, not a new user requirement or a reliability claim.
