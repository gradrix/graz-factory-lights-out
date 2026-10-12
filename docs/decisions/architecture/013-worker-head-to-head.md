# Worker head-to-head: keep the gflo worker, decide navigation aids on a repeat

Status: provisional, 2026-10-12, pending the hard-task repeat (below). Decision maker: the agent, under the user's delegation ("when it comes to other your recommendations and suggestions - sure, go ahead with it", 2026-10-11). Originating unit: `.scratch/.sflo/11-delivery-rate/run.md` (phase 2).

## Result

The 16 phase-1 tasks (running-coach 11, gflo 5), one run per task and arm, code 8123102, default single reviewer, the same local model:

| arm | config | delivered | false accepts | other losses | median s |
|---|---|---|---|---|---|
| frozen baseline (phase 1, 7cedc3c) | no aids | 14/16 | 1 | 1 exhausted | ~620 |
| mini | mini-swe-agent worker | 15/16 | 0 | 1 reviewer stop | 485 |
| nav | all aids: handoff, checkpoint 12, 60 turns, map, stale tests | **16/16** | 0 | 0 | 909 |
| notes | handoff only | 13/16 | 3 | 0 | 662 |
| plan | checkpoint 12, 60 turns | 13/16 | 2 | 1 context overflow | 649 |
| map | map tool only | 14/16 | 0 | 2 reviewer stops | 807 |

- Every arm delivered the same 13 tasks. All the differences come from three tasks: 06ba3e9, 3612b5f, 57271fe. Two of them are the phase-1 losses, and 57271fe's objective is ambiguous on the point its hidden test pins. So the table measures the three hard tasks, once each.
- 3 of the 80 runs (mini 06ba3e9, map 3612b5f, map 57271fe) stopped because the default reviewer cited a source location that does not exist. Since 8b33c5e the reviewer retries once with the rejection. These losses are reviewer infrastructure, not worker capability.
- The one context overflow (plan 89d66ea, turn 39 of 60, 98,886 tokens against 98,304) shows that a larger turn budget without the other aids can outgrow the 98K context.

## Choice (provisional)

1. **Keep the gflo worker as the default, and keep mini-swe-agent as the opt-in alternative.** mini matched the gflo worker: the kill criterion (about 30% delivered) is far exceeded either way, and nothing here shows the standard harness is ahead. gflo stays the controller in both cases.
2. **Do not ship any single aid.** Notes alone and plan alone each added false accepts on the hard tasks.
3. **The combined aids (nav) become the default only if the repeat confirms them.** That means at least 7 of nine hard-task runs delivered with no false accepts, against the no-aids arm under the same reviewer. If it doesn't, the default stays no aids. nav is about 1.5–2× slower per task.

## Repeat (queued 2026-10-12)

`~/gflo-pp/chain-hard.sh` on code 0002cbf, which includes the reviewer retry. Three tasks × three runs × three arms: single (no aids), nav, mini. It runs after the terse-objective arm. Results go to `~/gflo-pp/hard/rep*/results.jsonl` and the run note.

## Remaining assumptions

- One model and one rig; a second local model was not tested.
- Three hard tasks are a small sample. A difference of one task in nine is still noise.
