# Diagnose intermittent memory qualification halts

Type: task
Status: resolved

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

## Answer — 2026-09-10

Reproduced the exact original halt on full qualification run 14 and memory-only run
35. A delayed-inspection experiment reproduced it on run 76; Docker's flag stayed
false through one second. Host observation of the same full container ID on another
failure recorded memory.events.local max/oom/oom_kill rising from zero, proving a
real memory-limit OOM kill. The exact internal Docker event-loss cause is unproven.

Qualification now runs a trusted allocator supervisor and requires increasing local
kernel limit/OOM/kill counters, the same cgroup, child return -9, and clean supervisor
completion. It never accepts exit 137 alone. All original isolation controls remain.
Ten regression cases were run red/green. One hundred prospective complete broker
qualifications passed; real unrelated-SIGKILL and no-allocation probes were rejected.
Full suite with Docker enabled: 402 passed, 25 subtests. Raw evidence remains ignored;
[portable results](../memory-qualification-results.json) retain the failures, kernel
confirmation and prospective proofs. `scripts/qualify_broker.py` supplies the retained
repeatable qualification loop. Kernel semantics: [cgroup v2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html).
