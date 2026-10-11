# GFLO

A small local software factory: give it a repository, a task and executable acceptance checks. It edits an isolated copy, checks the result and repairs failures within a fixed budget. Your source repository stays unchanged. An accepted run produces a patch and its evidence.

**Works today:** bounded Python and TypeScript tasks using prepared dependencies, durable progress visibility and controlled recovery. [Incremental acceptance evidence](docs/evidence/autonomy-stages.md).

**Destination:** end-to-end autonomous local delivery, introduced through measured stages: visibility, independent review, environment preparation, research/browser tools, planning and integration. See the [roadmap](docs/roadmap.md) and [feasibility research](docs/research/autonomy-feasibility.md). Visibility and controlled recovery are implemented and qualified on the rig. Independent local review has passed the bounded qualification (12/12 fresh tasks, with documented quality limitations); three fixed environment profiles have passed bounded rig qualification, including an automatic repair. Approved-document fetch and cited local answers passed ten repeated and three fresh questions, with cross-version offline replay. Five supervised local-app browser journeys have passed rig qualification. Search, public browsing, decomposition and merging remain planned. Current priority: measuring end-to-end delivery on tasks from real repositories ([decision 011](docs/decisions/architecture/011-delivery-rate-route.md)). The model trials retain failed outcomes and do not qualify unattended large projects. See [environment preparation and offline use](docs/environments.md).

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

For an existing project with its own dependencies, set `"profile": "python-project"` ([decision 012](docs/decisions/architecture/012-project-resolved-python.md)) and, when its tests need flags or environment variables, `"test_command"` (an argument list such as `["env", "APP_TEST=1", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"]`); acceptance runs it in place of the default generated-test command and the worker is told about it.

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

`.gflo/runs/RUN_ID/` contains the frozen task, acceptance files, candidate workspace, per-attempt conversation and verification results, and `change.patch`. New CLI runs require the configured checks, discovered Python regression tests and a fresh local review to pass. Set `"review": "ensemble"` in the config to use the slower executable role-ensemble review for Python projects (roughly 17–31 minutes per review on one serving slot; on real repositories it often fails to reach a decision, so it is not recommended there; see [decision 010](docs/decisions/architecture/010-ensemble-review-integration.md)); the default is `"single"`. Acceptance remains limited by the quality of those checks and review; inspect the qualification evidence before relying on unattended results.

Review the patch before applying it to the source repository at the recorded base commit:

```sh
git -C /path/to/repository apply --check /absolute/path/to/change.patch
git -C /path/to/repository apply /absolute/path/to/change.patch
```

GFLO never pushes, merges or deploys generated changes. Full prompts and tool output are retained locally in run artifacts; treat them with the same privacy as the source code.

## Generate tests

`gflo tests init REPO TARGET... --out DIR` writes a test-writing task for tracked Python files. The worker adds test functions under `tests/`; acceptance is mechanical and controller-owned ([test_acceptance.py](gflo/recipes/test_acceptance.py)): every file outside `tests/`/`test/` stays unchanged and existing tests stay, new test functions need real assertions, must pass three runs in a row and on a behaviour-preserving reformatting of each target (so tests of source text fail), and must kill at least `--threshold` (default 60%) of the sampled mutants (flipped comparisons and operators, changed constants, dropped negations, returns replaced by `None`) that the existing related tests do not already kill. Equivalent mutants exist, so 100% is not expected. Only `test_*.py` modules (and data files) may be added or changed under the test directories, existing test functions stay, and tests that pin line numbers of the target fail the equivalent-rewrite check. Known limit: an existing test that reaches the target only through a helper module is not recognised as related, so copying it into a new module could earn credit; the patch review is the guard there. Use `--env K=V` when the project's tests need environment variables, then run the task as usual with `python3 -m gflo run DIR/task.json`.

`gflo tests overnight REPO --out DIR [--include PREFIX] [--limit N] [--hours 8] [--env K=V] [--environment ID]` queues one such task per module (only under `--include` prefixes when given, e.g. the package directory, to leave out scripts and harnesses), least directly tested first (test files anywhere, modules with fewer than five mutation sites, `setup.py`, `conftest.py`, `__init__.py` and `__main__.py` are skipped). Each runs as an ordinary `gflo run`, one at a time, under the global `--state` and `--config`. No new run starts after `--hours`. `DIR/queue.json` records each module's outcome; rerunning the same command continues the queue and retries modules whose run could not start or was interrupted. `DIR/report.md` is the morning report: result, time, number of new tests and mutation kill share per module, the mutants that still survive, and the patch path. Nothing is applied to the repository.

## Use approved documentation

The [document CLI](docs/document-evidence.md) fetches an explicitly approved official page, stores a historical snapshot and asks the local model for cited answers. New answers select bounded source spans; the controller supplies exact excerpts and retains any repair attempt. Saved answers replay offline. Initial acquisition needs Internet access; the model gets no browsing or tool authority.

## Check a local application

The [browser CLI](docs/local-browser.md) runs reviewed Playwright checks against a disposable Node application and saves screenshots, traces and cleanup evidence. Pinned support is prepared on the rig. It is a separate verification tool; the coding worker does not yet invoke it automatically. The prepared rig example is:

```sh
cd /home/gradrix/gflo-runtime
python3 -m gflo browser check .gflo/browser-example.json
```

## Develop and extend

```sh
make check        # container suite, no host Python
make rig-check    # full suite incl. Docker sandbox tests, on the rig
make test         # host Python, rig only
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
make coverage
```

The tests include real offline Docker execution, so the pinned image must be installed. Development coverage tooling needs a one-time installation; the factory runtime does not.

The task loop has three central responsibilities: [runner](gflo/runner.py) owns durable state and acceptance, [worker](gflo/worker.py) owns the model/tool conversation, and [sandbox](gflo/sandbox.py) executes commands and verification. [CLI](gflo/__main__.py) connects them. Environment preparation and immutable receipts are handled by [prepare](gflo/prepare.py) and [environment](gflo/environment.py); [review](gflo/review.py) owns fresh local assessment. Extend a supported profile through a concrete task and executable checks.

Read [architecture and limits](docs/architecture.md), [operations and rollback](docs/operations.md), and [pilot results](docs/pilot-results.md). The previous factory implementation and documentation have been removed. The new [roadmap](docs/roadmap.md) governs future work.
