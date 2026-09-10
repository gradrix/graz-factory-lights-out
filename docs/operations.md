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
| `history ATOM` | Review retained candidate diffs and outcomes; supports `--format json` and `--attempt N` for a positive attempt ordinal. |
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

To inspect only the second attempt, use `gflo --db PATH history ATOM --attempt 2`.
Add `--format json` for structured output. The filter preserves task-level status,
accepted candidate identity, and acceptance warnings. Unknown ordinals fail;
all retained history integrity checks still run, including unselected attempts.

## Draft a feature plan

`gflo plan-feature REQUEST --profile PROFILE --deployment DEPLOYMENT --output NEW_DIR`
asks the local model to propose tasks, dependencies, interface contracts, tests,
and documentation work from a pinned source snapshot. REQUEST is a `FeatureRequest`:
feature ID, objective, requirement mapping, source revision and SourceBundle, allowed
paths, initially selected paths, and a catalog of named pinned environments.
PROFILE is the existing default non-thinking ModelProfile; DEPLOYMENT must match
its recorded digest. Environments are selected from the trusted catalog, not installed
by the model. Generate the request schema with:

```sh
.venv/bin/python -c 'import json; from gflo.planning import FeatureRequest; print(json.dumps(FeatureRequest.model_json_schema(), indent=2))'
```

`gflo check-plan REQUEST PROPOSAL` checks binding, requirement coverage, source
references, scopes, known environments, dependency cycles, and unordered overlapping
writes. It does not assess semantic quality or authorize execution. Review proposed
interfaces and test adequacy before preparing WorkAtoms and trusted gates.

Planning v2 uses two attempts, three turns each, 12K total / 4K output tokens,
without thinking. Source reads retain the two most recent files, with a bounded
interface index for navigation. Existing output directories are refused: there is
no implicit restart or budget reset. Raw calls and observations remain in the run's
artifact store. Interrupted runs can have incomplete summary files; immutable
artifacts are the retained evidence. Transport/model errors halt explicitly.
A `needs-review` result may contain unanswered questions and is always a draft.

## Repository snapshots

Capture source on the trusted host, which requires Git and a quiescent checkout.
Keep the artifact store ignored or outside the captured repository:

```sh
gflo repository --store .gflo/repository-artifacts capture .
gflo repository --store .gflo/repository-artifacts list SNAPSHOT_DIGEST --scope gflo
gflo repository --store .gflo/repository-artifacts read SNAPSHOT_DIGEST gflo/cli.py --max-lines 80
gflo repository --store .gflo/repository-artifacts search SNAPSHOT_DIGEST validate --scope gflo
gflo repository --store .gflo/repository-artifacts select SNAPSHOT_DIGEST gflo/cli.py --purpose context
```

Use `artifact_digest` from capture as `SNAPSHOT_DIGEST`. Commands return JSON without
creating a work ledger. Search returns one hit per matching line (first occurrence),
with source/file identities and explicit completeness and budget reasons. Listing
supports `--after`; reads preserve complete lines within byte/line budgets. No scope
means all snapshot paths for this trusted API. Worker access is not enabled implicitly.

Context selection reports omitted requested files. `--purpose execution` refuses
any omitted requested file; an explicit subset still does not validate the whole
repository. Both selections retain existing bundle limits. Capture rejects unsupported
files rather than silently dropping them; see [architecture](architecture.md#repository-scale-source-access).

To propose edits, create a JSON mapping from path to
`{"expected_digest": "ORIGINAL_FILE_DIGEST", "content": "replacement text"}`.
Use `null` as expected digest only for a new file. Then run:

```sh
gflo repository --store .gflo/repository-artifacts apply SNAPSHOT_DIGEST edits.json --current SNAPSHOT_DIGEST --writable gflo/cli.py
```

The caller supplies the trusted current identity; this command cannot establish
checkout freshness for them. It publishes a derived snapshot in the same store,
preserves omitted files and executable metadata, and changes no checkout or acceptance.
Deletion and cross-store export are not implemented. Raw artifacts in `.gflo/` must
be transferred separately to reuse snapshots on another machine.

## Reviewed task preparation and feature runs

`gflo prepare-task` prepares an independent root task without submitting or running
it. `gflo run-feature` executes/replays a reviewed snapshot-backed graph, preserving
accepted-base bindings and stopping on task or combined-validation failure.
`plan-feature` supports snapshot requests with `--store` and repeated `--context-path`
flags; `needs-info` means the model returned clarification questions without a plan.
See [product intake](product-intake.md) for the complete flow, schemas, source-store
requirements, current-state ownership, and qualification limits.

For the opt-in planning comparison, add `--board` to a snapshot `plan-feature` command.
Inspect each role's `report.json`, the coordinator's `synthesis.json`, and the top-level
`result.json`. An advisory-budget halt or specialist failure produces no executable
plan. The single-planner path remains the normal default; see
[the board experiment](product-intake.md#optional-specialist-board-experiment).

A specialist question or blocker returns `needs-info` immediately. Inspect root
`questions.json` and the completed role reports; no coordinator synthesis is
expected on this path.


For a preauthorized feature, use `build-feature` as described in
[product intake](product-intake.md). Inspect root `result.json`, `feature-plan.json`,
and `planning/` evidence. `needs-info` returns product questions; `policy-halt`
identifies an unsupported plan; `planning-halt` retains exhausted/interrupted
planning. Task/integration halts retain the normal ledger evidence. Interrupted
execution clears prior success in the build result before revalidation and can be
replayed with the same command. Exit 0 means accepted, 2 means a reported halt,
1 means an error, and 130 means interruption. Build output binds the local store
path; portable fixtures recreate a run, not a moved runtime directory's identity.
