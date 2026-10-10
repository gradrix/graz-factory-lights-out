# Project-resolved Python environments

Status: accepted, 2026-10-10. Decision maker: agent, under the user's direction to measure the factory on their own repositories (decision 011). Originating unit: `.scratch/autonomy/delivery/11-delivery-rate.md`.

## Choice

Add an explicit `python-project` profile beside the three fixed ones. It resolves the project's **own** declarations (`pyproject.toml` runtime and optional dependencies, root `requirements*.txt`, root `constraints*.txt` as pip constraints) plus pytest from PyPI, once, in a network-enabled preparation container. The installed tree, with the resolved lock `gflo-lock.json` (name, version, URL, archive hashes from pip's install report), becomes an immutable receipt like any other profile. The worker, acceptance and resume stay offline against that receipt; the manifests are frozen into the task and changes invalidate it. Generated tests run with `python -m pytest`.

The profile is never inferred: a task or `environment prepare` names it. The fixed profiles and their stricter boundary are unchanged.

## Boundary difference

- Versions are whatever PyPI resolves within the project's constraints at preparation time, not a pre-approved hash list. The receipt records what was resolved; reproducing it needs the same index state or the stored tree.
- Source distributions may build in the preparation container (real projects need this: `fitparse` has no wheel). So fetched package code can run there, **with ordinary bridge networking for the whole resolution**: it can reach the internet, the host, the LAN and the local model port. The container has no host mounts except read-only manifests, no Docker socket, credentials or GPU, a read-only root, no capabilities, and 8 GiB / 4 CPU / 512 PID / 6 GiB scratch limits. Installed package code runs in the offline worker sandbox regardless of profile.
- Smoke results reported from inside the container (for example the pytest version) can be spoofed by a package that ships `sitecustomize.py`; the executor facts the controller records from Docker cannot.
- Preparation briefly needs up to about three times the tree size on the store filesystem (archive, validation spool, extracted tree).
- Only named PyPI requirements are accepted; URLs, paths, editable installs, includes and any option (also mid-line, such as `--hash`) are refused before any network use. A `pyproject.toml` without a `[project]` table (Poetry, dependency groups) is refused unless `requirements*.txt` declares the dependencies. pytest is added unpinned unless a requirement names it; constraints choose its version.
- A run refuses a receipt whose recorded manifests differ from the commit's, and verification fails when a dependency manifest is changed or added after freezing. Project test commands get 900 s per check.
- Bounds: 3 GiB transport and extracted tree, 200,000 paths.

## Evidence

- Rig, real network: the bundled `iniconfig` project prepares, runs pytest offline in the sandbox, and a changed manifest fails verification (`tests/test_project_profile.py`).
- `home-lab/services/running-coach` (pandas, SQLAlchemy, FastAPI, discord.py, Playwright package, fitparse sdist): 72 packages, 433 MB, 13,661 paths, prepared in 1 min 51 s; its suite then ran offline in the factory sandbox with 3,131 tests passing. 55 failures/errors are fixtures that need its disposable PostgreSQL but are not marked `db`.

## Remaining assumptions

- Projects that need system packages (apt), services (PostgreSQL) or non-PyPI indexes are out of scope until a measured task needs them.
- Resolution is not reproducible bit-for-bit across time; the stored receipt is the reproducibility unit.
