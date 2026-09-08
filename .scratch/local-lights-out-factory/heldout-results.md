# Forty-task local-model evaluation — 2026-09-08

**109/120 runs survived the campaign checks, but progression is not qualified:**
two results passed the original gates and failed the prospective supplemental probes.
All numerical targets were met; the zero-discovered-false-acceptance requirement was not.

| Class | Runs | Original gate acceptances | Verified after review | Target |
|---|---:|---:|---:|---:|
| Implementation | 30 | 29 | 29 | 24 |
| Defect repair | 30 | 30 | 28 | 24 |
| Consumer API migration | 30 | 25 | 25 | 24 |
| Requirements-derived test data | 30 | 27 | 27 | 24 |
| Total | 120 | 111 | 109 | 108 |

Forty distinct small Python tasks, ten per class, ran three fresh repetitions each.
Repetitions are not independent new tasks. Fixtures, gates, runtime, model and policy
were frozen before scoring; all forty reference candidates passed preflight and all
starting candidates failed at least one gate. The first draft preflight was stopped
before any model scoring to replace data conversions with consumer API migrations.
It remains in `.gflo/evidence/heldout-v1/`.

The qualified run is `.gflo/evidence/heldout-v1-qualified/`. Its `evaluation.json`
records no source drift during scoring. Model: pinned Inferact/Qwen3.8-27B-NVFP4 on
the RTX 5090, graph-enabled vLLM, temperature 0, seed 42, thinking disabled, 8K total
worker budget and 2K output reserve. Storage admission reserve: 256 MiB.

There were 228 Attempts and model observations: 252,944 validated prompt tokens,
51,496 completion tokens and 950.1 seconds of observed model time. Cumulative atom
execution time was 1,903.0 seconds; median atom time was 9.57 seconds. All recorded
usage was available. Maximum measured prompt was 2,087 tokens; all turns fit the 8K
policy with reserved output. No 4K/16K/32K policy comparison was performed.

## Failures and false acceptances

Nine runs exhausted ten attempts: bracket checking once, instance API migration three
times, paged API migration twice, and suffix-test generation three times. Some migration
failures expose ambiguous public input/output wording; do not attribute all failures
to model semantics. The suffix tests contained a real wrong expectation for a string
with leading whitespace that still ended in `.py`.

The extra probes covered all 84 accepted implementation/repair/migration runs. All 27
accepted test-generation runs passed a known-good implementation and their three
required seeded mutants; inspection also found no inputs outside the declared domains.
These are finite checks, not proof that no other defects exist.

Two confirmed false acceptances:

- `heldout-v1-r1-dedupe-last`: removing old list entries left stale indices when
  different IDs repeated, producing the wrong records.
- `heldout-v1-r2-version-sort`: unequal-length component lists did not preserve the
  order of numerically equal versions such as `1.0.0` and `1`.

Both now have immutable Acceptance findings. Historical acceptances remain intact,
but controller replay and prepared integration reject their reuse. A pre-finding
SQLite/artifact snapshot is in `frozen-ledger/`; it remains readable by the frozen
version-2 implementation. The live ledger requires reader version 3. No campaign
result or candidate was replaced.

## Follow-up changes and limits

`bounded-python-v4` exposes bounded readable observed stdout/stderr to repair workers,
while preserving raw provenance and excluding expected gate outputs. A separate matched
follow-up on the seen bracket failure repaired 3/3 cases with readable diagnostics
versus 1/3 with legacy feedback (three pairs, at most two actual repair turns per case).
That is diagnostic evidence on one seen task, not a new held-out improvement score.
Raw evidence: `.gflo/evidence/feedback-recovery-v1/`.

Strengthened regression gates reject both retained bad candidates and accept their
references. The local model repaired deduplication on Attempt 2. Version sorting still
exhausted ten attempts; a separately counted replacement contract with a public tie
example and an additional private gate also exhausted its three-attempt budget. These
failures are retained in `semantic-repairs-v1/` and `version-sort-clarified-v1/`.
No manual product repair or silent budget reset was used.

The runtime now has 253 passing tests plus 25 subtests with real Docker checks enabled,
no skips (`.gflo/evidence/factory-final-v1/`). Acceptance findings cover duplicate
reporting, bad bindings, missing evidence, reopening, concurrent acceptance checks,
transaction rollback and dependency reuse. The broader integrity map has 50 scoped
accumulated evidence rows; it is not a fresh same-build fifty-case campaign.

Next: diagnose persistent semantic repair, make public input/output contracts explicit,
and qualify stronger gate coverage before another fresh workload or larger-build claim.
This campaign does not establish general large-project feasibility.
