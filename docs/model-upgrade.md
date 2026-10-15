# Model upgrade: re-test GFLO on a new local model

GFLO is in **maintenance mode** ([decision 016](decisions/architecture/016-maintenance-mode.md)). It is used as it is, and no new components are built, until a stronger local model passes the gates below. This page is the to-do list for whoever picks it up then, human or AI. Read it top to bottom before changing anything.

## Where things stand (October 2026)

Model: Flash-Next GSQ-RCO Coder (pruned IQ1_M GGUF, llama.cpp b11284, 96K context, Q4 KV cache) on one RTX 5090 ([model profile](model-profile.md)).

| Job | Measured | Verdict |
|---|---|---|
| Small change (2–137 lines), precise objective | 14/16 delivered, 1 false accept; the 3 hard tasks 8/9 over three runs | Works; retries converge |
| Tests for a moderate module | 4/4 accepted | Works |
| Tests for a large module (overnight) | 1/3 per run, four runs | Runs out of turns or context |
| Feature spanning 2–3 commits | 2/6 delivered, 3 false accepts (queue: the same, 1.8× slower) | Does not work: accepted features are often wrong |
| Objective-derived checks as a safety net | caught 3/4 covered false accepts; 3/11 check sets wrong; 11/20 generated | Not a gate ([decision 015](decisions/architecture/015-objective-checks.md)) |

The limit is the model, not the harness. On features the model finishes, passes the tests, and is quietly wrong. Worker variants are already at their ceiling: the plain worker beat mini-swe-agent 8/9 to 4/9 on the hard tasks ([decision 013](decisions/architecture/013-worker-head-to-head.md)). Records: [roadmap](roadmap.md), `.scratch/autonomy/delivery.md`, run notes under `.scratch/.sflo/11-*`, `12-*` and `13-*`.

## The benchmark

The benchmark is private, so it lives only on the rig at `~/gflo-bench` (7 GB), frozen 2026-10-14. It holds tasks mined from the author's private repositories, their hidden tests, prepared environments and `manifest.json`. Never copy its contents into this public repository; commit only aggregate numbers. Keep the Python sandbox image (`docs/operations.md`, Sandbox image) on the rig, because the environments depend on it. Back the directory up before any rig rebuild.

| Suite | Content | Time on the current model |
|---|---|---|
| small | 16 single-commit tasks (11 running-coach, 5 gflo), default worker and reviewer | ~3–4 h |
| features | 6 commit chains (2–3 commits), one task each with the combined objective | ~2.5 h |
| tests | `gflo tests overnight` on the 3 largest untested running-coach modules, 4 h cap | ~1–4 h |

Results are scored by the hidden tests: `delivered` means accepted by GFLO and passing them; `false accept` means accepted but failing them. Gates and the baseline are in `ops/benchmark/gates.json`:

| Gate | Pass when | Opens |
|---|---|---|
| adopt | small: ≥14/16 delivered, ≤1 false accept | the new model becomes the default |
| features | features: ≥4/6 delivered, ≤1 false accept | feature development (below) |
| tests | tests: ≥2/3 accepted | test factory widened to large modules |

A gate is **borderline** when it misses by at most one on each count: at most one task short of the minimum and at most one false accept over the maximum, including both at once. Repeat that suite once into a new results directory before deciding. One run per task is noisy. In decision 013 the default worker delivered the 3 hard tasks 8 times in 9 runs, not 9 of 9. The current model's 1/3 on tests is itself borderline for that gate.

Incomplete means the suite did not finish: fewer tasks scored than planned, or a test-writing module still waiting to be retried. Rerun the same command. A module stopped because the model rejected its request (HTTP 400, for example context overflow) counts as finished and not accepted.

## Steps

1. **Check the slot is free.** `ssh monster-gaming-pc.lan 'pgrep -af "python3 -m gflo|drive.py|gate.py|chain-"'` should print nothing except possibly its own `zsh -c` line. `make rig-gate` runs the same check and refuses to start if the slot is busy.
2. **Install the model.** Put the GGUF under `~/benchmark-5090/flash/` on the rig. If its architecture is newer than llama.cpp b11284, also put a newer `llama-server` build under `~/benchmark-5090/flash/runtime/llama-bNNNN/`. Record the source and SHA256 in [model profile](model-profile.md).
3. **Serve it.** On the rig: `python3 ~/gflo-runtime/ops/model.py up --weights NEW-00001-of-0000N.gguf [--runtime runtime/llama-bNNNN/llama-server] [--context 131072]`. The service name stays `flash-next-coder`, so factory configs need no change. Check it with `python3 ~/gflo-runtime/ops/model.py status`. `python3 ~/gflo-runtime/ops/model.py up` with no options returns to the old model.
   - If the CUDA base image (`IMAGE` in `ops/model.py`) is too old for the new build, pin a newer image ID there.
   - If the model needs different server flags (chat template, reasoning), change them in `up()` and note them in the model profile.
   - `~/gflo-runtime` on the rig is a plain copy, not a git checkout. After any change to `ops/model.py` here, commit it, then copy it over: `scp ops/model.py monster-gaming-pc.lan:gflo-runtime/ops/model.py`. Otherwise the rig keeps serving with the old flags.
