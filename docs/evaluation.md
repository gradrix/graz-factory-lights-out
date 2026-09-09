# Evaluation

Results recorded on 2026-09-08. GFLO is an experimental developer preview.
**The larger-build progression gate failed:** numerical targets passed, but review
found two false acceptances. Finite checks cannot rule out further defects.

## Local-model campaign

Forty distinct small Python tasks, ten per category, ran three fresh repetitions.
Repetitions are not additional independent tasks. Fixtures, gates, runtime, model,
and policy were frozen before scoring; all reference candidates passed preflight
and every starting candidate failed at least one gate.

| Category | Runs | Gate accepted | Verified after review | Target |
| --- | ---: | ---: | ---: | ---: |
| Implementation | 30 | 29 | 29 | 24 |
| Defect repair | 30 | 30 | 28 | 24 |
| Consumer API migration | 30 | 25 | 25 | 24 |
| Requirements-derived test data | 30 | 27 | 27 | 24 |
| Total | 120 | 111 | 109 | 108 |

The RTX 5090 ran the [pinned graph-enabled vLLM profile](../infra/serving/vllm-5090-graphs.example.json):
Inferact/Qwen3.8-27B-NVFP4, temperature 0, seed 42, thinking disabled, and an 8K
worker budget with 2K output reserve. Across 228 attempts, recorded usage was
252,944 prompt tokens, 51,496 completion tokens, and 950.1 seconds of model time.
Cumulative atom time was 1,903.0 seconds; median atom time was 9.57 seconds.
The maximum prompt was 2,087 tokens. Larger-context policies were not compared.

Supplemental probes checked all 84 accepted non-test-generation runs. All 27
accepted test-generation runs passed a known-good implementation and three seeded
mutants each, with additional domain inspection. The two discovered defects were
incorrect deduplication when several IDs repeated, and unstable ordering of
numerically equivalent versions with different component counts.

Both defective acceptances now have immutable findings that block reuse. Nine
other runs exhausted their ten-attempt budgets. Some API migration failures also
exposed ambiguous task wording, so model capability alone does not explain them.

## Follow-up evidence

- Readable validation feedback repaired 3/3 matched cases versus 1/3 with legacy
  feedback on the already-seen bracket task. This small comparison is diagnostic,
  not a fresh held-out improvement score.
- Strengthened gates reject both known bad candidates and accept reference fixes.
  The local model repaired deduplication on its second attempt. Version-sort repair
  exhausted ten attempts, then three more under a clarified replacement contract.
- One live prepared integration accepted a provider and two consumers on their
  first attempts, then passed independent combined gates. This does not establish
  large-project planning or general integration reliability.
- The latest enabled test suite passed 253 tests and 25 subtests with no skips.
  Recovery evidence covers controller/execution deaths and storage boundaries.
  The accumulated integrity matrix has 50 covered rows, but it is not a fresh
  same-build 50-case campaign. Tokenizer-death overlap was checked at the client
  boundary, not proven inside a running GPU kernel.

The full 120-run campaign predates the latest feedback and finding changes; its
score must not be presented as a fresh evaluation of the current runtime.

## Reproduction

Install the development environment and [model service](../infra/serving/README.md)
and pull the broker image as described in [Getting started](getting-started.md).
The harnesses write their own manifests and evidence to a new output directory:

```sh
mkdir -p .gflo/evidence
.venv/bin/python scripts/review_heldout.py --manifest .gflo/evidence/probes-new.json
.venv/bin/python scripts/run_heldout.py --output .gflo/evidence/heldout-new --config infra/serving/vllm-5090-graphs.example.json
.venv/bin/python scripts/review_heldout.py --manifest .gflo/evidence/probes-new.json --campaign .gflo/evidence/heldout-new
```

These are sustained GPU/Docker workloads, not documentation smoke tests. Read each
script's `--help` before running follow-up or fault-injection harnesses. Current
source can reproduce the procedure but cannot recreate the old runtime merely by
rerunning it. Historical raw model responses, ledgers, source snapshots, and host
telemetry remain local; they are not included in this public summary. An audited,
sanitized evidence bundle remains a release task, so readers cannot yet independently
verify every historical claim from a clean checkout.

## Repair diagnosis — 2026-09-09

On the already-seen version-sort failure, three one-attempt repetitions per
treatment found baseline 0/3 at both 2K and 4K output reserves. Reasoning truncated
3/3 at 2K, but repaired 3/3 at 4K; targeted human-written repair guidance passed
2/3 at each budget. Gates and the total 8K budget stayed fixed. All seven accepted
repairs passed 69 supplemental inputs each. The reasoning repairs took 24–60
seconds end to end, so this is a candidate escalation profile, not a default-policy
change or large-build qualification. The interrupted partial comparison is retained
separately, with unknown lost inference cost. The original campaign score is unchanged.

The explicit reasoning profile now has protocol regression coverage. Current CPU
suite: 247 tests and 25 subtests passed, eight optional Docker checks skipped. Live
repair and supplemental gates used actual Docker containers.

## Stateful workload qualification — 2026-09-09

The opt-in low-effort escalation profile verified 23/24 small task runs, and the
three-module inventory migration passed. The initial tool-capable stateful campaign
completed one build, then failed the second build's final migration; the third was
unscored. That failed score is preserved.

After bounded observed-error feedback and explicit reporting-interface instructions,
a new frozen campaign completed all three ten-step builds: 30 accepted tasks in
32 attempts and 33 model turns. All three final migrations passed first attempt.
Each build passed six supplemental workflows and three additional boundary
workflows. No false acceptances were discovered in those checks. Source hashes
matched; referenced artifacts were present and uncorrupted.

Recorded usage: 59,084 prompt tokens, 12,878 completion tokens, and 219.51 seconds
of observed model-call time; no recorded observations lacked validated usage.
This is not total elapsed build time or GPU-only inference time. One Docker memory
qualification probe lacked its OOM flag, halting before work; explicit resume
rechecked the same controls successfully without resetting worker attempts.

This is a seen reference workload with fresh candidates, not an unseen repository
benchmark. Feedback and interface wording changed together, so their individual
contributions are not established. Gates and bounded retry limits were retained.
Prepared tasks and advancing source bases still come from a trusted harness.
Original 120-run scores and findings remain unchanged; large-system reliability
remains unqualified. See the [portable results](../.scratch/local-lights-out-factory/stateful-inventory-feedback-results.json).
