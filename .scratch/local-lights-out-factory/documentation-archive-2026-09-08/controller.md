# Durable prepared-task loop

A `RunPlan` binds a prepared Work atom, immutable source bundle, trusted process-gate plans, local model profile/deployment provenance, pinned broker image and a finite model-turn allowance. `prepare_run` publishes its bytes and binds the plan in SQLite. Resubmitting the same plan is idempotent; changing a bound plan requires a new Work atom. SQLite schema 2 adds immutable run-plan bindings and migrates schema 1 without rewriting existing history.

```sh
gflo --db .gflo/pilot.db submit-run prepared-run.json
gflo --db .gflo/pilot.db run ATOM_ID
gflo --db .gflo/pilot.db status ATOM_ID
gflo --db .gflo/pilot.db resume ATOM_ID
```

The run JSON follows `gflo.controller.RunPlan`; the retained `.gflo/evidence/durable-loop-smoke-v1/plan.json` is a concrete local example. It contains trusted gate expectations and stays controller-owned. Model requests contain only the bounded Worker view. `submit` still accepts a bare Work atom without a runnable plan. `resume` without an atom ID retains its earlier behavior: reconcile expired leases without dispatching work.

The controller locks this Factory's artifact store against another controller, reconciles owned broker resources and expired leases, and qualifies the fixed broker profile before consuming a new attempt. It claims a Lease, asks the local model for a bounded result, and records raw model evidence as an immutable observation. A permitted source-file request expands a fresh Worker view; repeated reads and exhausted turn allowances fail the attempt. A validated edit is merged with the pinned source and published before the ledger receives its candidate digest.

The candidate executes once in a disposable smoke environment, then every mandatory process gate runs independently in clean containers. The smoke cannot replace any gate. Receipts and candidate bytes bind conditional acceptance. No source tree is modified or deployed: the accepted output is a verified content-addressed source bundle.

A candidate/gate failure produces a diagnostic projected from actual observations, excluding trusted expected-output plans. The next attempt cites that retained evidence and uses it in its Worker view. Attempts and model turns both have finite bounds. Exhausted attempt budgets quarantine the atom, retaining failed candidates, receipts and observations. Infrastructure/protocol errors stop automatic retries with a retained failure; after the cause is addressed, an explicit resume can use the remaining budget. This first loop does not implement a separate infrastructure-repair scheduler.

On resume, accepted work is reverified without invoking the model or gates again. A validating attempt reuses its immutable passing receipts and completes remaining gates. An interrupted running attempt is fenced as failed after environment reconciliation, and a new attempt receives recovery evidence. A leased retry keeps its stored diagnostic. Expired attempts follow the ledger's normal bounded reconciliation. Process-death tests cover interruption during generation and immediately after acceptance commits; neither creates duplicate acceptance.

All model, Docker and artifact operations occur outside SQLite transitions. Gate and acceptance transitions recheck the live Lease and bindings. The authoritative input for this capability is the immutable bundled snapshot, not a mutable Git working tree. This is one prepared-task loop: Product-graph scheduling, general repository import/export, deployment, dependency-aware integration and unattended supervision remain later work. SIGINT returns CLI exit 130 after normal cleanup. Abrupt termination requires `resume`; a full external supervisor is not implemented.

CLI run/resume exits 0 for accepted, 2 for a nonaccepted result, and 1 for errors. It returns durable status/history rather than a model-written success message. The full default suite has 162 passing tests and 23 passing subtests; eight optional Docker checks skip without explicit live-test configuration. Fifteen loop tests use real SQLite/artifacts with deterministic model/broker doubles and include actual subprocess death, retry/quarantine, view expansion, plan immutability, schema migration and CLI integration.

The live CLI smoke reached acceptance on one attempt through the real vLLM and broker, including three independent process cases. Repeated resume returned the same durable history. [Loop verification](../.scratch/local-lights-out-factory/loop-verification-results.json) preserves the run, source hashes and local evidence. This is not yet the twelve-task pilot.

## Cumulative model cost

`gflo --db PATH report ATOM_ID` reads a consistent ledger history and verifies
referenced artifact hashes. It reports every recorded model observation by Attempt,
validated prompt/completion tokens, observed model time, failure reasons, and totals
for retry Attempts separately. Missing validated usage or timing is explicit; token
sums are lower bounds when usage is unavailable. Repeated reporting does not mutate
history or invoke the model. Corrupt referenced evidence fails the report.

Model time includes client processing and waiting; it excludes broker execution.
Unrecorded work lost during process death, energy and replanning are not measured.
Completeness flags refer only to recorded observations, not all possible GPU work.

## In-flight model-server recovery qualification

```sh
PYTHONPATH=. .venv/bin/python scripts/check_inflight_recovery.py \
  --config infra/serving/vllm-5090-graphs.example.json \
  --output .gflo/evidence/NEW_INFLIGHT_RUN
```

This deliberately interrupts the owned server while a coding request is active.
The harness verifies a retained unaccepted transport failure, waits up to 300 seconds
for Docker's automatic service restart, and invokes ordinary controller resume.
It requires passing trusted gates, unchanged failed history, idempotent accepted
resume and an artifact audit. Resume is harness-triggered; no general infrastructure
supervisor was added. The interrupted request's unavailable token usage stays unknown.
[The live variation passed](../.scratch/local-lights-out-factory/inflight-recovery-verification.json);
it is one development fixture, not the full integrity campaign.