4. **Smoke test.** From this checkout: `make rig-gate LABEL=<model>-smoke ARGS=--smoke`. It runs one small task (about 10 minutes). Read `~/gflo-bench/runs/<model>-smoke/gate.log` on the rig; the task should be accepted and scored.
   - If the worker's tool calls fail to parse, or the model loops, fix that before the full run. The likely places are the chat template or reasoning setting in `ops/model.py`, and the tool-call handling in `gflo/worker.py`. A fix to `gflo/` must pass `make check`.
5. **Full gate.** `make rig-gate LABEL=<model>`, overnight, about 8–10 hours of awake time. The rig runs the factory in WSL2, so Windows sleep pauses the run (it resumes on wake, but a model request or review in flight can be affected); disable sleep on the rig first. A sleep shows as a long gap between events in the run's `state.sqlite`; check that any failed task did not straddle one. It runs committed `HEAD` only and refuses uncommitted changes, so commit any fix from step 4 first. Rerun the same command at the same commit to resume after an interruption. A label holds one model profile and one code revision; after a code change, use a new label. Results: `~/gflo-bench/runs/<model>/report.md` and `summary.json`. To rebuild them: `cd ~/gflo-gate-<rev> && python3 ops/benchmark/gate.py report ~/gflo-bench/runs/<model>` on the rig.
6. **Record the result.** Add a section to this page's history and the numbers to the roadmap and README. Update decision 016 with the gate verdicts and the decision taken. Commit only aggregate numbers.

## What each verdict opens

- **adopt fails:** keep the old model; record the numbers and stop.
- **adopt passes:** make the new model the default. Change `WEIGHTS` and `RUNTIME` in `ops/model.py`, update `docs/model-profile.md`, the README numbers and `ops/benchmark/gates.json` (the new baseline). A faster model on the same rate is still a gain; note the median times.
- **features passes:** end maintenance mode for feature work, in this order, with the same kind of measurement before building more:
  1. Re-measure the queued arm (`gflo queue run`; decision 014). Use `drive.py --arms queued` with the chain step objectives, as in `~/gflo-pp/chain-p4.sh` on the rig. The step objectives are in `~/gflo-bench/features/obj/`.
  2. Objective-check round 2 (decision 015): failing generated checks go back to the worker as repair feedback, then are listed for human review instead of rejecting.
  3. Model-planned decomposition (decision 008 failed on the old model).
  4. Phase 5, brief to small product (roadmap), only after features hold on a repeat.
  5. Self-improvement (the factory proposing and building changes to itself) only after all of the above. It needs a stronger checker than the hidden tests, because a wrong self-change damages the factory itself.
- **tests passes:** raise the overnight queue's default module size; re-measure on a fresh set of large modules.
- **Mined tasks look too easy** (everything passes): mine harder tasks with `ops/delivery/mine.py` from newer commits, and run an arm with objectives the user writes before seeing the solution. That measurement is still missing ([delivery](../.scratch/autonomy/delivery.md)).

## Rules that still apply

- One model slot: never run two factory jobs at once.
- Never run Python on the development host; use `make check` there. Python on the rig is fine.
- The repository is public; mined tasks, objectives, hidden tests and transcripts stay on the rig or under `.gflo/`.
- Never push, merge or deploy into the user's other repositories.
- At most two qualification rounds per component before end-to-end evidence decides.

## History

| Date | Model | small | features | tests | Decision |
|---|---|---|---|---|---|
| 2026-10-11/13 | Flash-Next GSQ-RCO Coder IQ1_M (baseline, mixed code revisions) | 14/16, 1 FA | 2/6, 3 FA | 1/3 | maintenance mode (016) |
| 2026-10-15 | Same model, full gate `flash-baseline` at c5e4576 (reference) | 14/16, 1 FA (median 650 s) | 2/6, 3 FA (median 905 s) | 1/3 | adopt pass, features fail, tests borderline; no repeat: same model, 1/3 in all four runs. Now the baseline in `gates.json` |
