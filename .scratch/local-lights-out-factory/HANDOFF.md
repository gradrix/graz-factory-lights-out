# GFLO handoff — planning drafts and simpler setup

## Current checkpoint — 2026-09-09

Owner authorized merging and pushing all completed work. History filter `091654a`
was merged into main at `0d30d48` and pushed. No further merge/push permission is
needed for this authorized work. GitHub repository is already PUBLIC; no license
selected. Keep the experimental-preview wording; a supported release is not ready.

Added `gflo plan-feature` and `gflo check-plan`. The model proposes tasks,
dependencies, interfaces, acceptance descriptions, and unresolved questions from
an immutable FeatureRequest. Trusted validation checks structural coverage, scope,
source references, environment catalog, dependency cycles, and overlapping writes.
A valid draft does NOT authorize execution or create trusted acceptance gates.

One live compact-summary feature trial produced four tasks (renderer, CLI, tests,
docs) with matching proposed interfaces and no blocking questions after iterative
improvements. Earlier failures exposed deployment artifact omission, context
accumulation, truncation, and excessive routine questions. All results retained.
Planning v2: 12K/4K non-thinking, two attempts × three turns, two-file reading window,
bounded AST interface index. Implementation-worker budgets are unchanged.
No implicit resume; existing output directories refused. Raw immutable observations
remain even when a run halts; summary files can be incomplete after process death.

Added `python3 scripts/setup.py`: creates/reuses a venv, installs pinned dependencies,
prepares/submits a demo, reports CPU/Docker readiness. `--check-only` does not install.
`--start-model` uses existing service doctor/up and pulls the pinned broker image;
model cache and NVIDIA/Docker host prerequisites still need provisioning. Clean
venv setup and repeat setup passed; the default path runs no model/worker code.

Verification: 300 passed, eight optional Docker skips, 25 subtests; ruff and mypy
passed. The previous history self-trial passed 279 tests per generated candidate
in Docker; previous stateful campaign passed three builds. Original failed campaign
scores and findings remain unchanged. Huge-system capability remains unqualified.

## Continue

- Owner requires a migration path to large repositories. [ADR 0001](../../docs/adr/0001-repository-snapshots-and-bounded-task-inputs.md)
  and [issue 32](issues/32-separate-repository-access-from-task-bundles.md) define
  repository snapshots, bounded context, and separate execution inputs. Introduce
  source access with a real snapshot adapter before generalizing plan materialization;
  preserve old digests. No index/graph capability is implemented by this decision.

- [Issue 30](issues/30-diagnose-memory-qualification-halts.md): reproduce intermittent
  exit-137/no-OOM-flag resource checks without weakening enforcement.
- Materialize reviewed plans into WorkAtoms with independently reviewed ProcessGates,
  pinned environment/source bindings, and dependency-aware accepted-base progression.
  Do not execute arbitrary commands or treat model-written tests as sole acceptance.
- Qualify generated test tasks against trusted reference and faulty implementations,
  then broaden planning trials beyond this seen feature.
- GPU/model-cache provisioning remains the main onboarding gap. License selection
  remains an owner decision before a supported release.

[Planning results](planning-trial-results.json), [self-trial results](self-history-trial-results.json),
and [stateful results](stateful-inventory-feedback-results.json) are portable.
Raw planning evidence: `.gflo/evidence/planning-trial-v1/`, final `run-v2-defaults-1`.
Requests and deployment/profile files are retained there; source hashes/proposals
are in portable results. Raw artifacts/images require separate transfer/recreation.
The isolated history checkout remains at `.gflo/self-trial-checkout` for reference.
Keep `.scratch/` version-controlled. Issues 29 and 31 resolved; 30 ready-for-agent.
