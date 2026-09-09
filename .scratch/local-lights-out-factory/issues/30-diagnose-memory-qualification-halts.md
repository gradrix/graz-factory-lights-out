# Diagnose intermittent memory qualification halts

Type: task
Status: ready-for-agent

## Evidence

Two independent campaigns stopped on memory probes returning exit 137 with
Docker State.OOMKilled false. Basic controls and PID probe passed. Explicit
requalification succeeded previously without relaxing any limits.

Retained reports:
- `.gflo/evidence/stateful-inventory-feedback-v1/ledger.db.artifacts/7b1c9d2935e2ee50ef3cdacc91f1bcf763f08d0f94e547cd765a41fa2d6f098c`
- `.gflo/evidence/self-history-filter-contract-v1/ledger.db.artifacts/13e681e79429aa9f23f8d994c5410267b4ec1137b30fcdba16e560781eacde5e`

## Next investigation

Build a repeated, retained resource-probe reproducer. Distinguish an inspection
race, the kernel killing only the bootstrap's child process, and unrelated SIGKILL.
Do not accept exit 137 alone as proof of memory enforcement. Any replacement proof
must be independently tied to the same container/cgroup and retain existing
restrictions. Add failure-mode regression checks and qualify prospectively.
This trusted broker change is separate from the worker's CLI-only trial.
