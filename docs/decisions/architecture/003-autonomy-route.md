# Extend the small core through measured capabilities

Status: proposed route under accepted destination. Date: 2026-10-02.
Decision maker: agent; user requested local end-to-end autonomy and modular functionality.

Retain the current runner/worker/verification core. Add coherent reasoning assignments, a separate environment preparer, explicit research/browser capabilities, structured events and a small read-only view, then bounded planning and integration. Keep state transitions and permissions in ordinary controller code. Start serialized on the 5090; do not assume multiple large resident models fit.

Task boundaries follow one understandable objective and verifiable result, not a fixed token/line count. The proposed 8K–32K initial task-context range is an experiment; 128K remains available when justified. Test decomposition and reviewer diversity against the same tasks before promoting them. Same-model reviewers may share misconceptions.

Prepared workers remain offline. Network-enabled build/fetch and internet research use separately granted capabilities, no shared secrets and no worker Docker socket. Application browser tests use disposable services; arbitrary web browsing has a separate network/security boundary. Images, dependency inputs and browser versions are recorded, and repeated offline execution is verified.

Visibility uses durable events over the ledger and a small API/page before adopting telemetry infrastructure. OpenTelemetry is optional instrumentation, not the workflow authority. The [roadmap](../../roadmap.md) owns stage sequencing and acceptance; this record does not duplicate its thresholds.

Rationale and primary evidence: [feasibility research](../../research/autonomy-feasibility.md). This extends the current-core decision and supersedes first-release-only exclusions for future planning; it does not revive the deleted implementation. Current code still lacks these proposed capabilities. Broader project and deployment reliability remain experimental.
