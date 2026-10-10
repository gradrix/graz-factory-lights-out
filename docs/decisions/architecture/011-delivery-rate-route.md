# Measure end-to-end delivery on real repositories before further qualification

Status: accepted, 2026-10-10. Decision maker: the user ("take over the task and implement all these recommendations", 2026-10-10), choosing the agent's retrospective recommendation over continuing candidate-4 requalification. Originating unit: `.scratch/autonomy/delivery/11-delivery-rate.md`.

## Choice

1. Stop review-only qualification. Candidate-4 gate 1 (trial 7) was stopped incomplete on the rig and blind run B (trial 8) is not run. The maintained ensemble (decision 010) is merged into `main` as the opt-in reviewer it was built as; the default reviewer is unchanged.
2. The next measurement is the **end-to-end delivery rate**: worker + review + repair on tasks mined from the user's own repositories, scored by hidden tests the factory never sees. Agent-written cohorts no longer count as the deciding evidence.
3. The roadmap is replaced by five phases with explicit go/no-go numbers ([roadmap](../../roadmap.md)): delivery rate, worker head-to-head against a standard harness, a test factory with mutation-score acceptance, then queue/decomposition, then brief-to-product.
4. Process is proportional to an experiment loop on a personal rig: one run note per phase, failures preserved, no per-trial admission/hash/score file sets or Bind/Record commit pairs.

## Rationale

- The runtime on `main` had not changed for six days (last `gflo/` commit 92deaab, 2026-10-04) while about 37 commits on `main` recorded review experiments on agent-written ~95-line fixtures (the integration branch added 12 more, which did change `gflo/`).
- The review ensemble already passed 16/16 and 24/24 (candidate 3) and 24/24 (candidate 4, blind run A). Its remaining failure was one temperature-0 loop, repaired by sampled escalation (60472ae).
- The bottleneck is upstream: the planning pilot (decision 008) produced no complete multi-file increment, and the API arms exhausted their budgets. A stronger reviewer can only reject such output more reliably.
- Review costs 17–31 minutes and ~0.4M tokens per ~95-line project, so its scaling to real repositories is itself unmeasured.

## Remaining assumptions

- Tasks mined from git history (revert a feature commit, keep its tests hidden) represent the user's real work better than synthetic cohorts. Commits whose tests do not isolate the change are excluded, which biases toward well-tested changes.
- The 30% / 50% thresholds in the roadmap are agent-proposed planning numbers, not measured baselines.

## Evidence

Retrospective of session 39c48ab7 and repository state at 831c9ef; candidate-4 results in `.scratch/.sflo/09-autonomy-review-qualification/run.md`; the Phase 0 code tree (identical code to cf8bd5d) ran 179 tests on the rig with only the two known issue-10 subtests failing.
