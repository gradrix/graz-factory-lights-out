# Implementation foundation for the first GFLO experiment

Research snapshot: 2026-09-08. This is primary-source design evidence, not an
installation, compatibility test, sandbox audit, or RTX 5090 benchmark.

## Recommendation

Use a small typed Python orchestrator with standard-library `sqlite3`, validated
versioned records, immutable artifact files, a controlled container launcher,
and an explicit thin HTTP model client. Implement one real model-server backend
for the first experiment. Treat SGLang as the provisional backend candidate
below; admission still depends on the exact model and host passing the trial.

This is a GFLO design judgment: one process should own scheduling and durable
state transitions; workers should submit bounded results through GFLO-owned
interfaces. Keep model serving outside that process. Start without an agent
framework, separate message broker/task queue, graph database, ORM, or generic
multi-backend abstraction. Represent dependencies as relational edges and derive
readiness with queries. Add infrastructure only when measured limitations justify
its operational and recovery cost. SFLO and Gas City remain architectural
references, with no runtime or compatibility dependency.

## Transactions, durability, and recovery

Python exposes explicit `autocommit` control from 3.12; the current documented
default remains legacy transaction handling and is scheduled to change. Specify
the mode instead of inheriting that default. With `autocommit=False`, commit or
rollback opens another transaction; with `True`, those Python methods do nothing.
GFLO should choose one documented transaction convention and test it across
restart boundaries. Use parameter binding, runtime-validated records and SQL
constraints; Python annotations alone are not record validation. Keep a state
transition, associated event and lease update inside one short transaction.
Do not hold it across model requests or subprocess work.
[Python sqlite3 documentation](https://docs.python.org/3/library/sqlite3.html#transaction-control).

SQLite WAL permits overlapping readers and a writer, but only one writer at a
time, and requires processes on the same host rather than a network filesystem.
Use local storage and one orchestrator writer. Set and verify `journal_mode=WAL`
and `synchronous=FULL` on the writer: FULL synchronizes the WAL at commit;
NORMAL omits that synchronization and can sacrifice commits after power loss.
This is an operating-system/storage durability boundary, not proof against
arbitrary hardware failure. Keep reader transactions short, monitor WAL growth,
and handle busy/checkpoint outcomes explicitly: long readers can prevent
checkpoint progress. A checkpoint transfers WAL pages into the database; it is
not a backup. The WAL can contain committed state and must not be discarded or
separated from a copied database.
[SQLite WAL documentation](https://sqlite.org/wal.html).

Use `Connection.backup()` for an online database snapshot; Python documents its
operation while other clients access the database. Define a consistent artifact
manifest alongside that snapshot and test restore, because the database API
does not back up external files.
[Python backup API](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup).

## Execution boundary

Rootless Docker runs daemon and containers without host root privileges using
user namespaces; its setup requires subordinate UID/GID mappings and helper
programs. It is a candidate execution primitive, not a complete GFLO security
policy.
[Docker rootless mode](https://docs.docker.com/engine/security/rootless/).

Rootless CPU, memory and PID resource flags require cgroup v2 and systemd;
unsupported configurations ignore those flags. Even a systemd cgroup driver
requires checking which controllers are delegated. GFLO admission should verify
effective limits and fail closed when a required limit is unavailable.
[Docker rootless resource limits](https://docs.docker.com/engine/security/rootless/tips/#limiting-resources).

Keep daemon socket authority in the trusted launcher, outside worker containers.
Docker warns that daemon controllers can request powerful host mounts; a rootless
daemon reduces privilege but still controls resources accessible to its account.
GFLO should validate launch parameters and allowlisted mounts independently of
model output.
[Docker daemon attack surface](https://docs.docker.com/engine/security/#docker-daemon-attack-surface).

## Real-model boundary and remaining evidence

SGLang documents JSON-schema constrained output through its OpenAI-compatible
chat API and native HTTP `/generate` endpoint, including subsequent response
validation. A thin client can therefore request a versioned result schema,
capture timing and termination metadata, enforce deadlines and response limits,
and return a validated GFLO record.
[SGLang structured outputs](https://docs.sglang.io/docs/advanced_features/structured_outputs).

Design inference: schema validity does not establish correct code, accurate
claims, authorized actions, or satisfied acceptance criteria. Deterministic
verification and semantic checks remain separate gates. These API examples do
not establish that a particular Qwen checkpoint, quantization, context budget,
server build and CUDA stack fit or perform acceptably on one RTX 5090. The first
real-model experiment must record those exact versions and measure successful
loading, memory use, latency, structured-response failures and accepted work.
