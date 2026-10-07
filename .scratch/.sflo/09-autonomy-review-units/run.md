# Per-requirement review units

Executor: markdown
Unit: .scratch/autonomy/delivery/09-executable-review.md
Contract: contract.md sha256 b795a7bd2ae763a3a2c2784b348b73280304507f799b27b690ce8398e15d0ff7
Predecessor: ../09-autonomy-review-evidence/run.md

## Execution

Status: active — trial dispatched
Owner: Claude Code coordinator
Candidate: prototype 60aabe4 (repair of 377f0b5; prototype/review-evidence-20261004, base 847f90e); module ops/review_units_prototype.py; c3673ba predecessor files unchanged; maintained 92deaab unchanged
Controls: 93 collected, 92 pass, 1 skipped predecessor local Docker vertical (python:3.12-slim, no network)
Driver: ops/rig_trial.sh 60aabe4 review_units_prototype.py <this dir> — stage, verify, admit once, monitor, download, verify, score
Next: semantic grounding assessment of trial output; closure.

## Trial 1 — harness failure, preserved

377f0b5 dispatched once 2026-10-07T08:24Z. All four cases failed closed before inference: `run_unit` did not create the `units/` parent (FileNotFoundError). 0 requests, 0 commands; cleanup and idle confirmed. Offline tests had used pre-existing roots. Repair 60aabe4: create the parent, regression tests on the real nested layout, stop the batch after any controller crash, number trials in the driver. [Results](trial-1-trial-results.json), [score](trial-1-trial-score.json).
