# Cohort D fixture QA — PASS for future exposure gate

Frozen manifest SHA256: `da7a8d364c326a61bb8c22f0873188c0498d98213a676c23107c1d730a143d0b`. All 99 bound hashes verified before and after probes; 13 source repositories are clean and match manifest commits. Executed image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc` directly reports CPython **3.12.13**.

| Coverage | Evidence / result |
|---|---|
| Real-world contracts and finite expected values | Inspected all 12 task objectives/case expectations; no contradictory expectation identified |
| API, CLI, preserved behavior, errors, immutability | Shared harness checks strict recursive JSON type/value equality, retained action, error behavior and unchanged inputs; all 12 comparators match and reject nested bool/int swaps |
| SQLite atomicity/persistence | Fresh private databases for API and CLI; successful persisted state and full rollback checked for missing SKU and intermediate-negative quantities |
| Independent real-Docker reference controls | SQLite, webhook, invoice CSV, redaction all pass |
| Independent negative controls | Per-update SQLite commits, CLI-only per-update commits, CLI-only boolean→integer conversion, LF-only CSV records, redaction list aliasing, missing docs and failing tests all reject |
| Generated tests / docs | At least 3 passing default-discoverable cases and README length/action/CLI required; meaningfulness and full semantic documentation remain reviewer responsibilities |

No blocker found in this proportional audit. Existing preparer evidence supplies 60 baseline/reference/quality outcomes; four references and seven independent mutations were rerun here. Timing-safe HMAC use, resource closure, and universal correctness still require semantic inspection. D remains unused and conditional on a fixed coder profile and runtime candidate; this verdict does not qualify model performance or replace C outcomes.

Reproduce: `python3 .scratch/.sflo/03-autonomy-review/qa-cohort-d-probe.py` (exit 0). Complete executable probe, outputs and per-case failure details: `qa-cohort-d-probe.py`, `qa-cohort-d-probe.log`, `qa-cohort-d-probe.json`. Frozen fixtures and maintained product unchanged; no target-model/GPU calls.
