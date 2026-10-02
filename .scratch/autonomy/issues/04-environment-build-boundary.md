# Which bounded executor should prepare environment images?

Type: Prototype
Status: resolved
Owner: environment_research

Question: Can a small trusted preparation/build executor enforce memory, CPU, PID and disk limits, and stop on owner death, on the actual rig's overlay2/extfs storage without granting coding workers Docker access?

Stage3 implementation remains blocked on stage2 acceptance. Read-only research and disposable probes can resolve this prerequisite independently. Compare a resource-limited pinned BuildKit container with tmpfs-backed state against simpler trusted assembly. Measure actual executor limits, artifact bounds, export/load behavior and cleanup; limiting the Docker CLI alone is insufficient. Preserve shared images and daemon settings.

Decision: use immutable base images plus hashed read-only dependency snapshots; architecture004 records the boundary. Ordinary executor limits/EOF cleanup are proven; archive/package profile qualification remains delivery work. No custom image builder is required.

Evidence destination: docs/research/environment-build-boundary.md; private .gflo/environment-build-probe.
