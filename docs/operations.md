# Operations

All commands operate on a local ledger and its associated artifact store. Run
`gflo --help` and `gflo COMMAND --help` for argument details.

| Command | Purpose |
| --- | --- |
| `submit CONTRACT` | Store a validated Work atom; a contract alone is not executable. |
| `submit-run PLAN` | Store a complete, verified RunPlan and its input artifacts. |
| `run ATOM` | Execute a submitted plan within its attempt and model-turn budgets. |
| `resume ATOM` | Reconcile and continue a prepared run. |
| `resume` | Reconcile expired leases only; dispatch no workers. |
| `status ATOM` | Inspect attempts, receipts, events, and acceptance findings. |
| `history ATOM` | Review retained candidate diffs and outcomes; supports `--format json`. |
| `report ATOM` | Sum recorded model time and tokens across attempts, including failures. |
| `audit-artifacts` | Report missing, corrupt, unreferenced, and staged bytes; delete nothing. |
| `integrate PLAN --current-state STATE` | Validate a prepared combination of accepted changes. |

Pass `--db PATH` and optional `--reserve-bytes N` before the command. The storage
reserve is an admission check, not a disk quota or reservation; zero disables it.
Qualification campaigns use 256 MiB. Reports flag missing usage instead of inventing
costs, and do not measure energy or work lost before it was recorded.

## Recovery

A prepared atom follows `ready → leased → running → validating → accepted`.
Failure makes it `retry-ready` while attempts remain, otherwise `quarantined`.
Contracts permit at most ten attempts. Retries retain earlier candidates and cite
failure evidence. Infrastructure failures halt the loop until explicit resume.

Expired leases fence prior work. The controller reconciles owned execution
containers before retrying. Interrupted running work gets a fresh attempt;
interrupted validation can reuse its durable candidate and receipts. Replaying
accepted work verifies stored evidence without creating a second acceptance.
Source files in your checkout are never modified by this loop.

Keep the ledger and artifacts together on local storage. Stop controllers before
making a consistent backup that includes SQLite WAL state. Multi-host operation,
host-clock changes, storage loss, and unattended supervision remain unqualified.
An artifact audit detects loss; it cannot reconstruct missing bytes. Orphan and
staging files remain available for investigation rather than automatic deletion.

## Acceptance findings

Historical `accepted` status is not sufficient permission to reuse a result.
`status` also exposes `acceptance_challenged` and `acceptance_findings`.
A trusted caller records independently verified contradictory evidence using
`WorkLedger.record_finding(AcceptanceFinding(...))`. The record binds the atom,
contract, candidate, evidence artifact, and reason. There is no worker-facing or
CLI mutation command for this operation.

Findings preserve the original acceptance and appear in history. Controller replay
and integration reject challenged candidates; an accepted integration also rechecks
its children when reused. Losing the finding's evidence bytes does not clear the
block. Repair needs a new atom with independently passing evidence; there is no
clear/dismiss operation or automatic revocation of external copies.

The first finding atomically advances the ledger reader version from 2 to 3.
Older readers refuse new opens. Stop already-running older controllers before
upgrading: a schema marker cannot replace code on an open connection. New readers
also support version-2 ledgers, and version-1 ledgers migrate to version 2.

## Prepared integration

```sh
gflo --db RUN/ledger.db integrate RUN/integration-plan.json --current-state RUN/current-state.json
```

The plan pins the common base, accepted children, upstream contracts, scopes,
broker image, and mandatory combined gates. The current-state file is trusted
input: update it when the base or provider contracts change. Overlapping edits,
deletions, stale inputs, and challenged children are rejected. Every child must
have a RunPlan; integration of integration children is not implemented.

Repeated integration resumes retained validation or reuses a verified acceptance.
Semantic failure retains evidence and requires new prepared repair work. Current
input checks do not provide an external compare-and-swap or Git promotion.

## Opt-in bounded escalation

`vllm-python-worker-escalating-low-v1` uses one model turn per attempt.
`vllm-python-worker-escalating-tools-v1` permits three turns, allowing source reads
before an edit. Both require exactly two attempts, an 8,192-token context budget,
and a 4,096-token output reserve in the WorkAtom. Initial turns use at most 2,048
output tokens without thinking; retry turns use at most 4,096 including reasoning
with explicit low effort. RunPlan validates these limits. Resume preserves attempts
and the pinned profile; changing a failed run's profile in place is rejected.

These profiles are opt-in. The low-effort single-turn profile passed a scoped
23/24-task qualification; the tool-capable profile passed the scoped three-build
stateful qualification after feedback and interface-context improvements. The default worker profile remains unchanged.

Failed process gates provide bounded feedback from observed execution data. For
JSON stdout, up to eight `error` fields are surfaced before truncated logs, with
JSON paths to locate them in the workflow. These fields can include deliberate
invalid-request cases; their presence alone does not identify a gate mismatch.
Expected outputs remain private, and complete raw output remains in artifacts.
