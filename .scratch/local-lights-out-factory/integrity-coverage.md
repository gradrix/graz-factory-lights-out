# Integrity coverage consolidation

All **50 original matrix rows now have scoped evidence**. This is a retrospective
mapping across retained runs and versions, not a newly scored same-build 50-case
campaign. The machine-readable report preserves this distinction and keeps
`full_integrity_campaign_passed` false.

The final seven gaps have new evidence:

| Rows | Evidence | Boundaries |
|---|---|---|
| 03-3, 03-5 | `.gflo/evidence/prepared-integration-live-v1/result.json` | Pinned provider contracts, common base, independent combined validation; no Git promotion |
| 05-1, 05-2 | `before-request-death-v1`, `read-expansion-death-v1` | Real SIGKILL of co-located controller/worker dispatch; scripted proposals |
| 06-1, 06-2, 06-4 | `model-lookup-death-v1`, `model-tokenize-death-v1`, `model-between-turns-death-v1` | Real local engine death and ordinary resume |

The tokenizer injection occurs after POST transmission and before the client reads
the response. It does not prove that tokenization itself was executing at the
instant of death. This complements deterministic tokenizer protocol-loss coverage.

Prepared integration tests additionally reject stale child contracts, overlapping
edits, corrupted contract artifacts and failed combined gates. Interrupted gates
resume the retained candidate; repeated accepted integration remains idempotent.

[Machine-readable mapping](integrity-coverage.json) hashes supporting receipts.
Previous coverage snapshots remain in `integrity-coverage-v1.json` and
`integrity-coverage-v2.json`. Prior live runs were not all repeated in this consolidation.