## Storage admission

`gflo --reserve-bytes 67108864 --db PATH run ATOM_ID` requires 64 MiB of free
space before dispatch and checks incoming artifact bytes against the same reserve.
The number is an example, not a calibrated operational recommendation. Declare it
before a qualifying campaign. `--reserve-bytes 0` is the development default and
disables admission. Python callers pass `reserve_bytes` to `WorkLedger`.

Admission checks both database and artifact filesystems before new work and resume;
artifact publication checks again before staging. This is a free-space observation,
not a reservation or a disk quota: concurrent writers, WAL growth and filesystem
metadata can still exhaust storage. Real write errors remain failures. A low-space
exception can be reported on stderr when durable diagnostics cannot be written;
it does not consume a fresh Attempt or create an acceptance. After freeing space,
use ordinary resume. Read-only inspection can use a zero reserve.

A bounded SQLite page-limit fixture exposed automatic rollback on SQLITE_FULL;
the transaction wrapper now avoids a second rollback that would hide the original
error. Fault tests never fill the host filesystem. They cover admission, staging/link
ENOSPC, SQLite-full rollback/reopen, and fresh/interrupted resume. They do not yet
qualify every storage failure window, including a failing commit/fsync.

## Worker change history

```sh
gflo --db PATH history ATOM_ID
gflo --db PATH history ATOM_ID --format json
```

The text view shows the original objective/source revision, each Attempt's outcome,
retained failure reasons, published candidate diffs and gate outcomes. JSON additionally
includes model-profile identity, model-evidence references, retry plans and full gate
receipts. Every candidate is compared with the immutable task baseline, not the prior
failed candidate. Attempts without a candidate remain visible. Referenced source,
model observation and gate-evidence artifact bytes are hash-verified; missing/corrupt
bytes fail the view rather than silently omit a failed candidate.

This is a view of existing evidence: no model calls, source edits, Git commits or
acceptance transitions occur. Worker rationale is not inferred from code changes.
Raw rejected model responses remain in model evidence; they are not rendered as
published candidates. Text output escapes terminal control characters in untrusted
source and diagnostics. Git integration history remains a later capability.

Storage recovery tests also inject failures before an acceptance COMMIT and after a
successful COMMIT whose acknowledgment is lost. On reopening, ordinary resume either
commits the retained passing receipts or returns the existing acceptance. Neither
path regenerates the candidate, repeats its completed gates, or inserts a second
acceptance. These are deterministic connection-boundary injections against a real
SQLite ledger; they do not simulate physical power loss or prove disk-controller
flush behavior. Separate artifact tests inject file, publication-directory and
cleanup-directory fsync failures, preserving evidence and successful retry.

## Recorded recovery checks

```sh
.venv/bin/python scripts/run_recovery_checks.py --output .gflo/evidence/NEW_SUBSET
```

The runner freezes source hashes and a fixed selector/count manifest before executing
22 deterministic checks: model protocol loss, gate-controller interruption,
acceptance commits and storage faults. It records each JUnit case, skips/failures and
elapsed time. A missing/skipped case or deadline failure fails its group. The report
explicitly separates this passing subset from the incomplete full integrity campaign.
Model protocol replies and gate interruptions are injected; live process-death evidence
is collected separately. An incomplete gate reruns against the original candidate;
a complete retained gate receipt is reused without another model call.

## Live execution-process death

```sh
PYTHONPATH=. .venv/bin/python scripts/check_execution_death.py \
  --output .gflo/evidence/NEW_EXECUTION_DEATH_RUN
```

The harness uses scripted proposals and real isolated broker containers. It verifies
the running fixture command is PID 1, sends SIGKILL or handled SIGTERM, and checks
exit 137/143, retained failure evidence, trusted validation, repeated-resume identity,
artifact integrity and cleanup. The TERM fixture explicitly installs a handler;
it does not test every possible application signal policy. Candidate smoke is
advisory: its failure cannot replace or waive mandatory clean validation. A killed
mandatory validation fails its gate and requires a fresh Attempt. GPU inference
is not involved. Failed injector qualifications are preserved separately from the
[four passing live cases](../.scratch/local-lights-out-factory/execution-death-verification.json).

## Abrupt controller death during validation

```sh
PYTHONPATH=. .venv/bin/python scripts/check_controller_death.py \
  --plan .gflo/debug/controller-death-plan.json \
  --output .gflo/evidence/NEW_CONTROLLER_DEATH_RUN
```

The supplied prepared fixture has one gate with two delayed cases and a scripted
`print(42)` candidate; the recorded plan is also retained in the run manifest.
A dedicated child controller receives real SIGKILL after candidate commit, before launch, during execution,
between cases, before receipt commit or after receipt commit. The parent reopens the
ledger and invokes ordinary resume, requiring no new candidate proposal, unchanged
recorded history, one acceptance, clean artifact audit and no owned container leftovers.
This validates abrupt process death rather than merely raising an exception. It does
not introduce an unattended supervisor or qualify all remaining integrity categories.
[All five live windows passed](../.scratch/local-lights-out-factory/controller-death-verification.json).
