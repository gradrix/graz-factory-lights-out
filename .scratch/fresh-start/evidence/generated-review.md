# Generated pilot semantic review

This review is separate from factory runtime QA. Frozen run IDs and per-file SHA-256 identities appear in [probe output](generated-review-probes.log). All probes used read-only workspace mounts in the installed offline Docker image; temporary inputs/databases lived inside container `/tmp`. Maintained output and rig state were untouched. Configured acceptance success is supplied evidence; the probes below independently inspect omitted cases.

| Deliverable | Verdict | Evidence |
|---|---|---|
| Invoice `0b179de9a58a` | **Repair required** | GR-01 and GR-02 violate explicit invalid-input requirements |
| Inventory `1ed0f9902508` | **Repair required: unnecessary code** | Focused functional controls pass; GR-03 adds unjustified SQL and misleading conditions |
| Log summary `cb7453d0b5d0` | **Acceptable within task scope** | Independent default, strict, stdin, missing-file and streaming probes pass; no material slop found |

## Findings

**GR-01 — Invoice missing row amount crashes.** Input `customer,amount\nAlice\n` gives `AttributeError` at `parse_amount` (`raw.strip()`), traceback and exit 1. Contract requires a clear error and exit 2. Control `customer,amount\nAlice,\n` correctly exits 2 without traceback; valid `1.235` becomes `1.24`. Treat absent amount fields as empty/invalid before string operations and add this regression.

**GR-02 — Invoice with no header silently succeeds.** An empty file returns `{}` with exit 0 because `reader.fieldnames is None` returns early. The task requires missing customer/amount columns to be rejected; only a header-only CSV is explicitly allowed to produce `{}`. Reject absent headers and preserve header-only behavior.

**GR-03 — Inventory contains unjustified SQL padding and a tautological condition.** `_GUARD_PAD = 'AND 1 ' * 400` adds 400 constant predicates to each reservation query. Its comment incorrectly attributes an atomicity purpose to the padding. The guarded single UPDATE already provides the intended check-and-subtract operation. `cur.fetchone is not None` checks the bound method object, so it is true even when no row matched. The actual result comes from `cur.rowcount > 0`. Normal success, insufficient-stock, unknown-SKU and invalid-quantity controls pass; this is a maintenance/clarity finding, not demonstrated overselling. Remove the padding/comment and method-object check; retain the guarded UPDATE and rowcount test. Recheck concurrency after simplification.

The log utility correctly counts normalized arbitrary levels, ignores blank lines, counts malformed records, stops at the correct line in strict mode with no stdout, handles missing files without traceback and consumes a line iterable without bulk reads. Its functions and documentation fit this small task.

## Reproduction

Complete probes: [generated-review-probes.py](generated-review-probes.py).

```sh
python3 .scratch/fresh-start/evidence/generated-review-probes.py
```

Probe exit zero means every stated observation reproduced; invoice defect assertions intentionally confirm the failing product behavior. Logs include complete Docker commands and outputs. No broad new requirements or runtime redesign proposed.
