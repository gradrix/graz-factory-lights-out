# Prepare supported execution environments

Status: active
Blocked by: none; Stage2 accepted3bd8ae2
Owner: /root
Contract source: docs/roadmap.md stage 3; environment-preparation research.

Deliver one trusted preparer for pinned Python stdlib, packaged Python API and Node/TypeScript environments. Infer a supported profile from source manifests, freeze complete dependency locks, isolate network fetching from offline execution, and return a durable base-image/dependency-snapshot/runtime/check receipt. Arbitrary Dockerfiles, install scripts, host mounts and registry credentials are outside the initial profile boundary. Unsupported dependencies yield an actionable environment request.

Acceptance: each profile starts with empty package caches and no profile dependency snapshot, while explicitly recording shared base inputs; then its independent scenario passes in two fresh offline containers. Exercise invalid/missing/corrupt locks and artifacts, registry failure, cancellation/owner death and resource limits without affecting shared services. No worker receives Docker socket or host/model credentials. A failed revision cannot replace the previous accepted receipt. Provide actual target runtime context to local review and qualify real 5090 model work in each profile.

Research: docs/research/environment-preparation.md.
Preparatory fixtures: .gflo/environment-qualification; hash manifest and negative cases. Syntax/JSON/hash checks only; no environment qualification is claimed.
Candidate: none
Evidence: none

Next: implement the first complete preparation-to-offline-check path. Resource limits must constrain actual preparation work, including disk, not merely the Docker client. Preserve one active maintained-product mutation unit.

Architecture refinement: docs/decisions/architecture/004-environment-snapshots.md. Bounded ordinary containers plus read-only snapshots replace custom image builds for the initial profiles; base images remain immutable and the complete environment includes both identities.

Security constraints: docs/research/environment-security-boundary.md. Validate the whole bounded archive before extraction into fresh private staging; reject duplicate/path-prefix conflicts, sparse entries, links and special files. Bind receipt to tree, locks and base identity. Guardian/deadline coverage includes transport and publication; failed/cancelled attempts cannot publish. Fetch gets sanitized manifests only. Registry URL restrictions must not be described as an enforced network firewall. Select runc explicitly and inspect actual device visibility. Independent security qualification is required on the implemented candidate.

Independent artifact acceptance inputs are frozen in evaluations/environment-artifacts (manifest b99ebaff58e9b496db487e75fed82d36ac30c84c8fedf83c94f12bed7802efa6): two valid and25 rejecting small archives, plus13 receipt/publication scenarios. Header inventories and deterministic regeneration were checked without extraction. No implementation behavior or Stage3 acceptance is implied.

Execution run: .scratch/.sflo/04-autonomy-environments/run.md.
Model-task fixtures: public evaluations/environment-coding manifestc479e671e6a4bdc06f8b58cfcf8a5f520c50f2859387ec7894f97039f43ab374; protectedv2 .gflo/environment-coding-qualification-v2 manifest858384ee7ca74724efe1ee4247c69cc039d88e8b53b344ef42c5f6c6d6e9989b. Independent pre-exposure QA passed after correcting two false-pass oracle gaps; originalv1 preserved. No model exposure yet.
