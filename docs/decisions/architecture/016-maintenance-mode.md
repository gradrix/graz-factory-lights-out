# Maintenance mode until a stronger local model passes the gates

Status: accepted, 2026-10-14. Decision maker: the user ("ok, let's put it in maintenance mode", 2026-10-14), on the agent's recommendation after decision 015. Originating unit: `.scratch/autonomy/delivery.md` route check (2026-10-14).

## Evidence

- Small, precisely described changes: 14/16 delivered with the default worker (decision 011 route, phase 1). Retries converge: the 3 hard tasks were delivered 8/9 times over three runs (decision 013).
- Feature-sized work: 2/6 delivered, and 3 of 5 accepted features were wrong, whether run as one task or as a queue (decision 014). Objective-derived checks did not close the gap (decision 015).
- Worker variants are at their ceiling on this model (decision 013). The remaining limit is model capability, which harness work does not move.

## Choice

- Stop building new components: no queue or decomposition work, no objective-check round 2, no phase 5, no self-improvement loop.
- Keep the product as it is for its measured jobs: small precisely described changes and test-writing for moderate modules, with every patch reviewed. Keep fixing bugs found in use.
- Prepare re-measurement for the next model instead. The private benchmark is frozen on the rig (`~/gflo-bench`), and `make rig-gate` reruns all three suites and compares them with `ops/benchmark/gates.json`. The to-do list for that day is [model upgrade](../../model-upgrade.md).
- Gates (agent-proposed, user-approved direction): adopt a new model when small ≥14/16 with ≤1 false accept. Resume feature development when features ≥4/6 with ≤1 false accept. Widen the test factory when large-module tests ≥2/3.

## Remaining assumptions

- The benchmark objectives were written from the reference commits; delivery on objectives the user writes before knowing the solution is unmeasured.
- One run per task is noisy (2–3 tasks of 16 between repeats); borderline results are repeated before a decision.
- The baseline numbers come from three code revisions (7cedc3c, 60d6e0d, 149d6af); the gate runs whatever revision is current.

## Result

(Gate runs are added here and in the history table of [model upgrade](../../model-upgrade.md).)
