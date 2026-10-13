# Start phase 4: queue and integration, measured on mined commit chains

Status: accepted, 2026-10-12. Decision maker: the agent, under the user's delegation ("when it comes to other your recommendations and suggestions - sure, go ahead with it", 2026-10-11). The user chose the terse-objective arm as the check before this decision (2026-10-11). Originating unit: `.scratch/autonomy/delivery/11-delivery-rate.md`; next unit `.scratch/autonomy/delivery/12-queue-integration.md`.

## Evidence

The phase 4 gate was about 50% delivered on real tasks (roadmap, decision 011).

| arm (16 mined tasks, running-coach 11 + gflo 5) | delivered | false accepts | median s |
|---|---|---|---|
| detailed objectives, frozen 7cedc3c | 14/16 | 1 | ~620 |
| terse objectives (about half the length), same code | 13/16 | 1 | 796 |
| phase 2 best arms (8123102): all aids / mini-swe-agent | 16/16 / 15/16 | 0 / 0 | 909 / 485 |

- The rate does not depend on operator-length briefs. Terse objectives lost one more task (3e6e4bd exhausted on a recorded-reps headline the shorter text no longer spelled out). They kept the same false accept (57271fe, ambiguous "index") and took about 30% longer with more second attempts.
- Every arm is far above the gate. The open limit is task shape, not rate: all 16 tasks are single commits of 2–137 source lines, and multi-module features are still unmeasured (decision 008 measured planning decomposition failing on them).

## Choice

Phase 4 starts, and its first unit measures before it builds broadly:

1. **Mine commit chains** of 2–4 consecutive commits from the user's repositories that together build one feature. The hidden tests are those of the final commit. The same mining rules apply as in phase 1, and private data stays on the rig.
2. **Two arms on the same chains.** *Direct*: one task carrying the combined objective. *Queued*: one task per commit, run in dependency order. Each task starts from an integration branch that holds the earlier accepted patches, and the full suite (no new failures) runs after every merge. A rejected step stops its chain and the run says so.
3. **Build only what arm 2 needs:** a durable queue file with dependencies, branch integration in a controller-owned clone (never the user's repository), and resume. Environment and browser tools for the worker, and model-planned decomposition, wait for this measurement.

**Accept** (agent-proposed): chain delivery for each arm, scored by the final commit's hidden tests. The queued arm earns a default role only if it delivers at least as many chains as direct with no more false accepts.

## Remaining assumptions

- Chains mined from history are human-decomposed. The queued arm measures executing a good decomposition, not producing one. Model-planned decomposition is a later arm.
- One run per chain and arm, on one model and one rig.

## Result (2026-10-13)

Six mined chains (2–3 commits each; running-coach 4, gflo 2), one run per arm, code 60d6e0d. Run note: `.scratch/.sflo/12-queue-integration/run.md`.

| arm | chains delivered | false accepts | exhausted | total time |
|---|---|---|---|---|
| direct (one task, combined objective) | 2/6 | 3 | 1 | 9,113 s |
| queued (`gflo queue run`, one step per commit) | 2/6 | 3 | 1 | 16,021 s |

- The queued arm meets the bar only as a tie, and the two arms traded the two gflo chains, which is within the run-to-run noise decision 013 measured. It took 1.8× the time. **The queue earns no default role**: `gflo queue run` stays experimental and opt-in. Agent decision, under the same delegation.
- The queue itself worked end to end on the rig (13 steps run, integrated and committed; the stop after an exhausted step behaved as designed).
- **New limit:** 6 of 10 accepted chains failed the reference tests, against 1 of 15 accepted single commits in phase 1. On feature-sized work, "no new failures plus the worker's own tests" does not certify the behaviour. Splitting into steps does not help, because every step shares that blind spot. Feature delivery is 2/6 in either arm, below phase 4's own 50% gate. Phase 5 is not earned. The next step is a route choice about acceptance for feature-sized work, which is put to the user.
