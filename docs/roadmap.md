# Toward a useful local factory

Status: accepted route, 2026-10-10 ([decision 011](decisions/architecture/011-delivery-rate-route.md)). Supersedes the six-stage plan of 2026-10-02, which is recoverable from git history (`git show 831c9ef:docs/roadmap.md`).

## Destination

A local factory that takes a repository and a well-specified task, works slowly and unattended on the RTX 5090, and hands back patches a person would merge. Tests with mechanically checkable value come first, because mutation score and coverage are objective acceptance a local model cannot talk its way past. Brief-to-product delivery is the long-term destination, attempted only when the measured numbers below earn it.

All inference stays local. No cloud fallback, no automatic push/merge/deploy of generated changes.

## What already exists

Durable runs, offline Docker sandbox, read-only operator acceptance, repair loop, resume, evidence, three fixed environment profiles, document evidence and local browser checks as separate CLIs, the single-request reviewer (default) and the role-ensemble reviewer (opt-in, decision 010). Evidence per capability: [autonomy stages](evidence/autonomy-stages.md).

Measured limits: small single-module tasks succeed (12/12 cohort D); multi-file increments did not complete (decision 008); ensemble review costs 17–31 minutes per ~95-line project, and on real repositories it delivered 7/16 against its own timeouts, context overflow and invalid outputs (decision 010 update: not promoted). The fixed profiles cannot run the user's real projects (pytest, pandas, SQLAlchemy, …).

## Phases

Each phase ends with a measured run on real repositories, merges to `main`, and records one run note. Thresholds are agent-proposed planning numbers.

### 1. Delivery rate on real tasks

- **General Python profile** (`python-project`): resolve the project's own `pyproject.toml`/`requirements*.txt` (plus a test runner) in a network-enabled preparation container, publish an immutable dependency snapshot with its resolved lock, and run the worker offline against it as today.
- **Task miner**: from a repository's history, take commits that change source and tests together; the base is the parent commit without the new tests; the hidden acceptance is the commit's tests that fail on the base and pass on the commit (fail-to-pass), plus the previously passing tests (pass-to-pass). Objectives are written as an operator would brief the task, naming the public interfaces the hidden tests use, never the tests.
- **Scoring harness**: run the factory, apply the hidden tests to its patch, record delivered / failed / stopped, wall time and failure category.
- **Accept**: 20 tasks from at least two of the user's repositories, default reviewer and ensemble reviewer arms. The resulting rate decides phase 2.

Result (2026-10-11, frozen 7cedc3c, default reviewer): **14/16 delivered (87.5%)**, 1 false accept (an objective ambiguous on the point its hidden test pins), 1 worker miss; 16 tasks from running-coach and gflo, short of the planned 20. Objectives were detailed operator briefs written from the reference commits, so the rate is for precisely specified bounded changes. The ensemble arm delivered 7/16 (decision 010 update). Run note: `.scratch/.sflo/11-delivery-rate/run.md`.

Follow-ups (user choice, 2026-10-11): (1) a terse-objective arm reruns the 16 tasks with objectives cut to about half their length, keeping only the public interfaces and exact outputs the hidden tests need, on the same frozen code, before phase 4 is decided. Result (2026-10-12): 13/16 delivered, 1 false accept (the same 57271fe), median 796 s; the extra loss is 3e6e4bd (exhausted). (2) The measured acceptance became a product command, `gflo task init` (the project suite gains no new failures over the base), and the README now leads with the measured use cases and objective-writing guidance.

### 2. Worker capability

Status: navigation aids (`navigation` config) and the mini-swe-agent worker (`worker: "mini-swe-agent"`) are implemented (2026-10-10). Result (2026-10-12, one run per task and arm, code 8123102): all aids together 16/16 delivered with 0 false accepts; mini-swe-agent 15/16, 0; map alone 14/16, 0; handoff notes alone 13/16, 3 false accepts; plan checkpoint alone 13/16, 2. Every arm delivered the same 13 tasks, so the arms differ on three hard tasks only, and three of the 80 runs were reviewer stops (fixed in 8b33c5e). Provisional choice ([decision 013](decisions/architecture/013-worker-head-to-head.md)): keep the gflo worker, keep mini-swe-agent opt-in, ship no single aid; a repeat (three hard tasks × three runs × no aids, all aids, mini) decides whether all aids become the default. Kill criterion not triggered.

