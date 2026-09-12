# Choose implementation route after local-model halts

Type: task
Status: needs-info

## Decision

The owner approved the reusable/scalable CSV import POC. The pinned local model has
failed three prepared builds and a supervised continuation; references pass the
independent checks and larger runtime workload. Should Codex finish the application
directly and then use it to improve the factory, or should all application authorship
remain with the pinned local-model worker while reliability work continues?

## Why ask

Existing qualification rules preserve local-model authorship and prohibit manually
fixing delivered candidates. Reference code is reviewable under importflow/reference,
with retained checks and runtime receipts; promoting it would change the evidence
claim. The question was asked asynchronously while remaining verification/docs were
completed. Do not silently turn a reference into a factory delivery.
