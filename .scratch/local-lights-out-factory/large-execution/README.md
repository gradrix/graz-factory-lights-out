# Real larger-build admission

Pinned factory commit `3085d463a3a66563f813be4bb1d34647813edc78`, containing 34 runtime
files (381,820 bytes), 30 test files (326,381 bytes), plus pyproject.toml: 65 files,
708,963 source bytes. The script reads exact committed blobs, publishes a snapshot
manifest and checks both SourceBundle construction and repository execution selection.

All three workloads (runtime, tests, full Python build) exceed the existing 256 KiB
canonical SourceBundle limit and are rejected. The file-count limit is not the cause.
Snapshot identity and bounded selection of gflo/artifacts.py succeed. No large build
was executed, no execution gate passed, and no limits were changed. The independent
host/Docker suite checks from the previous checkpoint are not execution-adapter proof.

This confirms a concrete blocker to general larger systems: repository capture and
navigation are ahead of isolated execution capacity. ADR 0001 requires a separately
versioned execution-input/materialization path, preserving legacy bundle identities
and bounded worker context. Raising the old bundle limit would contradict that design.

Run from the factory root:

```sh
.venv/bin/python .scratch/local-lights-out-factory/large-execution/probe.py
```

The script refuses an existing `.gflo/evidence/large-execution-v1/`; raw snapshot
objects live there. `results.json` carries portable counts, commit and snapshot
identity, and exact admission outcomes. The next qualification should bind the first
intended larger workload, its dependencies and its real build/test commands. The
owner has been asked which larger system/repository/stack to target.
