# Per-requirement review units

Executor: markdown
Unit: .scratch/autonomy/delivery/09-executable-review.md
Contract: contract.md sha256 b795a7bd2ae763a3a2c2784b348b73280304507f799b27b690ce8398e15d0ff7
Predecessor: ../09-autonomy-review-evidence/run.md

## Execution

Status: active — trial dispatched
Owner: Claude Code coordinator
Candidate: prototype 377f0b5 (prototype/review-evidence-20261004, base 847f90e); module ops/review_units_prototype.py; predecessor c3673ba files unchanged; maintained 92deaab unchanged
Controls: 92 collected, 91 pass, 1 skipped predecessor local Docker vertical (python:3.12-slim, no network)
Driver: ops/rig_trial.sh 377f0b5 review_units_prototype.py <this dir> — stage, verify, admit once, monitor, download, verify, score
Next: semantic grounding assessment of trial output; closure.
