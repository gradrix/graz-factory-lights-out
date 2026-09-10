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

## Reviewed feature progression and bounded manager probe

A local planner produced a four-task expense-report plan from explicit requirements
and existing scaffold interfaces. Trusted review supplied separate process gates.
Three independent executions accepted all 12 tasks in 12 attempts. Each combined
validation included engine/renderer/documentation checks plus 25 seeded valid CLI
inputs and five invalid inputs. Omitted archive content was preserved. Replaying
each completed graph produced the same result without model calls. This is one
product repeated, not three distinct product benchmarks.

An underspecified currency/month variant initially exhausted six model turns
rereading files. Adding a clarification-only result exposed an envelope mismatch:
two responses contained questions but failed the required outer protocol. With an
explicit envelope instruction, the model returned reporting-currency, rate-source,
record-schema, output-format, and compatibility questions in one turn. The updated
planner also produced a valid three-task plan for the specified product; those three
tasks and the independent combined behavior checks passed in one additional run.
The earlier failed probes remain failures; the follow-up does not erase them.

These results support bounded planning under reviewed requirements and narrow
clarification behavior. They do not establish business strategy, recursive manager
reliability, autonomous test authority, or large-repository build capability.
Source outside selected inputs was deliberately inert. Earlier campaign scores and
false-acceptance findings are unchanged.

Portable [results](../.scratch/local-lights-out-factory/feature-progression-results.json)
and the [fixture](../.scratch/local-lights-out-factory/feature-progression-fixture.json)
retain the exact request, model proposal, reviewed gates, source recipe, and image
pins. Recreate the original four-task fixture without executing source or a model:

```sh
.venv/bin/python scripts/prepare_feature_trial.py --output .gflo/feature-reproduction
```

The script refuses an existing output directory and verifies the reconstructed
snapshot identity. It prints the plan, ledger, and snapshot digest. With the pinned
model service and broker image available, execute the printed plan using
`gflo --db DATABASE run-feature PLAN --current SNAPSHOT_DIGEST`. This re-executes the
retained reviewed plan. A new planner run is a separate observation, using the
emitted request/profile/deployment and the ledger's artifact store. Historical raw
model exchanges and process receipts remain under ignored `.gflo/evidence/feature-progression-v1/`
and need separate transfer for forensic replay.

## Specialist-board comparison (2026-09-10)

Single planning remains the default; `plan-feature --board` is experimental.
On one unfamiliar checkout-quote feature, both reviewed three-task plans passed
identical independent task and whole-feature gates in three worker attempts each.
The board showed no additional quality benefit in this small comparison.

| Compact follow-up | Planning calls | Total planning tokens | Model time | Outcome |
| --- | ---: | ---: | ---: | --- |
| Single | 2 | 8,294 | 36.1 s | Three tasks accepted |
| Board | 7 | 29,628 | 113.8 s | Three tasks accepted |

The board used 3.6 times the planning tokens. Counts include failed calls and use
server-reported usage; execution costs are separate. All roles used the same local
Qwen model/profile, so these are not independent model opinions.

Initial single planning exhausted its attempts; initial boards exceeded the 12,000-byte
advice limit. More concise instructions and changed ordering of the same four context
files preceded the paired follow-up; their effects cannot be isolated. The ambiguous
request correctly stopped single planning, while board specialists found the missing
rounding policy but coordinator output failed the response envelope twice.
Those failures remain recorded. A subsequent deterministic early-blocker gate returned
the product specialist’s clarification after one live call (2,937 tokens, 10.5 s),
without synthesis. This follow-up does not replace the earlier failed result.

[Portable results](../.scratch/local-lights-out-factory/board-comparison-results.json)
retain each trial. The [fixture](../.scratch/local-lights-out-factory/board-comparison-fixture.json)
contains source files, requests, proposals and trusted reviews/gates. Recreate source
with `snapshot_bundle(store, SourceBundle(files=fixture["source_files"]))` and verify
the request’s snapshot reference before execution. Raw exchanges and receipts live
in ignored `.gflo/evidence/board-comparison-v1/` and need separate transfer.
This is one feature and one ambiguity probe, not a large-repository qualification.


## Policy-driven build handoff (2026-09-10)

The previously seen checkout feature now runs through one `build-feature` command:
local planning, deterministic policy compilation, three worker tasks and independent
combined gates. Trusted file/integration checks were fixed before this new planning
run; no generated plan was edited to fit them. All three tasks passed in one attempt
each. Planning used two calls (8,294 tokens); the first omitted required fields and
is retained as a failure. The three workers used 4,445 validated tokens in total.
Replay returned the same accepted result without additional recorded planning or
worker calls. This is workflow qualification, not a new unseen-product benchmark.

