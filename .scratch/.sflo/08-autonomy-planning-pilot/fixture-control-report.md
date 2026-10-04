# Planning pilot fixture admission inputs

Two fixtures are frozen for independent admission review, not model qualification. No model calls occurred. Authoring is confined to the prototype worktree's `evaluations/planning-pilot`; no commit made.

- Fixture manifest: `9d6b6dc798d148524ef7e360abfc31958a47bb05b6870e56735a7ef64c283e5b` (25 bound public/source/protected acceptance files).
- Separate private reference manifest: `e3b47b296f6a9829d1e3d0a0e59e2a3dd0de50076d09e0b4f3c29acb93772b18`.
- Contract: `d52ae8c2f322f417fed6c8cf6ace5343720cc40f86f0d0aeb6b9294e2fc33bea`.

## Cases and scope

`manifest-reconcile` extends a seven-module stdlib JSON CLI with strict file manifest validation, path-first classification, unambiguous signature renames, totals and portable CLI handling. Milestone A1–A2 isolates validation/basic classification; full checks include ambiguous renames, sorting, shared-path precedence, API/CLI errors, tests and documentation.

`config-preview` extends a seven-module packaged FastAPI service with nested configuration set/remove/test operations, complete validation before application, strict JSON equality, atomic nonmutation, explicit copied audit events and HTTP conflict/status mapping. Milestone B1–B2 covers shape/domain/audit; full checks add conflicts, limits, installed-package HTTP, preserved endpoints, tests and documentation. Four implementation modules require meaningful work: validation, domain, audit and routes.

Public task objectives state every checked behavior and milestone boundary. Full requirements remain available to both children. Protected acceptance and private references are separate from source; the harness must never mount or prompt them to workers/planners. Failure output identifies public scope and exception class without protected source lines or expected values. The manifest's hash map is binding data, not model context.

## Novelty

Prior coding C/D, environment, telemetry, availability and browser stock tasks were inspected by domain. Neither file-manifest reconciliation with unique rename signatures nor nested configuration edit previews was previously used. Generic validation, CLI and HTTP mechanics recur deliberately as established interfaces. This is two fresh increments, not evidence of broad planning superiority.

## Measured offline controls

Final exact fixture bytes passed **16/16 expected outcomes** on the actual rig using approved Python 3.12.13 environment receipts, pinned image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, explicit runc, no pulls, network none, read-only source/oracle/dependencies, nonroot, capability drop, memory/PID/CPU limits and private tmpfs.

- Four starter milestone/full executions rejected missing implementations.
- Four reference milestone/full executions passed.
- Four semantic mutants rejected: accepting boolean file sizes, greedy ambiguous rename pairing, boolean/integer test equality, and input mutation.
- Four quality mutants rejected: removed generated tests and unchanged starter documentation, separately for each case.

API checks build the wheel offline and import the installed package from a private temporary site; a real loopback uvicorn server exercises HTTP. Both references provide three substantive tests. Counts and README length are only mechanical admission checks; subsequent independent semantic review remains necessary to assess generated tests and documentation. This oracle cannot prove arbitrary prose quality.

Environment dependency receipts were resolved before and after controls. All owned containers were removed and absence checked. Final local fixture hashes matched after execution. Earlier drafts' 16-control and API-only 8-control evidence remain separate and were not substituted for final results.

## Evidence / reproduction

`fixture-manifest.json` and `fixture-controls.json` contain compact identities, commands/outcomes and environment bindings. Complete reference sources, generators, control runner and per-container facts/logs remain under prototype `evaluations/planning-pilot/private`. Final rig staging is `/home/gradrix/gflo-planning-fixture-controls-v3`; raw results are `private/control-results`. Run the control runner only from a fresh disposable copy because it refuses an existing results directory. Earlier v1/v2 staging and copied results are retained.

No serving changes, network dependency downloads or model exposure. Freeze is ready for root's independent admission review; no accepted pilot result is claimed.
