# Architecture and limits

## One task through acceptance

The CLI snapshots a clean Git commit and operator-owned acceptance files. The runner records a task in SQLite, then invokes the worker. The worker gets a shell in an offline container, an acceptance-check request and a question tool for unresolved product choices. Fresh local assessment checks whether a question actually requires a person. Final executable verification and read-only local review run independently of the worker's completion message. Present Python unittest suites under tests/ run alongside the immutable external acceptance checks.

```text
pending → running → verification → accepted
              ↑           │
              └─ repair ──┘
                 │
              exhausted

process interruption → interrupted → resume within original budget
accepted artifact changed → invalidated
```

SQLite stores run/attempt states; files store complete requests, outputs, checks and patches. An OS file lock serializes runs in one state directory. Each new attempt receives the objective and previous failure evidence, with the retained workspace. There is no accumulated conversation across attempts and no hidden context condensation. Oversized model requests fail visibly.

The worker cannot mount the controller database, private Git index, credentials or acceptance files. Its shell container has no network, a read-only root filesystem, a writable candidate mount, a bounded temporary filesystem, resource limits and a non-root user. Verification uses a fresh container with both mounts read-only. The runner cleans leftover containers for its workspace before reconciling a resumed run.

Generated code still runs in the same kernel through Docker. This is practical isolation for local coding, not a hardened hostile multi-tenant service. Tests can be incomplete or deceptive; operator-owned black-box checks and patch review remain necessary. The system does not infer the adequacy of a test suite from an exit code.

## Bounds

- Default three attempts; permitted range one to ten.
- Default 24 model turns per attempt; permitted range one to 100.
- Five identical tool requests stop an attempt's model loop.
- Model request timeout up to 300 seconds; worker stops scheduling turns after 30 minutes. An already-started command can finish after that scheduling deadline.
- Shell commands: 60 seconds. Each acceptance command: 120 seconds.
- Container: 1 GiB RAM, two CPUs, 128 processes, 128 MiB `/tmp`; shell output retains its final 16 KiB.
- No dependency downloads during runs. Shell containers use `--network none`, images use `--pull never`, and inference is restricted to loopback, directly or through an explicit SSH tunnel.

The filesystem is not quota-managed. Keep task inputs and generated output bounded and monitor disk space. The state directory lock does not serialize unrelated state directories or other clients of the GPU. A Windows/WSL shutdown stops the rig; Docker restart policy resumes serving when Docker starts again, but does not boot Windows or WSL.

## Extension seams

`Factory(state, worker, verifier, cleanup)` owns task transitions. The worker callable receives `(workspace, task, previous_evidence, attempt_number)` and returns a report. The verifier receives `(workspace, task, acceptance_directory)` and returns a boolean verdict plus check evidence. Cleanup terminates retained execution before observing a resumed candidate.

These callables also enable deterministic fault injection in tests. Production uses one implementation of each. The implemented profiles cover Python stdlib, packaged Python APIs and CommonJS TypeScript. Each profile supplies pinned inputs, actual runtime context and offline checks; the three-profile paths have passed bounded rig qualification, with failed original trials retained in the evidence. Unsupported dependencies require a new approved recipe. Symlink-containing input repositories and Git submodules are rejected explicitly.

Automatic planning/delegation is a later stage. First accumulate real-task completion, repair, interruption and regression evidence. SFLO inspired explicit acceptance/repair stages; Gas City inspired work state that survives disposable sessions. Neither is a runtime dependency. The new [roadmap](roadmap.md) describes the staged autonomy work; the [feasibility research](research/autonomy-feasibility.md) supplies current primary sources.

## Execution observation

`observe.py` owns versioned SQLite events, per-run process identity/heartbeat and read-only projections. State transitions and their lifecycle events share a transaction. A heartbeat means the controller process is alive; last-action time separately describes progress. `web.py` serves the loopback read-only page and bounded artifact endpoints. `guard.py` is a disposable per-command supervisor that removes its exact Docker container on timeout or controller pipe EOF. Worker and sandbox callbacks emit operation metadata; they do not own acceptance.

`review.py` is a fresh, read-only assignment. It validates decision shape and source locations. The runner validates the same result independently before publication, combines it with executable verification, and binds both evidence files into the accepted receipt. `needs_input` is terminal for that frozen contract; it is not an implementation failure to retry blindly. Review capability qualification and model-profile selection are separate from controller correctness.

## Prepared environments

`prepare.py` separates trusted, hash-checked registry acquisition from offline assembly and smoke tests. `artifacts.py` validates complete bounded archives before extraction. `environment.py` publishes immutable receipts binding the base image, dependency tree, recipe, locks and runtime facts. New task contracts bind the receipt before inference; resume and each executor resolve it again. Changed receipts, dependency bytes or frozen project manifests cannot silently change an accepted task. Legacy tasks remain explicitly unbound.

Use an existing environment ID for registry-independent execution. Automatic preparation can fetch approved packages, so initial setup requires network access and preprovisioned base images. See [environment use and measured limits](environments.md).

## Approved documentation

`documents.py` owns bounded historical snapshots, checked citations and offline saved answers. Fixed fetch and inert extraction helpers run in separate restricted containers; only fetch has network access. Local inference receives source text as untrusted data with no tools. The controller approves the URL/question and validates citations; semantic entailment remains separately assessed. See [usage and limits](document-evidence.md). Search, browser journeys and automatic research delegation remain later units.