The withheld-rounding variant returned `needs-info` in one call (3,092 tokens) and
started no execution. Fifteen new tests cover policy rejection, question/exhaustion
halts, changed bindings, tampered proposals, and interrupted execution replay through
the real ledger/controller with service doubles. Full suite: 375 passed, eight
optional Docker skips, 25 subtests; ruff/mypy passed. The actual feature trials used
the local GPU model and Docker gates separately from those skipped host tests.

[Results](../.scratch/local-lights-out-factory/policy-build-results.json) and
[fixture](../.scratch/local-lights-out-factory/policy-build-fixture.json) are portable.
`scripts/prepare_policy_trial.py` reconstructed the exact snapshot in a fresh store.
Raw evidence remains in ignored `.gflo/evidence/policy-build-v1/`. Existing campaign
scores, board failures, and open memory-qualification findings remain unchanged.


## Python definition navigation (2026-09-10)

On a captured 220-file, 1,815,776-byte GFLO repository, the `gflo` scope contained
27 Python files. All indexed successfully in 0.332 seconds; unchanged reuse took
0.007 seconds and reparsed zero files. Five preselected simple/qualified names
located their expected source files and verified source reads. Nine tests cover
nested/async/duplicate definitions, stale snapshots and shards, scopes, syntax and
budget coverage, reuse, and CLI access. These timings are a single local run, not
large-repository performance qualification. No model participated in these probes.
See [results](../.scratch/local-lights-out-factory/symbol-navigation-results.json).


## Memory qualification reliability (2026-09-10)

