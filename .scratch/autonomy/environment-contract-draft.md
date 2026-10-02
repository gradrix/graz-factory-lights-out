# Supported environments: proposed execution contract

Planning only. Freeze and bind a new execution run after Stage 2 acceptance; this draft grants no capability or acceptance.

## Behavior

Provide one trusted preparer for three approved profiles: Python stdlib, packaged Python API, and CommonJS Node/TypeScript. A constrained explicit request or validated repository manifests select a versioned approved recipe; unsupported dependencies return an actionable request. No arbitrary resolver, Dockerfile, lifecycle script, host mount or model-supplied Docker argument.

Preparation records exact base image/platform, actual runtime, complete lock and manifest hashes, recipe identity, acquired package hashes, immutable dependency-tree identity and offline smoke evidence. An environment ID resolves only within the controller-owned store. New task contracts freeze this identity before inference; run/resume verify it before any tool or check, irrespective of later config changes. Old tasks remain explicitly legacy-unbound without rewriting historical contracts.

Online acquisition executes only trusted code with sanitized approved artifact URLs and hashes. Enforce HTTPS exact registry allowlist, verified public IPv4 destination, original-host TLS verification, no redirects/proxies, byte/deadline caps and hash checks. This is a trusted-client boundary, not a network firewall. Never execute project or package code online. Offline assembly and execution have network=none and no fallback or pulls.

Preparation uses explicit runc, nonroot, no capabilities, no-new-privileges, read-only root, bounded memory/swap/CPU/PIDs and every writable scratch mount. Bound logs, transport, archive count/expanded size, host staging and total elapsed time. Supervise owner EOF, cancellation and cleanup through transport, smoke and publication. Cleanup failure prevents acceptance/reuse. No Docker socket, host/model credentials or GPU devices reach a worker/preparer.

Validate the complete uncompressed archive before extracting into fresh private staging. Reject traversal, absolute paths, links, special/sparse entries, unsupported extensions, duplicate normalized paths and file-ancestor conflicts. No overwrite or following destination links. Bind file names/content/modes and locks into the receipt, then publish atomically only after verification and cancellation fencing. A failed attempt cannot replace an existing good receipt.

Worker and reviewer receive compact actual runtime/profile context. Both worker commands and protected checks use the same frozen environment. Keep one application, existing lifecycle semantics and bounded evidence-bearing failures.

## Acceptance

- Each of the three profiles starts with empty package caches and no dependency snapshot, records reused base inputs, and passes its independent scenario twice in fresh offline containers with no pulls/downloads. These are cold package-cache trials, not completely cold hosts.
- Python API scenario builds and installs its wheel offline with locked build backend and checks real loopback HTTP responses. Node scenario compiles strict TypeScript, resolves Node types and runs valid/invalid cases. Stdlib scenario exercises CLI output/errors.
- Execute frozen malicious artifact corpus and receipt/publication plans from evaluations/environment-artifacts, including instrumented declared-size rejection before body reads and unchanged prior-good receipt.
- Exercise bad/missing/corrupt locks and artifacts, forbidden URLs, registry/DNS timeout, disk/memory/PID limits, cancellation across phases, owner SIGKILL, daemon cleanup failure, receipt/tree tampering and config change after task creation.
- Confirm credential/socket/GPU absence and actual runtime/resource/device facts from executors. Check Python 3.10 controller compatibility.
- On the actual RTX5090 run one frozen realistic task in each supported profile, requiring external executable checks and fresh local review. Preserve failed attempts and independent semantic evaluation.
- Independent QA and security checks bind their verdicts to the final candidate. Existing relevant lifecycle/acceptance tests remain passing. Documentation explains supported profiles, reproducible use, evidence and limits.

## Delivery sequence

Begin with strict artifact publication/resolution behavior, then one complete stdlib preparation-to-bound-task path. Extend that same lifecycle to approved Python/API and Node packages. Use behavior-first checks at public seams, then target qualification; avoid building a general framework before the first path works.

Sources: delivery/04-environments.md; environment-implementation-handoff.md; docs/decisions/architecture/004-environment-snapshots.md; docs/research/environment-security-boundary.md. New facts can refine this draft before freezing; acceptance must not be relaxed after observing qualification outcomes.
