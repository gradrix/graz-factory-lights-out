# Complete small Python project qualification

The local model must plan and create Taskdock: a persistent task-list CLI with a
storage API, CLI, offline-installable package, documentation and generated tests.
The initial snapshot has only `BRIEF.md` and an unrelated archive sentinel. There
are no implementation stubs or manually supplied plan/candidate edits.

This is supervised preparation, not autonomous product discovery: Codex selected the
product, wrote the explicit brief/API/CLI semantics, supplied the trusted environment,
authored independent gates, and preflighted those gates against separate references.
The local model chooses the task graph and writes every delivered project file.
References and check scripts are never part of its repository source/context.

Three fresh builds are frozen before inference, each with up to five tasks, two
attempts and three turns per worker, 16,384 total / 6,144 output tokens per turn.
Planning retains its six-response 12,288-token ceiling. Maximum reservation is
36 responses / 565,248 tokens per build, 1,695,744 tokens overall. Requirements,
gates and model stay unchanged across builds. All failures and costs are retained.

Independent checks cover API semantics and corrupt-store preservation, injected
atomic-write failure, real CLI subprocess workflows, offline installation and an
installed entry script, documentation topics, and at least six generated pytest cases
that reject four behavior faults. A held-out 60-step state-sequence/completion-write
failure audit runs after acceptance. Accepted files preserve both original files;
replay cannot construct a model client or append events.

## Environment and preparation assistance

The pinned broker image already has Python, pytest, pip, setuptools and wheel. Runtime
dependencies are standard-library-only; this trial does not provision arbitrary
third-party dependencies. Initial preflight passed API and CLI checks but hit the
sandbox's noexec mount when directly launching the installed script. No model call
had run. The brief and check were revised before freezing builds to invoke the installed
entry script through Python outside the source tree. No sandbox restriction was relaxed.
This qualifies installed-entry behavior, not direct OS execution from writable storage.
The initial failure is summarized in `preflight-initial.json`; full process evidence
is retained in `.gflo/evidence/small-project-preflight-v1/`.

The corrected five gates and the held-out reference audit pass. `preflight.json`
binds the gate digests and outcomes. Campaign admission rejects a changed gate or
incomplete preflight. Raw corrected receipts live in `small-project-preflight-v2`.
`reference/` exists solely for gate preflight and is never a delivered model result.

## Reproduce

From the factory root, using the same pinned serving deployment and broker image:

```sh
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/small-project/campaign.py --preflight
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/small-project/campaign.py
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/small-project/report.py
```

Commands refuse existing campaign/preflight directories. Portable fixture files retain
the exact request and policy for each build. Raw requests, responses, process output
and ledgers remain under `.gflo/evidence/small-project-v1/`; `results.json` is the
portable outcome summary. Only results passing acceptance and the held-out audit are
exported under `deliveries/`, byte-for-byte from their accepted snapshots.
