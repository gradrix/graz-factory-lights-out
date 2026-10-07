# Per-requirement review units — larger finalization thinking cap

Agent decision under user direction 2026-10-07 ("go with a recommendation… as autonomous as possible… scalable"), after [trial 2](run.md): 20/28 units exhausted the 1024-token cap. Contract b795a7bd… otherwise unchanged: units, wire, aggregation, fail-closed exhaustion, acceptance, scalability record.

## Changes

- Unit requests use thinking_budget_tokens 4096 and max_tokens 8192. A cap, not a target: cost scales with reasoning actually used. Exhaustion threshold becomes 4096; exhausted units remain incomplete.
- Per-unit work 300 s, HTTP ≤240 s (first unit per case includes ~75 s uncached prompt plus up to ~60 s thinking at measured ~70 tok/s). Case work = units × 300 s.
- Model, quantization, context, slot count, temperature and reasoning effort unchanged; no server restart or serving configuration change. This is a request parameter of the existing service.

## Risk

Longer thinking may also wander or confabulate; grounding is still assessed independently. A 4/4 pass permits a fresh-case qualification only. If units still exhaust at 4096, the route narrows to evidence selection per unit or a different model profile, under a further contract.
