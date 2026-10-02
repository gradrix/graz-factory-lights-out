# Prepare supported execution environments

Status: pending
Blocked by: independent local review acceptance
Owner: unclaimed
Contract source: docs/roadmap.md stage 3; environment-preparation research.

Deliver one trusted preparer for pinned Python stdlib, packaged Python API and Node/TypeScript environments. Infer a supported profile from source manifests, freeze complete dependency locks, isolate network fetching from offline execution, and return a durable image/runtime/check receipt. Arbitrary Dockerfiles, install scripts, host mounts and registry credentials are outside the initial profile boundary. Unsupported dependencies yield an actionable environment request.

Acceptance: each profile starts with empty package caches and no profile image, while explicitly recording shared base inputs; then its independent scenario passes in two fresh offline containers. Exercise invalid/missing/corrupt locks and artifacts, registry failure, cancellation/owner death and resource limits without affecting shared services. No worker receives Docker socket or host/model credentials. A failed revision cannot replace the previous accepted receipt. Provide actual target runtime context to local review and qualify real 5090 model work in each profile.

Research: docs/research/environment-preparation.md.
Preparatory fixtures: .gflo/environment-qualification; hash manifest and negative cases. Syntax/JSON/hash checks only; no environment qualification is claimed.
Candidate: none
Evidence: none

Next: after stage 2 accepts, freeze an execution contract and implement the first complete preparation-to-offline-check path. Resource limits must constrain actual preparation work, including disk, not merely the Docker client. Preserve one active maintained-product mutation unit.
