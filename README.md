# GFLO

GFLO is a software factory that runs entirely on your own machine. You give it a Git repository and a precisely described change; a local model makes the change in an offline Docker sandbox, the project's tests and a fresh model review check it, and you get a patch with its evidence. Your repository is never modified, and GFLO never pushes, merges or deploys. There is no cloud API, no subscription and no hosted fallback.

## What it does today

Measured on the author's rig: one RTX 5090 serving a pruned Flash-Next Coder GGUF through llama.cpp ([operations](docs/operations.md)). Failures are kept in the record.

| Job | How | Measured | Typical time |
|---|---|---|---|
| Fix a bug or make a bounded change in a Python project that has a pytest suite | `gflo task init` + `gflo run` | 14 of 16 tasks delivered: past commits of two of the author's projects (one is GFLO itself), redone from their parent commit and judged by the tests those commits added ([run note](.scratch/.sflo/11-delivery-rate/run.md)). 1 accepted patch was wrong | ~10 min, up to 42 |
| Write tests for existing modules | `gflo tests init`, or `gflo tests overnight` for a queue | 2 of 2 modules accepted on a real project; on one, the new tests caught 17 of the 18 code mutations the existing tests missed | ~12 min per module |
| Build a small program from a written spec, with your own acceptance checks | `gflo run` | 12 of 12 small single-module tasks ([evidence](docs/evidence/autonomy-stages.md)) | minutes |

These numbers come from changes of 2–137 source lines. Their objectives were written for the measurement from the original commits: they name the functions involved and the exact behaviour wanted. A rerun with objectives about half as long is in progress.

On the same 16 tasks, the gflo worker with all navigation aids on (`"navigation"` in the config) delivered 16 of 16. The standard mini-swe-agent harness (`"worker": "mini-swe-agent"`) delivered 15 of 16. Each was run once per task. Both arms delivered the same 13 tasks as the other variants, so the differences come from three hard tasks, and a repeat on those decides the default ([decision 013](docs/decisions/architecture/013-worker-head-to-head.md)).

**Not yet:**
- features that span several modules ([decision 008](docs/decisions/architecture/008-planning-pilot-outcome.md));
- vague requests;
- non-Python projects (TypeScript only in prepared fixtures);
- applying, merging or publishing its own patches.

Every accepted patch still needs your review.

## Change an existing Python project

```sh
# illustrative objective; describe your own change
python3 -m gflo task init path/to/repo --out .gflo/tasks/fix-1 \
  --objective "parse_duration() in app/time.py rejects '1h30m'; it should return 5400. Add regression tests."
python3 -m gflo run .gflo/tasks/fix-1/task.json --environment ENV_ID   # the exact command is printed by task init
```

`task init` prepares the project's dependencies once (from `pyproject.toml` / `requirements*.txt`; the only online step) and runs the project's suite on the clean base commit. It records which tests already fail or are skipped there. Acceptance then needs no hand-written checks: the full suite may gain no new failures, and a fresh model review must pass. The review blocks a patch that leaves out tests the objective asked for, so ask for regression tests in the objective. The suite must finish within about 12 minutes, the acceptance limit with room for the change; narrow it with markers if it is slower. Use `--pytest-args` (default `tests`) and `--env K=V` when the suite needs markers or environment variables, as in `--pytest-args "-m 'not db' tests" --env APP_TEST=1`. When the run is accepted, review `change.patch` and apply it yourself (see [Inspect the result](#inspect-the-result)).

A good objective is one a careful colleague could implement without asking questions. These rules come from what went wrong on real tasks:

- **Name the public function, class or module** that should change, and how it is called.
- **State exact outputs** wherever a test will compare them: strings, numbers, error types. "Return 5400" works; "handle hours" does not.
- **Spell out any term with two plausible readings.** One wrong delivery came from "index of the first step": the worker took a list position, the project meant the file format's own step numbering.
- **Say what must not change.** If behaviour changes on purpose, say which existing tests should change with it; the worker is reluctant to edit tests it did not write.
- **Leave out how to implement it** unless the approach matters.

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

## Bring your own acceptance checks

For new projects, non-pytest projects or stricter acceptance, write the checks yourself. Commit the intended input in a clean Git repository. Create an acceptance directory outside the worker repository and a task JSON file:

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
