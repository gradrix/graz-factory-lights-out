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
replay cannot request a model turn or append events.

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

## Original outcomes and post-review findings

Two of three original builds passed their frozen gates; the third exhausted CLI
repair, alternating incorrect help/error exit behavior. The first two also passed
the initial held-out audit. Manual source review then found missing gate coverage:
leading/trailing CR/LF was stripped before title validation, and JSON version 1.0
was accepted as integer 1. These violate the original brief, not a new requirement.
`edge_audit.py` passes the reference and fails all three accepted storage candidates.
Findings bind the exact storage candidates and both accepted combined candidates;
their reuse now blocks without rewriting historical acceptance or adding replay events.
There are **zero fully qualified original projects**. Initial exported first-project
bytes are retained under `challenged/`, not offered as a corrected delivery.

The first reporting harness incorrectly treated construction of a model client as
inference. The corrected replay client permits construction but raises on any model
turn; replay added no model calls or ledger events. This reporting correction did
not change a plan or candidate.

## Fresh corrective work

Two new repair jobs start from the unchanged complete challenged snapshots. Codex
supplied the observed failure description, limited writes to storage and tests,
and strengthened the independent checks with the exact missing edge cases and two
additional test mutants. The local model still plans and edits the repair. Other
project files must remain byte-identical. Each new job reserves 18 responses /
270,336 tokens; the original build histories are not reset. This is recorded
supervisory assistance, not unattended recovery or a new unbiased completion sample.

Both first repair planners exhausted their budgets before editing: the controller
incorrectly rejected valid private interface names beginning with `_`. The schema
fix permits those Python names while keeping general Work-atom identifiers unchanged.
Two exact retained plan responses validate without task edits; 533 tests/25 subtests
with Docker and four historical replays pass. The original 12 planning responses and
their costs are retained in `repair-results.json`.

Fresh v2 repairs use identical source, requests, policies, model and budgets after
the schema correction. Run with `repair.py --fixed-symbols` and report with
`report.py --fixed-symbols`. Both commands use `.gflo/evidence/small-project-repair-v2/`;
v1 remains separate. Only outputs passing all strengthened gates and post-acceptance
audit can become deliveries. No model source or tests are manually corrected.


The v2 first planner accepted private symbols but alternated uncovered requirements
and out-of-scope tasks, then hit tokenizer admission after five responses; the second
job never started. This was preparation error: full creation requirements were paired
with repair-only write scope. `repair-v2-planning-admission.json` retains the evidence.
No context limit was raised and neither history was reset.

V3 (`repair.py --scoped-requirements`, corresponding report flag) scopes requirements
to storage and tests, preserves the same source and full strengthened gates, model
and budgets. Trial 1 stops needs-info on incorrect Python equality/stripping beliefs.
Trial 2 completes storage, tests and integration; the independent held-out audit and
unchanged terminal replays pass. Costs: 3 responses/14,052 tokens and 9 responses/
48,385 tokens respectively. Exact model-produced files are in
`deliveries/repair-v3-trial-2/`. Source review confirms raw validation before stripping,
strict integer version checks, atomic replacement and unchanged CLI/packaging/docs.
It also notes an unused duplicate validator: passing behavior is not polished code.
The result demonstrates supervised small-project delivery, not unattended reliability.
