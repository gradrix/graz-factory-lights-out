# Durable artifact bytes

`WorkLedger` owns an `ArtifactStore` alongside its database: `ledger.db.artifacts/` for `ledger.db`. Both directories belong to the trusted Control plane. Attempt workers must never have write access. This implementation targets local POSIX storage with hard links and file/directory `fsync`; network filesystems and host-power-loss behavior are not qualified.

Publish exact bytes before passing their digest to the ledger:

```python
candidate = ledger.artifacts.publish(b"candidate payload")
ledger.candidate(lease, candidate)
# Publish the trusted runner's evidence bytes before record_gate().
```

Publication writes a private staging file, flushes and synchronizes it, links it atomically under its SHA-256 identity without replacement, and synchronizes the directory. Repeated/concurrent identical publication verifies existing content. Corrupt existing objects raise an error; publication never silently repairs or replaces them. Objects are read-only regular files; reads reject symlinks, directories and FIFOs and verify their hashes. Parent directories remain a trusted boundary. The current byte API buffers one artifact in memory; streaming and size admission belong to the broker before untrusted output collection.

The ledger verifies dependency artifacts before submission, candidate bytes before recording the candidate, evidence bytes before recording a gate, and new retry evidence before claiming a retry. Acceptance rechecks dependency, candidate and gate-evidence bytes, including on an idempotent acceptance request. Filesystem work runs outside SQLite transactions. This relies on the controller-only append-only store: there is no supported concurrent deletion or repair. Validator execution, candidate schema conformance and authoritative source-tree preconditions still belong to the broker/gate runner.

Contract, input-manifest, upstream-contract, validator, output-schema and receipt digests remain identity bindings for external inputs or canonical SQLite records; they are not automatically treated as byte objects. `dependency_artifacts`, candidates, gate evidence and retry evidence are stored byte references. Later typed manifests must explicitly define and verify nested references; publishing arbitrary manifest bytes does not verify their transitive contents.

Run `gflo --db PATH audit-artifacts` to report `missing`, `corrupt`, `unreferenced` and `staging` entries. This command is diagnostic and returns a report without modifying history or content. It includes references from all attempts, including failed and superseded ones. Objects published before a failed ledger commit appear as unreferenced; a retry can safely reuse them. Interrupted publication can leave a staging file. Audits during active writes are snapshots, so an unreferenced object is not proof of abandonment.

There is no garbage collection. Audit preserves all staging files and unreferenced objects as well as live/accepted references. Losing previously accepted bytes raises an integrity error on subsequent acceptance checks and is reported by audit; it does not rewrite historical acceptance into success or failure. Stop downstream consumption until missing/corrupt evidence is resolved. `resume` still only reconciles expired leases; worker dispatch and automated artifact fault handling are pending.

Tests cover duplicate concurrent writes, process termination before/after atomic publication, process termination between publication and ledger commit, reopen recovery, missing/corrupt content, nonregular objects, dependency admission, rejected absent evidence, failed-attempt retention and accepted-content loss. Process-crash tests do not simulate sudden storage power loss or backup/restore.

Publication failures preserve the primary write/link/fsync exception. If staging
cleanup also fails, its error is attached as an exception note instead of replacing
the original cause. A cleanup failure after otherwise successful publication still
raises: the caller receives no successful publication receipt. A linked object may
remain after a directory-sync error; reconciliation retains it and retry verifies
and syncs it again. Its presence alone cannot establish task acceptance.