The earlier intermittent exit-137/no-OOM-flag halt reproduced in both full and
memory-only qualification. Waiting one second did not restore the Docker flag.
Observation of the exact failing container's local cgroup counters confirmed a
kernel OOM kill. A trusted supervisor now retains those counters around a bounded
allocator child, requiring limit, OOM and kill increments plus child SIGKILL.
This follows the [kernel's cgroup memory-event semantics](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html).

All 100 prospective complete qualifications passed. Real unrelated-SIGKILL and
no-allocation probes were rejected. Ten new regression cases cover missing counters,
wrong child status, changed cgroup, malformed output, stderr, timeout and exit errors.
Full suite with Docker enabled: 402 tests and 25 subtests passed, with no skips.
[Results](../.scratch/local-lights-out-factory/memory-qualification-results.json)
preserve baseline failures and prospective proofs. This fixes qualification evidence;
it does not relax resources or rescore previous campaigns.


## Recursive-settings feature and portable replay (2026-09-10)

A new recursive settings merger passed three fresh policy builds: nine tasks accepted
in nine attempts, plus final integration gates. The fixed checks cover 100 seeded
recursive reference comparisons, mutable alias preservation, invalid nested values
and nonfinite numbers, existing decoder delegation, and two-line CLI framing. Each
build preserved 60 archive files and the existing decoder. Planning used one, two,
and two calls; malformed initial proposals in the latter runs remain recorded.

Definition queries selected the four relevant files from a 64-file snapshot before
planning. These were prepared queries, not model-chosen repository navigation.
The product still had stubs and explicit requirements; three successful builds do
not establish broad large-product reliability.

Portability testing found a real replay defect: mapping order affected derived gate
lists under an unchanged policy/plan digest. New materialization sorts those lists;
replay preserves historical ordering only when every gate and other contract field
matches. Four regression cases and all three live replays passed without new model
calls. Both earlier board-comparison ledgers also replayed exactly. Full suite with
Docker enabled: 406 tests and 25 subtests passed, no skips; ruff/mypy passed.
[Results](../.scratch/local-lights-out-factory/navigation-feature-results.json) retain
the failure and fix. The [fixture](../.scratch/local-lights-out-factory/navigation-feature-fixture.json)
reconstructs using `scripts/prepare_policy_trial.py --fixture FIXTURE --output NEW_DIR`.
Raw evidence stays in ignored `.gflo/evidence/navigation-feature-v1/`.


## Real repository trial: ai-gamer, 2026-09-10

A prepared rule-correction task on ai-gamer's 87-file snapshot produced an accepted
local-model implementation, delivered in [PR 1](https://github.com/gradrix/ai-gamer/pull/1).
It passed all 19,683 3x3 boards against a trusted reference and larger-board checks;
86 other original files, including a SQLite database, were preserved. Codex supplied
17 regression cases after every local test-generation trial halted. Those tests pass
the candidate and reject the original. This was not an end-to-end factory success.

Initial plain and reasoning trials failed or truncated. Low reasoning with a 12K
context / 6K output budget repaired the implementation on its second attempt but
spent both test responses entirely reasoning. Separate plain test trials also failed.
Task selection, requirements and trusted gates were prepared by Codex; validation
feedback exposed reference code. These results do not measure unaided task discovery
or training quality. Legacy gameplay tests cannot collect due to stale imports;
training, services and dashboard were not exercised.

[Portable results](../.scratch/local-lights-out-factory/ai-gamer-winners-results.json)
retain all six trial outcomes and attribution. The
[fixture](../.scratch/local-lights-out-factory/ai-gamer-winners-fixture.json) reconstructs
original and follow-up snapshots via `scripts/prepare_repository_trial.py`.
Factory validation at this checkpoint: 410 tests and 25 subtests with Docker enabled.


Follow-up: projecting remaining turns/output into the worker instruction yielded two
complete test candidates, but both failed semantic checks. A subsequent four-file
decomposition accepted gap and anti-diagonal tasks on their first attempts; the
potential task failed on an invalid draw fixture and then truncated. Rectangular
coverage and integration were never reached. These are negative qualification results,
not proof of reliable autonomous test generation. See
[budget results](../.scratch/local-lights-out-factory/worker-turn-budget-results.json)
and [split-task results](../.scratch/local-lights-out-factory/ai-gamer-split-tests-results.json).
The product fix PR is merged; its final tests were written by Codex. The current
Docker-enabled factory suite passed 412 tests and 25 subtests.


## Development repair follow-up, 2026-09-10

The model and serving configuration were unchanged. An opt-in protocol adds pinned
sandbox development checks, retained drafts, and hash-bound exact text edits. A
trusted generator supplies verified example boards as read-only data. Exhausted
work produces a review packet instead of resetting its retry budget.

The first repair-only trial accepted three tasks then halted. Assisted planning
exhausted two malformed JSON responses, requiring an explicitly reviewed plan. That
run passed its gates, but review found square-only coverage in the rectangle tests;
an immutable finding now blocks that acceptance. A new coverage check requires actual
winning calls in every direction on non-square boards. The first correction trial
truncated twice. After existing files were restricted to small edit responses, the
same correction passed in one response: 6212 prompt / 1695 output tokens, 28.80 seconds.

The corrected set passes 20 generated tests, rejects the original with four assertion
failures and no other errors, and rejects always-True/False potential mutants. The
non-square coverage check and original exhaustive winner oracle pass. All 91 other
files remained unchanged; replay required no new worker observations. This is a
reviewed-plan, data-assisted result on a seen task, not an unattended or held-out
success score. [Portable results](../.scratch/local-lights-out-factory/development-repair-results.json)
retain every stage, including the challenged acceptance.

Final validation: 423 tests and 25 subtests passed with Docker checks enabled;
ruff and mypy passed. The model weights and serving deployment were unchanged.


## Second real repository: leds-service, 2026-09-10

With the same model and existing generic repair protocol, local planning and two
workers produced a configuration-parser fix and five tests on their first attempts.
Review found that the whitespace test used default values and survived a silent
fallback mutant. An immutable finding blocks reuse of that initial acceptance.
A reviewed repair task added a sixth, non-default regression in one local response:
2567 prompt / 455 output tokens, 7.89 seconds. The two initial workers used 3624
prompt / 1425 output tokens and 23.68 seconds combined (excluding planning).

All six tests pass; the suite rejects the original implementation and the fallback
mutant. Independent checks compare against a reference parser on fixed edge cases
and 600 seeded configurations. AST comparison confines original code changes to
initConfigs, and all 84 other original files remain identical. Replay adds no model
observations. No factory core customization was necessary for this product.

Codex selected the task, supplied requirements and trusted checks, reviewed coverage,
and prepared the corrective task. The local model wrote all shipped implementation
and test source. This is one supervised feature on a second real repository, not a
held-out reliability score or hardware/service qualification. Both initial acceptance
and the subsequent finding remain in [portable results](../.scratch/local-lights-out-factory/leds-config-results.json).
[Initial](../.scratch/local-lights-out-factory/leds-config-fixture.json) and
[repair](../.scratch/local-lights-out-factory/leds-config-repair-fixture.json) fixtures
reconstruct from the pinned upstream revision with prepare_repository_trial.py.

The selected source is merged in [leds-service PR 10](https://github.com/gradrix/leds-service/pull/10).
No factory core code changed during this qualification; targeted checks, fixture
reconstruction and replay passed. The preceding full factory validation remains
423 tests and 25 subtests with Docker enabled.
