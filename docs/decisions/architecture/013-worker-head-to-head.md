# Worker head-to-head: keep the gflo worker with no navigation aids by default

Status: accepted, 2026-10-12, after the hard-task repeat (below). Decision maker: the agent, under the user's delegation ("when it comes to other your recommendations and suggestions - sure, go ahead with it", 2026-10-11). Originating unit: `.scratch/.sflo/11-delivery-rate/run.md` (phase 2).

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

## Choice

1. **Keep the gflo worker as the default, and keep mini-swe-agent as the opt-in alternative.** mini matched the gflo worker: the kill criterion (about 30% delivered) is far exceeded either way, and nothing here shows the standard harness is ahead. gflo stays the controller in both cases.
2. **Do not ship any single aid.** Notes alone and plan alone each added false accepts on the hard tasks.
3. **The default stays no aids.** For the combined aids (nav) to become the default, they needed at least 7 of 9 hard-task runs delivered with no false accepts. The repeat gave nav 5 of 9 with 2 false accepts; no aids got 8 of 9 with none. The phase 2 result of 16/16 came from a single run that turned out to be noise. The aids stay available as opt-in config.

## Repeat (2026-10-12)

`~/gflo-pp/chain-hard.sh` on code 0002cbf, which includes the reviewer retry. Three hard tasks (06ba3e9, 3612b5f, 57271fe) × three runs × three arms:

| arm | delivered | false accepts | other losses |
|---|---|---|---|
| single (no aids, default) | **8/9** | 0 | 1 exhausted (3612b5f) |
| nav (all aids) | 5/9 | 2 | 2 interrupted: one context overflow at 60 turns (100,906 tokens against 98,304), one question assessment with no grounded decision |
| mini | 4/9 | 2 | 2 exhausted, 1 needs_input |

- The nav overflow repeats the phase 2 failure mode: a 60-turn budget outgrows the 98K context.
- 3612b5f is the hardest task: every arm lost it at least once.
- On these tasks a run takes 9–40 minutes in every arm.

## Remaining assumptions

- One model and one rig; a second local model was not tested.
- Three hard tasks are a small sample. A difference of one task in nine is still noise.
