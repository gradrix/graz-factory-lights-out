# Fresh held-out Node availability fixture

**Builder self-verification passes; independent QA required before exposure.** One new task computes free scheduling slots by subtracting the clipped union of busy intervals from a half-open window. This is distinct from the prior deployment-report aggregation task. No model call or runtime change occurred; prior failed outcomes remain frozen.

## Frozen identities

- Public: `.gflo/environment-node-followup-public`, manifest SHA-256 `68292397b94126e485d7d119f6c2e6a5692d9232ea366665c309e79eb18d84b5`.
- Protected: `.gflo/environment-node-followup`, manifest SHA-256 `2ec5da0ddb1c0e60996efa706360f397e3bc3433c45d05a70205ef48be4daf52`.
- Starter commit: `f5bd510e3d7da5a4d107e9c869a12d1983fe3aee`.
- Task budget: 3 attempts, 24 turns, 900 seconds.
- Unchanged approved package/lock SHA-256: `152e1b3aa7d2f0fca2ab5da0c1b443e0b811cd699a15a19ed807a41588fa85ee` / `2bd0d5d024a8f29b79d28b062d54d9e2a2f34737a67fd38d08ee0b031230b20f`.
- Pinned Node image: `88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0`.

## Evidence

| Check | Result |
|---|---|
| Starter missing feature | Rejected |
| Reference in two distinct paths, including spaces | Both pass |
| Missing overlap union, sorting, clipping | Three mutants rejected |
| Strict rather than inclusive minimum; coerced integer | Both rejected |
| Skipped validation outside window; input mutation; string duration | Three rejected |
| Ordinary error message containing ` at ` | Passes |
| Actual stack-frame error leak | Rejected |

Oracle checks strict compilation, exact dependency inputs, preserved total behavior, API and JSON CLI results, invalid-input exit/stderr behavior, no mutation, 1000 intervals, endpoints and filtering, and 80 deterministic cases against an independent occupancy algorithm. It requires three discovered passing tests and the explicit documentation word/action requirements. Meaningfulness of generated tests and prose/command correctness remain local-review responsibilities; token presence alone is not claimed to establish those qualities.

Run `python3 .gflo/environment-node-followup/private/validate.py` for reproduction. Full bounded offline runc commands and outcomes are in `private/validation.json`. Inputs/dependencies are read-only, network disabled, non-root, 2 CPUs/1 GiB memory, 600-second outer bound. Initial self-verification accidentally used a non-defective coercion mutant; its rejected expectation is retained in `validation-initial-invalid-mutant.json`. The final mutant genuinely coerces numeric strings and is rejected.

Only public source/objective may enter coding context. Protected acceptance, reference, mutant construction and validation remain outside coder/reviewer contexts. Independent reviewer `qa_resume` has received these frozen identities; no model exposure is authorized by this builder report alone.
