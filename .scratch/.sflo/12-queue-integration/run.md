# Phase 4, unit 12: queued vs direct delivery on mined commit chains

Decision [014](../../../docs/decisions/architecture/014-phase-4-start.md); unit `.scratch/autonomy/delivery/12-queue-integration.md`. Code 60d6e0d on the rig (`~/gflo-p4`); private chain data, objectives and transcripts stay under `~/gflo-pp/p4/`.

## Chains (mined 2026-10-12)

Ten candidate chains of 2–4 consecutive commits (running-coach 6, gflo 4). Validity is judged as in phase 1: at least one hidden test of the chain fails at the chain base and passes at its final commit, and no manifest changes.

| Chain (base..final) | Repo | Commits | F2P | Used | Why not |
|---|---|---|---|---|---|
| cb1fc65..e7d7f18 (recovery modality, labels) | running-coach | 2 | 132 | yes | |
| e7d7f18..e596ceb (FIT prescriptions, mixed scope) | running-coach | 2 | 14 | no | second commit bundles about eight unrelated behaviours; no operator-style objective (phase 1 selection rule) |
| 04e5179..8331398 (continuous lap labels) | running-coach | 2 | 4 | yes | |
| 8ea88b9..dcd2e78 (paused laps, title forms) | running-coach | 3 | 23 | yes | |
| 2236887..cde2e00 (headline count, VO₂ titles) | running-coach | 2 | 2 | yes | |
| e5f9ddc..0937b55 (Garmin delivery) | running-coach | 4 | 108 | no | changes dependency manifests |
| 87bab04..e666533 (task init) | gflo | 3 | 0 | no | its tests need git, absent in the sandbox image |
| e4ff619..8591076 (overnight queue) | gflo | 4 | 0 | no | same |
| d16015b..80400b0 (python-project profile) | gflo | 3 | 10 | yes | |
| 54cb497..44ae332 (uv.lock pins) | gflo | 2 | 3 | yes | |

Six chains, 14 steps. Objectives:
- Step objectives reuse the phase 1 objective where a step was a phase 1 task (06ba3e9, f20a4e2, 366e6ca, dcd2e78, 3e6e4bd, cde2e00); the rest are new, written to the same rules.
- The direct objective is either one merged brief written for the chain (A, J, K) or the step objectives as an ordered list, "later changes win" (C, D, G).

## Arms

- direct: `single` arm, one task with the direct objective, scored by the final commit's hidden tests.
- queued: `gflo queue run`, one step per commit, then the integration branch is scored by the same hidden tests. A step that ends without acceptance stops the chain.

Queued after the overnight rerun (`~/gflo-pp/chain-p4.sh`, results `~/gflo-pp/p4/results.jsonl`).

## Results (2026-10-13, code 60d6e0d, `~/gflo-pp/p4/results.jsonl`)

One run per chain and arm. Hidden tests are the final commit's; F2P / P2P counts are failures.

| chain | direct | queued (steps committed) |
|---|---|---|
| e7d7f18 (rc, 2) | false accept: F2P 13/132, P2P 6 | false accept (2/2): a hidden test module fails to import at collection, so the whole suite is scored failed |
| 8331398 (rc, 2) | false accept: F2P 2/4 | false accept (2/2): F2P 3/4 (the same warmup-laps effort test) |
| dcd2e78 (rc, 3) | **delivered** | **delivered** (3/3) |
| cde2e00 (rc, 2) | exhausted (F2P 1/2) | exhausted at step 1 (0/2) |
| 80400b0 (gflo, 3) | **delivered** | false accept (3/3): F2P 3/10, resolver parsing |
| 44ae332 (gflo, 2) | false accept: F2P 1/3, uv.lock interpreter version | **delivered** (2/2) |
| **total** | **2/6 delivered, 3 false accepts, 9,113 s** | **2/6 delivered, 3 false accepts, 16,021 s** |

- The queue machinery worked: 13 steps ran, every accepted step was integrated and committed, and the stop on the
  exhausted first step of cde2e00 behaved as designed. There were no wiring failures.
- The arms tie. Decision 014's bar ("at least as many chains, no more false accepts") is met only as a tie. The two
  arms traded the gflo chains (80400b0, 44ae332), which is the noise level seen in decision 013, and queued took 1.8×
  the time. The queue earns no default role; it stays experimental and opt-in.
- The finding that matters: **6 of 10 accepted chains were wrong.** On single mined commits (phase 1) it was 1 of 15.
  Feature-sized work passes "no new failures" plus the worker's own tests far more often than it meets the
  reference behaviour. Splitting the work into steps did not help, because each step's acceptance has the same blind spot.
- Phase 1 delivery was 14/16 on single commits; on 2–3 commit features it is 2/6 in either arm.

Decision: [014](../../../docs/decisions/architecture/014-phase-4-start.md) (Result section).