Compare the gflo worker against a standard agent harness (mini-swe-agent first) on the phase-1 tasks with the same local model, and test repository navigation aids and a second local model. Navigation arms, cheapest first, each measured on the frozen phase-1 tasks: carry the worker's findings into the next attempt (today a repair attempt restarts from zero), a turn budget above 40 with a plan-before-editing checkpoint, and a generated repository map offered as a tool (modules, symbols, signatures, import graph). A module-scoped worker hierarchy stays in phase 4: decision 008 measured decomposition failing on multi-file increments, and the observed misses were cross-module. Keep gflo as the controller (sandbox, budgets, evidence, acceptance) whichever worker wins. **Kill criterion:** if no worker/model reaches about 30% delivered on real tasks, autonomous feature delivery is model-limited; narrow the product to phase 3 and human-reviewed patch proposals.

### 3. Test factory

Status: `gflo tests init` and its mutation-score acceptance are implemented (2026-10-10). First real-repository trials (running-coach, 2026-10-11): both accepted on the first attempt in about 12.5 minutes each. `performance_recovery_mode.py` got 21 new tests that kill 17 of the 18 mutants the existing tests miss. `plan_formatter.py` got 14 new tests, but its existing tests already kill 8 of 9 mutants, so its 1/1 is weak evidence. Merge-unchanged judgement (delegated by the user, made by the agent): 2/2 mergeable unchanged; one pins some odd current output. Patches stay on the rig (private repository); applying them is the user's step. gflo trials (2026-10-12): `document_references.py` got 25 tests in 1 attempt, 17.5 min, killing 3 of 4 surviving mutants (existing tests already killed 26); `web.py` got 12 tests in 2 attempts, 28 min, killing 25 of 25 (it had no direct tests). Neither was mergeable unchanged. The first copied the whole 1,219-character model prompt into an equality assertion, so any prompt edit, even fixing its "at most8 claims" typo, would break it. The second bound the real default port 8787, so it fails while an observer runs. Both are merged into `tests/` after a few-line edit. **Phase 3 score: 2 of 4 mergeable unchanged, 4 of 4 after a small edit.** All the defects are tests pinning incidental detail. A new acceptance check now rejects any new test string literal that shares a stretch of at least 200 characters with a string literal of the target: it flags the original document-references patch and passes the other three merged patches.

`gflo tests init <repo> <target>...`: the worker writes tests for existing code. Acceptance is mechanical: source outside the tests is untouched, new tests pass repeatedly and on an equivalent reformatting of the target, contain real assertions, share no stretch of 200 or more characters with the target's string literals, and kill a required share of the mutants the existing tests miss. Mutation score replaces a coverage gate; a static test-smell check replaces most model review. `gflo tests overnight` (2026-10-11, `gflo/overnight.py`) walks the modules, least directly tested first, and writes a morning report. First real run (running-coach, 2026-10-12): 0 of 3 modules, 8 of 9 attempts lost to tool calls cut off at the 4,096-token output cap. Repaired by retrying cut-off calls with a larger budget; a rerun on the same modules is queued. **Accept** on the share of generated test patches the user would merge unchanged.

### 4. Queue, decomposition and integration

Started 2026-10-12 ([decision 014](decisions/architecture/014-phase-4-start.md)): the gate (about 50%) is met, and the terse-objective arm delivered 13/16. First unit: mined commit chains, direct against queued with branch integration. Originally gated on phase 1/2 delivery of about 50%. Durable task queue with dependencies, integration onto a branch with a full suite after each merge, environment and browser tools offered to the worker. Decomposition is re-tested against direct execution on real multi-file tasks.

### 5. Brief to small product

The former stage 6: brief → requirements → plan → implementation/review → integration → product journey → local release, on three project classes, three runs each. Attempted only after phase 4 shows steady gains.

## Working rules

- One run note per phase under `.scratch/.sflo/<phase>/run.md`; failures stay recorded.
- `make check` (container suite) guards every commit; `make rig-check` runs the Docker-dependent suite on the rig before a phase merges.
- Independent review of product changes stays; qualification of a component stops after two rounds unless end-to-end evidence points back at it.
