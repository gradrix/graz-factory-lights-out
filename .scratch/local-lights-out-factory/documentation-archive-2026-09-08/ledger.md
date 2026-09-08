# Durable Work ledger

The first controller slice submits prepared Work atoms, persists immutable Attempts and events, fences expired Leases, and accepts a candidate once against stored trusted gate receipts. It now also publishes and verifies [immutable artifact bytes](artifacts.md). The [broker and trusted process gates](broker.md) now execute the fixed Python process-contract capability in separate containers. The [bounded worker/model client](worker.md) is implemented. The [prepared-task loop](controller.md) now connects dispatch, bounded retry and resume. Product-graph dependency resolution remains pending.

## Install and run

The tested environment is Python 3.13.5, recorded in `.python-version`. The package requires Python 3.11+; the standalone serving/target scripts retain their standard-library environment. `requirements-dev.lock` pins the tested runtime and development dependencies; the build backend is pinned in `pyproject.toml`.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock -e .
.venv/bin/gflo --db .gflo/example.sqlite3 submit examples/work-atom.json
.venv/bin/gflo --db .gflo/example.sqlite3 status example-provider-edit
.venv/bin/gflo --db .gflo/example.sqlite3 resume
```

On this Debian checkout, `ensurepip` is unavailable. The environment was created without bundled pip, then populated using the installed system pip's `--python` option:

```sh
python3 -m venv --without-pip .venv
python3 -m pip --python .venv/bin/python install -r requirements-dev.lock -e .
```

The example is only a schema/submission demonstration: its repeated-letter digests and profile references are placeholders, not verified inputs. It remains `ready`; no worker starts. `resume` reconciles expired leases and explicitly reports `workers_dispatched: false`. Running `python -m gflo` is equivalent to the installed entry point. Missing databases are errors for status/resume.

## Contract and lifecycle

`gflo.records.WorkAtom` records objective, source/precondition identity, requirement/module references, scope, profile references, tools, required gates and their validator digests, context/output/recovery budgets, expected output schemas and idempotency/integration keys. JSON validation is strict: unknown fields, unsupported versions, coercible numeric strings, booleans used as integers, malformed digests, traversal paths and duplicate gate/output identifiers fail before persistence. Nested records and tuples are frozen.

A prepared, dependency-ready atom starts at `ready`, then follows `leased → running → validating → accepted`. Failure or expiry yields `retry-ready` while budget remains, otherwise `quarantined`. This slice does not implement planning, supersession, graph integration, lease renewal or cancellation. A retry creates a fresh Attempt and Lease; the old history remains intact. There is a ten-attempt maximum per atom, with a smaller budget permitted by the contract.

| Trusted control-plane method | Effect |
| --- | --- |
| `submit(atom)` | Persist the contract; identical resubmission returns the same atom ID. Reused IDs/keys with changed content conflict. |
| `claim(atom_id, owner, lease_seconds=300, retry=None)` | Atomically lease ready work. A retry must cite the last failure event and change strategy or supply new evidence. |
| `start(lease)` | Record that the leased Attempt is running. |
| `candidate(lease, digest)` | Record the candidate identity and enter validation; cannot accept it. |
| `record_gate(lease, evidence)` | Persist an immutable trusted-runner receipt bound to the Attempt, contract, inputs, candidate and pinned validator. |
| `accept(lease, current_inputs_digest=...)` | Accept only with all mandatory passing receipts and matching current input identity; exact repeated acceptance returns the original receipt. |
| `fail(lease, reason)` | Preserve the diagnostic and consume the Attempt; return its failure event ID. |
| `reconcile()` | Fence expired Attempts, append expiry diagnostics and return affected atom IDs. |
| `status(atom_id)` | Read a consistent snapshot including contracts, Attempts, events and gate receipts, without exposing lease tokens. |

Use `with WorkLedger(path) as ledger:` to close connections reliably. Each connection belongs to one thread. Mutations use short `BEGIN IMMEDIATE` transactions: competing connections serialize before checking eligibility. SQLite uses foreign keys, WAL and `synchronous=FULL`. Contracts, Attempts, events, gate receipts and acceptances reject SQL updates/deletes through append-only triggers. Scheduling state is a mutable projection committed with its corresponding event. Unsupported schema versions fail; no migration is attempted implicitly.

## Authority and recovery boundaries

The API and database are trusted controller resources, not a worker protocol. A Lease fences stale results; it does not authenticate a model or sandbox. There is no CLI command to record gates or accept work. Future workers must have neither these APIs nor filesystem access to the database.

Gate receipts are durable in SQLite; the ledger verifies referenced evidence and candidate bytes through its append-only artifact store, and the trusted process-gate runner can now supply receipts after independently collecting evidence. Other validator capabilities are not implemented. Its `runner_id` is provenance, not an authentication mechanism. Failed/inconclusive receipts cannot be overwritten with passes; revalidation requires another Attempt.

`current_inputs_digest` must come from the controller's authoritative input snapshot, held stable through validation/acceptance. The ledger compares identities; it cannot notice external working-tree changes on its own. The execution broker and integration code must supply source-tree enforcement before live acceptance is enabled. Gate and expected-output schema digests are bindings, not proof of actual execution or output conformance.

Reconciliation does not kill processes or imply they performed no side effects. The future broker must isolate and reconcile old environments before dispatching a retry. The retry record cites retained failure evidence and a changed strategy or new evidence digest; the ledger verifies existence and integrity of that referenced content. Cross-atom repeated-failure accounting and autonomous re-planning remain later work.

Local process-crash recovery is tested. Storage loss, backup/restore consistency, host-clock adjustments, multi-host operation and unattended supervision are not qualified here. Keep the SQLite database on local storage and back up its WAL/artifact state consistently once that facility exists.

## Verification

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check gflo tests/test_ledger.py
.venv/bin/ruff format --check gflo tests/test_ledger.py
.venv/bin/mypy gflo
git diff --check
```

Tests use real SQLite databases, independent connections and CLI processes. They cover races for claims/acceptance, expiry and retries, recovery-budget exhaustion, evidence/input mismatches, immutable history, reopening persisted gate receipts, and forced process death mid-transition. Existing serving and target tests are included in pytest discovery. None of these tests use a live model.

Implementation references: [Pydantic strict validation](https://docs.pydantic.dev/latest/concepts/strict_mode/) and [Python SQLite transaction control](https://docs.python.org/3/library/sqlite3.html#transaction-control).
