# Supported environments: acceptance

Accepted 2026-10-02 for the bounded three-profile capability. Runtime source is `25f75c3`; it is byte-unchanged under `gflo/` at `8fdde15`. Serving manager/default is `8fdde15` (96K/Q4). Contract SHA256: `2f0f083ced4a23de3f97ad58f1ab970764041e65f39d63855f820878a1660ebb`.

## Evidence

- Three cold package-cache preparations and six fresh offline smoke checks on the rig: `rig-preparation-25f75c3.json`. Base images were reused.
- Independent artifact, publication, transport, profile, cleanup, phase-interruption and invalid-input checks: reports in this execution directory. Integrated security verdict: `security-environments-final.md`; scope and untested hostile-host/daemon scenarios remain explicit there.
- Maintained regression gate: 88 tests passed in 97.040 seconds; aggregate branch-aware coverage met 85%. `coverage-25f75c3.txt`.
- Stdlib task `d535632d4d5f`: accepted first attempt in 482.71 seconds at the original 128K setting; independent semantic QA passed.
- Fresh API task `0ff5575a451b`: accepted first attempt in 285.71 seconds at 96K/Q4; protected checks, local review, external rerun and independent semantic QA passed. Independent checks include 100 domain cases, 15 HTTP cases, generated tests and documented commands.
- Fresh TypeScript task `df7b986b2ae8`: accepted after one automatic repair in 178.41 seconds at 96K/Q4; protected checks, local review, external rerun and independent semantic QA passed. Independent checks include 150 interval cases, CLI behavior, immutable inputs, tests and documented commands.
- Serving comparison and limits: `qa-serving-profile.md`. Equal-input warm decoding rose from 16.52 tokens/s at 128K to 73.95 at 96K/Q4. Three-position retrieval over 81,441 input tokens passed; this is not full-window coding qualification.

## Failed evidence stays failed

The original frozen cohort remains **1/3 accepted**, with API and Node both interrupted at 900.03 seconds. Diagnosis found working feature code, genuine documentation defects and two oracle defects. Corrected fixtures were versioned and independently checked before exposing distinct fresh tasks. Neither original task was hand-repaired, rescored or relabeled as a fresh success. Follow-up results establish the remaining profile paths; they do not change the original cohort score or imply a measured universal success rate.

## Practical limits

These profiles use fixed approved dependency sets and preprovisioned pinned images. Automatic preparation may fetch approved packages; explicit existing receipt IDs support offline work. Containers share the host kernel. Model quality outside these bounded tasks, full-context coding, concurrency, cold host boot, arbitrary dependencies, planning/integration and end-to-end autonomy remain unqualified. Stage 4 research/browser work is separate and has not been accepted.

The authoritative unit is `.scratch/autonomy/delivery/04-environments.md`; execution history is `run.md`.
