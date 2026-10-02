# GFLO

A small local software factory: give it a repository, a task and executable acceptance checks. It edits an isolated copy, checks the result and repairs failures within a fixed budget. Your source repository stays unchanged. An accepted run produces a patch and its evidence.

**Works today:** bounded Python tasks using prepared dependencies, durable progress visibility and controlled recovery. [Incremental acceptance evidence](docs/evidence/autonomy-stages.md).

**Destination:** end-to-end autonomous local delivery, introduced through measured stages: visibility, independent review, environment preparation, research/browser tools, planning and integration. See the [roadmap](docs/roadmap.md) and [feasibility research](docs/research/autonomy-feasibility.md). Visibility and controlled recovery are implemented and qualified on the rig. Independent local review has passed the bounded qualification (12/12 fresh tasks, with documented quality limitations); three environment profiles are implemented and undergoing final qualification. Research/browser tools, decomposition and merging remain planned. See [environment preparation and offline use](docs/environments.md).

## Run on MONSTER-GAMING-PC

The prepared installation is `/home/gradrix/gflo-runtime`. The model and sandbox image are already on disk. Once installed, these commands need no Internet connection:

```sh
cd /home/gradrix/gflo-runtime
python3 -m gflo doctor
python3 examples/prepare.py .gflo/examples
python3 -m gflo run .gflo/examples/invoice/task.json
python3 -m gflo status
```

`prepare.py` creates new example repositories; it refuses to overwrite existing ones. Run the other examples with `inventory/task.json` and `log-summary/task.json`. Run one task at a time using the same state directory.

To use this checkout with the rig's model, see [local setup](docs/operations.md). Python 3.10+, Git and Docker are required. The runtime uses only Python's standard library; no agent subscription, hosted API or cloud fallback is involved.

## Bring a task

Commit the intended input in a clean Git repository. Create an acceptance directory outside the worker repository and a task JSON file:

```json
{
  "repo": "path/to/repository",
  "objective": "Describe the required behavior, compatibility and deliverables.",
  "acceptance": "acceptance",
  "checks": [["python", "-I", "/acceptance/check.py"]],
  "max_attempts": 3,
  "max_turns": 24
}
```

Paths are relative to the task file. Checks are argument lists, not shell expressions. They run in `/workspace` with the candidate and `/acceptance` mounted read-only. Use `/tmp` for test databases and other temporary output. New runs freeze a prepared environment receipt. The checkout can infer and validate an approved profile from manifests; use an existing receipt ID to run without registry access. See [supported profiles](docs/environments.md).

Acceptance checks are trusted operator code. Make them test observable requirements and fail on missing tests, not just print a success message. The [examples](examples/) demonstrate behavior checks and a separate quality check requiring discoverable tests, documentation and removal of scratch files.

```sh
python3 -m gflo run task.json
python3 -m gflo status RUN_ID
python3 -m gflo resume RUN_ID
```

An interrupted attempt consumes its attempt allowance; resume keeps its files and passes interruption evidence to the next attempt. A saved completed verdict can be reconciled without repeating the worker. Exhausted runs stop; revise the task deliberately and start a new run. Modified accepted artifacts are reported as invalidated.

Exit codes: `0` accepted/read-only command success, `2` not accepted (including exhausted or needs-input), `1` configuration/runtime failure, `130` interruption. Run ID and evidence directory print before execution; status works without the model.

## Inspect the result

`.gflo/runs/RUN_ID/` contains the frozen task, acceptance files, candidate workspace, per-attempt conversation and verification results, and `change.patch`. New CLI runs require the configured checks, discovered Python regression tests and a fresh local review to pass. Acceptance remains limited by the quality of those checks and review; inspect the qualification evidence before relying on unattended results.

Review the patch before applying it to the source repository at the recorded base commit:

```sh
git -C /path/to/repository apply --check /absolute/path/to/change.patch
git -C /path/to/repository apply /absolute/path/to/change.patch
```

GFLO never pushes, merges or deploys generated changes. Full prompts and tool output are retained locally in run artifacts; treat them with the same privacy as the source code.

## Develop and extend

```sh
make test
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
make coverage
```

The tests include real offline Docker execution, so the pinned image must be installed. Development coverage tooling needs a one-time installation; the factory runtime does not.

The task loop has three central responsibilities: [runner](gflo/runner.py) owns durable state and acceptance, [worker](gflo/worker.py) owns the model/tool conversation, and [sandbox](gflo/sandbox.py) executes commands and verification. [CLI](gflo/__main__.py) connects them. Environment preparation and immutable receipts are handled by [prepare](gflo/prepare.py) and [environment](gflo/environment.py); [review](gflo/review.py) owns fresh local assessment. Extend a supported profile through a concrete task and executable checks.

Read [architecture and limits](docs/architecture.md), [operations and rollback](docs/operations.md), and [pilot results](docs/pilot-results.md). The previous factory implementation and documentation have been removed. The new [roadmap](docs/roadmap.md) governs future work.
