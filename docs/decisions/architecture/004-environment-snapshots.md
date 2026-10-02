# Identify an environment by its base image and dependency snapshot

Status: accepted design, implementation pending stage2 acceptance
Decision maker: agent, under the user's incremental local-factory implementation direction
Date: 2026-10-02

## Decision

The first environment preparer will produce a receipt binding an immutable base image identity, a hashed dependency snapshot, complete locks, actual runtime versions and smoke evidence. Dependencies are mounted read-only at controller-selected paths. Python uses /opt/deps and PYTHONPATH; the initial Node/TypeScript profile uses /node_modules with an explicit compiler path. Models cannot provide mount paths or Docker arguments.

Fetch and offline assembly run in ordinary capped containers. The controller receives a size-bounded uncompressed archive, validates it before extraction, and publishes a complete receipt atomically only after checks. Initial profiles reject dependency symlinks and unsupported file types; npm's optional .bin links are omitted explicitly and known tools use direct paths. Missing package layouts fail rather than silently alter behavior.

## Why

This meets the requested container-environment capability with a smaller execution boundary than baking dependencies into custom images. Actual rig probes established CPU/memory/PID/tmpfs limits and owner-death cleanup for ordinary containers. The installed Buildx builder is privileged and automatically requests GPUs; shared-daemon image import cannot inherit a per-job cgroup limit. Neither is needed for the first three profiles.

## Consequences and evidence

The environment identity is the image **and** snapshot; an image digest alone is insufficient. Both must be pinned and checked. Environments remain portable as a base image plus validated dependency artifact and receipt, rather than a single baked image. Existing images can be reused and are recorded separately from cold package caches.

The [measured boundary research](../../research/environment-build-boundary.md) distinguishes proven container limits from unimplemented transport and package preparation. Actual Node resolution, non-root installation, archive validation, failure recovery and all three profile scenarios still need qualification. No Stage3 capability is claimed by this design decision.

This refines [the staged route](003-autonomy-route.md) and supersedes the custom-image assembly proposal in environment-preparation research for these initial profiles. Custom images remain a later separately qualified capability when a project requires them.
