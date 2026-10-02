# Environment candidate: independent slop check

Candidate: runtime `25f75c3275739cc7cc2a4fc5a4e16580b81511d1`; operating documentation `bfb8084`. Reviewed working files match those candidate paths (no runtime or environments-document diff). Contract: `contract.md` in this directory.

## Result

No material slop finding. The implementation has proportionate seams for archive validation, immutable receipts, preparation, process supervision and fixed recipes. These address explicit contract requirements. The three profiles share one preparation/publication path without introducing a plugin registry, resolver framework or speculative profile hierarchy. Worker and reviewer use the same compact runtime context. The 45-line operating guide gives the actual command flow, network boundary, supported profiles and incomplete qualification status without claiming acceptance.

Read-only inspection covered `gflo/artifacts.py`, `environment.py`, `prepare.py`, `guard.py`, recipe fetch/validation/assembly/smoke code, runner integration, sandbox integration, worker/reviewer context and `docs/environments.md`. No model calls, container execution or system changes were made. This is a maintainability/presentation assessment, not independent functional or security acceptance.

## Optional cleanup

- `gflo/sandbox.py:96`: the comment “The current profile is Python stdlib” predates the immediately following packaged-Python branch. Remove that sentence or say that Python regression tests supplement protected checks. Its cost is misleading a maintainer about already-supported behavior; it does not affect execution.
- `gflo/environment.py:249-250`: `resolve_binding()` resolves and hashes the full dependency tree, then `binding(environment)` immediately resolves and hashes it again to serialize the same facts. This is demonstrable duplicate filesystem work within one operation. If preparation/resume overhead becomes relevant, serialize the already-checked value through a small internal helper while preserving validation at public execution boundaries. No timing measurement establishes a material performance problem, so this is not an acceptance blocker and does not justify a new abstraction framework.

Keep historical failed trials and qualification evidence. No deletion, cosmetic test rewrite or documentation restructuring is required by this check. No maintained output was changed; only this requested report was written.
