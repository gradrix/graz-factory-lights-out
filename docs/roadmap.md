# Toward a useful local factory

Status: accepted route, 2026-10-10 ([decision 011](decisions/architecture/011-delivery-rate-route.md)). Supersedes the six-stage plan of 2026-10-02, which is recoverable from git history (`git show 831c9ef:docs/roadmap.md`).

## Destination

A local factory that takes a repository and a well-specified task, works slowly and unattended on the RTX 5090, and hands back patches a person would merge. Tests with mechanically checkable value come first, because mutation score and coverage are objective acceptance a local model cannot talk its way past. Brief-to-product delivery is the long-term destination, attempted only when the measured numbers below earn it.

All inference stays local. No cloud fallback, no automatic push/merge/deploy of generated changes.

## What already exists

Durable runs, offline Docker sandbox, read-only operator acceptance, repair loop, resume, evidence, three fixed environment profiles, document evidence and local browser checks as separate CLIs, the single-request reviewer (default) and the role-ensemble reviewer (opt-in, decision 010). Evidence per capability: [autonomy stages](evidence/autonomy-stages.md).

Measured limits: small single-module tasks succeed (12/12 cohort D); multi-file increments did not complete (decision 008); ensemble review costs 17–31 minutes per ~95-line project. The fixed profiles cannot run the user's real projects (pytest, pandas, SQLAlchemy, …).

## Phases

Each phase ends with a measured run on real repositories, merges to `main`, and records one run note. Thresholds are agent-proposed planning numbers.

### 1. Delivery rate on real tasks

- **General Python profile** (`python-project`): resolve the project's own `pyproject.toml`/`requirements*.txt` (plus a test runner) in a network-enabled preparation container, publish an immutable dependency snapshot with its resolved lock, and run the worker offline against it as today.
- **Task miner**: from a repository's history, take commits that change source and tests together; the base is the parent commit without the new tests; the hidden acceptance is the commit's tests that fail on the base and pass on the commit (fail-to-pass), plus the previously passing tests (pass-to-pass). Objectives are written as an operator would brief the task, naming the public interfaces the hidden tests use, never the tests.
- **Scoring harness**: run the factory, apply the hidden tests to its patch, record delivered / failed / stopped, wall time and failure category.
- **Accept**: 20 tasks from at least two of the user's repositories, default reviewer and ensemble reviewer arms. The resulting rate decides phase 2.

### 2. Worker capability

Compare the gflo worker against a standard agent harness (mini-swe-agent first) on the phase-1 tasks with the same local model, and test repository navigation aids and a second local model. Keep gflo as the controller (sandbox, budgets, evidence, acceptance) whichever worker wins. **Kill criterion:** if no worker/model reaches about 30% delivered on real tasks, autonomous feature delivery is model-limited; narrow the product to phase 3 and human-reviewed patch proposals.

### 3. Test factory

`gflo tests <repo> <target>`: the worker writes tests for existing code. Acceptance is mechanical: tests pass on the base, are not flaky across three runs, raise coverage, and kill a required share of mutants of the target. A static test-smell check replaces most model review. An overnight queue walks modules and produces a morning report. **Accept** on the share of generated test patches the user would merge unchanged.

### 4. Queue, decomposition and integration

Only when phase 1/2 delivery reaches about 50%. Durable task queue with dependencies, integration onto a branch with a full suite after each merge, environment and browser tools offered to the worker. Decomposition is re-tested against direct execution on real multi-file tasks.

### 5. Brief to small product

The former stage 6: brief → requirements → plan → implementation/review → integration → product journey → local release, on three project classes, three runs each. Attempted only after phase 4 shows steady gains.

## Working rules

- One run note per phase under `.scratch/.sflo/<phase>/run.md`; failures stay recorded.
- `make check` (container suite) guards every commit; `make rig-check` runs the Docker-dependent suite on the rig before a phase merges.
- Independent review of product changes stays; qualification of a component stops after two rounds unless end-to-end evidence points back at it.
