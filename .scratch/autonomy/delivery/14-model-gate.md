# 14 — Model gate (maintenance mode)

Owner: Claude Code coordinator. Decision: [016](../../../docs/decisions/architecture/016-maintenance-mode.md). User request 2026-10-14: "prepare some tests and context todo (for new AI) ... change string somewhere to new model, run full test end to end. And if we see that some gates pass, proceed with further factory development".

## Acceptance

- The private benchmark is frozen in one rig directory (`~/gflo-bench`, manifest plus small, features and tests suites, environments), independent of the experiment directory `~/gflo-pp`.
- Serving another model needs no code edit: `ops/model.py up --weights ... [--runtime ...]`, with the same service name.
- One command (`make rig-gate LABEL=...`) snapshots the code to the rig, runs all three suites resumably, and writes `report.md` and `summary.json` with a verdict per gate (`ops/benchmark/gates.json`). Unit tests: `tests/test_gate.py`.
- `docs/model-upgrade.md` gives a fresh AI or person the state, the steps, and what each verdict opens.
- Proof: a smoke run and one full gate run on the current model complete through `make rig-gate`.

## State

- 2026-10-14: built at 4b0c5fd. Benchmark frozen (7.1 GB). The model restarted through the new `ops/model.py`, which `~/gflo-runtime/ops/model.py` now matches. Smoke run `flash-smoke`: task 0937b55 delivered, hidden tests pass, 820 s.
- 2026-10-14: QA round 1 (fresh reviewer, c5e4576): repair. Fixed: the tests suite counts only finished modules, one results label holds one model profile and code revision, `rig_gate.sh` refuses uncommitted changes, doc fixes (slot check, rig `model.py` copy, borderline wording, paths).
- 2026-10-14: full gate `flash-baseline` on the current model started (code c5e4576), as the end-to-end proof and a reference on current code.
- 2026-10-15: **accepted.** `flash-baseline` completed all three suites (report rebuilt with 8da79d7): small 14/16, 1 FA; features 2/6, 3 FA; tests 1/3 — identical to the recorded baseline, now replaced by this single-revision run in `gates.json`. Verdicts adopt pass, features fail, tests borderline; no repeat (same model, 1/3 in four runs). The rig's Windows sleep paused the run for 10 h inside 3612b5f's last review (seen as an event gap in `state.sqlite`); its patch failed the hidden tests anyway. Doc step 5 now says to disable sleep.
