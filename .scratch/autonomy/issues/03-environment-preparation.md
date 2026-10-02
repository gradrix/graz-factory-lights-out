# How should trusted templates prepare reproducible local task environments?

Type: Research
Status: resolved
Blocked by: none for research; implementation depends on stage 2 acceptance

Resolve concrete Python stdlib, packaged Python API and Node/TypeScript profiles, immutable image/dependency identities, separated network fetch/offline execution, cold-cache verification and bounded failure behavior. Capture the actual target interpreter/runtime as task evidence for workers and reviewers. Do not create a generic environment framework or expose Docker sockets/secrets to model-controlled containers.

Research output: [environment preparation](../../../docs/research/environment-preparation.md). Three fixed templates, complete dependency locks/artifact hashes, separated network fetch and offline execution, explicit target-runtime receipt. Package candidates were checked against official registries; no images built or capability qualified. Implementation must prove resource and cleanup bounds; cold package caches are distinct from preinstalled base-image inputs.
