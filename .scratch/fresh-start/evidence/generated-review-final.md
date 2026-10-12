# Final generated-output semantic recheck

**Verdict: all three final deliverables are acceptable within the bounded pilot contracts.** This is independent semantic review of generated outputs, separate from factory runtime configured acceptance. Factory runtime was unchanged from candidate2; its QA is recorded separately.

| Output | Final run | Configured acceptance rerun | Independent semantic result |
|---|---|---|---|
| Invoice | `41fbdafe38ff` | All three checks pass | GR-01/GR-02 resolved; quoted whitespace preserved |
| Inventory | `ff554c2e0dfd` | Both checks pass, including concurrency | GR-03 resolved; concurrent processes cannot oversell in the tested case |
| Log summary | `cb7453d0b5d0` | Both checks pass | Prior independent semantic pass retained; all workspace file hashes unchanged |

## Resolved findings and controls

- **GR-01:** Missing row amount and explicitly empty amount both now exit 2 with useful stderr, no traceback and no stdout. Valid amounts remain accepted.
- **GR-02:** Empty input now rejects missing header. Header-only input remains a successful `{}`. A header missing the amount column also fails correctly.
- **Quoted names:** `" Alice "` remains the distinct key ` Alice `; `Alice` remains a separate customer. Quoted comma names remain intact. Whitespace-only customer names reject correctly.
- **Adjacent invoice controls:** Per-row half-up rounding, negative refunds, zero formatting, nonnumeric amounts, NaN and Infinity all meet the tested contract expectations. Both `summarize(stream)` and CLI success paths were exercised.
- **GR-03:** SQL padding, its misleading comment and the method-object condition are removed. Reservation uses one guarded UPDATE and affected-row count without replacement complexity. Two independent CLI processes reserving four from five yield exactly one success and one remaining. Insufficient/unknown stock and invalid-quantity controls reject; put/get behavior remains intact.

The unchanged log-summary retains the earlier independent default/strict/stdin/missing-file/streaming evidence; its configured behavior and quality checks were also rerun here. No further material slop found in the repaired areas. These checks do not certify requirements beyond the task contracts or replace patch review for future changes.

## Evidence and reproducibility

Complete probe: [generated-review-final-probes.py](generated-review-final-probes.py).
Full per-file SHA-256 identities, commands and results: [generated-review-final-probes.log](generated-review-final-probes.log).

```sh
python3 .scratch/fresh-start/evidence/generated-review-final-probes.py
```

Exit zero requires every configured check and independent assertion to pass. The final line is `ALL_RECHECKS_PASS`. Runs use the installed pinned Docker image with read-only workspace/acceptance mounts and disposable `/tmp` inputs; no rig action or maintained-source mutation occurred.

Original failed evidence remains in [generated-review.md](generated-review.md), its probe/log and `invoice-edge-failure.json`. Invoice lineage is `0b179de9a58a → 08187f980bed → 41fbdafe38ff`; inventory lineage is `1ed0f9902508 → ff554c2e0dfd`. Final acceptance does not relabel those earlier failures as successes.
