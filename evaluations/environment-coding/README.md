# Environment coding qualification tasks

Three fresh bounded feature tasks for later Stage 3 model qualification: a Python stdlib expense ledger, an installable FastAPI reservation preview, and a CommonJS TypeScript deployment report. Each directory contains only an objective and starter project. Private references and independent acceptance checks remain outside the model/reviewer workspace in `.gflo/environment-coding-qualification`.

Budgets remain three attempts, 24 turns per attempt and 900 seconds per task. These tasks do not replace Stage 2 cohorts or establish Stage 3 acceptance. Run them only after the environment preparer and its independent security/lifecycle gates are accepted. No coding-model or GPU calls were made during preparation.

## Frozen runtime facts

- Python profiles: actual CPython 3.12.13, base image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, linux/amd64.
- Python API: FastAPI 0.115.12, Uvicorn 0.34.2, Pydantic 2.13.5, HTTPX 0.28.1; offline build backend setuptools 78.1.0. The complete approved dependency lock is in `locks/python-api.requirements.lock`.
- Node profile: Node 22.23.3, npm 10.9.9, TypeScript 5.8.3, @types/node 22.15.3 and undici-types 6.21.0; base image `sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0`, linux/amd64. The unchanged approved npm lock is part of the starter source.

Dependency snapshots are read-only environment inputs: Python `/opt/deps` through PYTHONPATH; Node `/node_modules` with the real TypeScript compiler entry point. These are controller-selected profile paths. Source, tests and documentation must support arbitrary project locations and working directories. Do not use a fixed workspace source path.

## Preparation evidence

Starters fail because their requested feature is absent. Reference implementations pass each protected oracle in two fresh offline local containers with different project mount locations. API checks build and install an actual wheel before real loopback HTTP checks. Node checks compile with strict TypeScript before API/CLI and node:test checks. Tests/docs are required by each task and protected checks.

These runs reused existing base images and previously prepared dependency trees; they prove fixture feasibility, not cold preparation, receipt integrity, cancellation, public-only fetch, target-GPU model reliability or Stage 3 completion. The private validation evidence records explicit runc, effective mounts/environment, resource limits, runtime versions and empty GPU-device observations. Independent review of the implementation and eventual model outputs remains required.

`manifest.json` and `MANIFEST.sha256` freeze all public task inputs before model exposure. The private manifest separately binds acceptance, references, clean starter commits, approved-lock identities and validation. Do not copy private files into target model contexts. Later corrections require a new version preserving original fixtures and evidence.
