# GFLO

Local software factory: task + repo + acceptance checks → sandboxed local-model worker → reviewed patch. Overview: `README.md`; design: `docs/architecture.md`.

## Where things are

- Route and phase gates: `docs/roadmap.md`; current frontier: `.scratch/autonomy/delivery.md`; decisions index: `.scratch/autonomy/map.md`, records in `docs/decisions/`.
- Core loop: `gflo/runner.py` (state, acceptance), `gflo/worker.py` (model/tool loop; opt-in navigation aids, map tool `gflo/recipes/repo_map.py`), `gflo/sandbox.py` (Docker execution), `gflo/__main__.py` (CLI). Reviewers: `gflo/review.py` (default), `gflo/ensemble.py` (opt-in). Test factory: `gflo/testfactory.py` + `gflo/recipes/test_acceptance.py`. Environments: `gflo/prepare.py`, `gflo/environment.py`, recipes in `gflo/recipes/` (`python-project/resolve.py` resolves real repositories).
- Rig operations, model serving, rollback: `docs/operations.md`, `ops/`. Delivery-rate tooling: `ops/delivery/`.

## Checks

- Never run Python on this host. `make check` runs the suite in a `python:3.12` container; Docker-executing tests skip there (`tests/docker_support.py`).
- `make rig-check` runs the full suite on `monster-gaming-pc.lan` from a `git archive` snapshot. Two `test_browser` seed-reader subtests fail there by known issue 10.
- Pre-commit hook: `git config core.hooksPath .githooks` (runs `make check` when Python files change).

## Working rules

- The model runs on the rig (`gflo-model` container, one slot). Before launching rig work, check nothing else is using it (`ssh monster-gaming-pc.lan 'ps -eo pid,etime,cmd | grep -E "gflo|ensemble"'`).
- Experiments get one run note per phase (`.scratch/.sflo/<unit>/run.md`), with failures kept. Don't create per-trial admission/hash/score file sets.
- This repository is public on GitHub; the user's other repositories (home-lab, dendrite, ...) are private. Mined tasks, objectives, hidden tests and run transcripts from them stay under `.gflo/` (ignored) or on the rig; commit only aggregate results.
- Never push, merge or deploy generated changes into the user's other repositories.
