# Importflow qualification

Owner selected a CSV inventory-import service and requested scalability and reuse.
The generated application separates streamed immutable payloads, bounded CSV
aggregation, durable generic jobs, handler execution and FastAPI serving. Three
original builds are frozen before inference using the same pinned local model and
established non-reasoning windows profile. Each reserves at most 54 responses and
860,160 tokens; total 2,580,480. Each task retains two attempts/three model turns and
16,384 total/6,144 output tokens. Model output is never manually repaired.

## Preparation and bounded scale

Codex authored the brief, interface requirements, independent gates and separate
reference implementations. References qualify gates only, never enter planner/worker
inputs, and are not a model delivery. A pinned Python image adds FastAPI 0.141.1,
uvicorn 0.52.4 and httpx 0.28.1; Dockerfile, complete dependency lock and admitted image
identity are in provision/. Workers retain offline 128 MiB/32 PID sandbox limits.

The functional default admits up to 64 MiB per upload, one million rows and one
thousand labels. Worker gates exercise 4 MiB blob streams, 2 MiB HTTP streams and
200,000 CSV records with bounded traced Python memory. Their small /tmp filesystem
precludes qualifying the full upload default there. Larger runtime payloads require
a separate recorded runtime harness; default limits are not measured throughput.
The job gate races eight submitters and eight claimers; the held-out gate uses four
worker processes over 100 jobs. Each job publishes its own result once; there is no
cross-import inventory side effect or implied global exactly-once processing.

SQLite WAL establishes a single-host baseline. Short transactions, immutable payload
identities and fenced leases support multiple worker processes; they do not establish
multi-host throughput. Shared storage/database adaptation and measured resource
budgets are required for that claim. The concrete Store interface keeps SQL private;
handler mappings demonstrate actual variation without a speculative backend layer.

## Preflight and reproduction

Initial preflight retained a false-negative documentation check: reference said
'one host', gate required 'single'. The corrected gate admits either phrase. All ten
corrected process cases, including reference mutation tests and held-out checks,
pass. Initial and corrected bound receipts are in preflight-initial.json and
preflight.json; raw artifacts remain in .gflo/evidence/importflow-preflight-v1 and v2.

```sh
docker build -t gflo-importflow-dev:trial .scratch/local-lights-out-factory/importflow/provision
.venv/bin/python .scratch/local-lights-out-factory/importflow/campaign.py --preflight
.venv/bin/python .scratch/local-lights-out-factory/importflow/campaign.py
.venv/bin/python .scratch/local-lights-out-factory/importflow/report.py
.venv/bin/python .scratch/local-lights-out-factory/importflow/wire_audit.py
```

Campaign/preflight refuse existing roots. Frozen fixture identities bind the admitted
image, source, checks, model and budgets. Export only exact accepted snapshots after
independent audit; preserve challenged/failing histories. Then qualify real HTTP,
larger payloads, fault recovery and a second built-in handler through new factory work.

## Completed results and current decision

No qualifying model-generated application exists. Whole-project planning: trial 1
exhausted 6 responses/51,885 tokens; trial 2 hit context admission after 4 responses/
36,338 tokens; trial 3 never started. Existing declaration rules explicitly require
function signatures, including qualified method names; rejected class syntax was a
model response error, not a reason to widen historical contracts.

Three operator-prepared builds froze one-file tasks with public callable declarations
and passed through normal policy compilation. All halted. Trial 1 accepted blobs.py
and jobs.py, then failed CSV empty-input handling (8 responses/30,275 tokens). Trial 2
failed job capacity/idempotency (7/31,696); trial 3 failed job behavior (7/28,042).
A fresh supervised continuation preserved those two passed modules, rechecked them
on the actually fixed SQLite image, and adopted an unchanged failed parser as its
explicitly unaccepted input. Empty-input clarification helped, but row diagnostics
and another CSV check failed; 6 responses/24,186 tokens. No model source was manually
corrected. Total retained generation: 38 responses/202,422 tokens across these runs.
All complete prepared/continuation wire audits and terminal replays pass. Original
interrupted planning stays interrupted; no attempt or build directory was reset.

### Correct SQLite admission

The first base links SQLite 3.46.1, affected by the upstream WAL-reset advisory.
The first fix used LD_LIBRARY_PATH; ordinary runtime launches link 3.51.3, but the
broker intentionally clears that variable before exec, restoring 3.46.1. Both
preparation histories remain. provision-sqlite-system/ uses the system loader;
sqlite-linkage.json proves 3.51.3 in broker commands and child processes with no
LD_LIBRARY_PATH. Eleven system-preflight cases pass. New generation/validation uses
this admitted image; old frozen trials are not reinterpreted.

The separate reference runtime audit on that image handled 67,108,793 upload bytes /
554,618 rows, duplicate/conflicting submissions, oversize rejection, and 500 jobs on
four workers. runtime-system-reference.json records measurements (0.159 s upload,
0.731 s processing; 500 small jobs in 0.198 s) and the exact 512 MiB/2 CPU/32 PID/
256 MiB tmpfs profile. These are reference, memory-backed workload measurements,
not generated-app results, persistent-disk throughput, multi-host scale or an SLA.

The reusable gflo.qualification.prepared_planner adapter records operator provenance
and preserves request binding/policy/replay. 527 CPU tests plus the nine live Docker
cases pass (536 unique tests/25 subtests); typing checks 35 source files. The owner
has been asked whether to finish the application directly and use it as a factory
qualification target, or retain local-model-only authorship and work on reliability.
Until that choice, the reference remains test infrastructure and no delivery is claimed.
