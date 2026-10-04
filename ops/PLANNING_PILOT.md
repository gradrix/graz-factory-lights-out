# Disposable local planning experiment

This branch contains an experiment, not an installed factory feature. The maintained `gflo/` package is unchanged. Decisions, admission evidence and results belong to main's `.scratch/.sflo/08-autonomy-planning-pilot/` run. Do not merge these scripts into the runtime as a shortcut to product delivery.

## What it compares

Two independently authored projects run in this order: manifest reconciliation direct, manifest reconciliation with two ordered workers, configuration preview with two ordered workers, configuration preview direct. Every arm shares one pool of 48 requests and 1,800 seconds across planning, review and implementation. Each arm starts from the same frozen project source and prepared environment. Final verification and independent semantic review decide complete outcomes.

The scripts keep progress, raw request/response bodies, child factory records, plans, checks and failures in a new private output directory. `planning_pilot_prototype.py status OUTPUT` displays completed outcomes; each arm's `progress.jsonl` and `budget.json` show ongoing work. Existing output is never resumed or reset.

## Before inference

The coordinator must freeze source, fixture manifest, environment bindings, model identity and control/review evidence. Run the independent and builder controls under `ops/test_*planning*.py` and `ops/test_cancellation_probe.py`; these use controlled clients and must not invoke the model. The separate cancellation probe requires a hash-bound admission receipt and consumes it once. Its `--client` mode is internal to its supervisor, never an operator entry point.

Only after all admission gates pass may the coordinator stage the frozen candidate on the owned rig, perform the one-request cancellation experiment and start the four project arms. The maintained run holds the exact command, hashes and observed results. All real invocations share the trusted lease at `~/.local/state/gflo-planning-pilot/lease`. Do not run parallel inference clients during the experiment.

The pilot `run` command requires explicit fixture manifest and its SHA256, canonical environment bindings, private config path, expected serving identity, and new output path. Configuration and key contents are never copied into evidence. Project source alone enters worker mounts; acceptance and private reference code must not enter worker or planner prompts.

## Reading results

An accepted child is an intermediate fact. A complete arm additionally requires full checks, fresh review, intact candidates, remaining work time and confirmed cleanup. Unknown model state or executor cleanup stops admission. Never restart the model to erase a failed lifecycle result. Repeating a failed experiment requires a separately labelled decision and new evidence.

Two cases can reveal a useful mechanism or a failure. They do not establish large-project autonomy, a reliability rate or statistical superiority. Retain every failure when deciding the next smallest maintained change.
