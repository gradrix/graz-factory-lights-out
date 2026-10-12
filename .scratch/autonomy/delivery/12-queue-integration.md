# 12 — Queue and integration (phase 4, first unit)

Owner: Claude Code coordinator. Decision: [014](../../../docs/decisions/architecture/014-phase-4-start.md).

## Acceptance

- `ops/delivery` mines commit chains (2–4 consecutive commits, one feature, final commit adds tests that fail at the chain base) from running-coach and gflo; at least 6 chains.
- A controller-owned queue runs a chain's tasks in order on an integration branch in its own clone. Each step's base is the previous accepted state, and no step may add suite failures. The queue is resumable and never touches the source repository.
- Both arms (direct, queued) run once per chain on the rig. Chain delivery and false accepts go in the run note `.scratch/.sflo/12-queue-integration/run.md`.

## State

- 2026-10-12: queue built. `gflo/queue.py` (`gflo queue run`) has unit tests in `tests/test_queue.py`. Chain mining (`BASE..COMMIT` entries in `ops/delivery/mine.py`) and the `queued` arm in `ops/delivery/drive.py` are built, scored by `score_tree` on the integration branch.
- Refinement of decision 014's "full suite after every merge": each step is built from the branch head, so its acceptance suite run already covers the committed tree, and the queue does not run the suite a second time.
- Next: mine the candidate chains on the rig, write direct and per-step objectives, and run both arms after the overnight rerun.
