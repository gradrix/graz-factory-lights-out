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

## Reusable test-adequacy gate, 2026-09-10

A generic pytest gate now checks candidate success and assertion-based rejection of
trusted faulty module variants. It rejected the retained weak leds-service suite
because the untrimmed-key variant survived, and accepted the earlier repaired suite.
A fresh local repair used the same reviewed instruction, model and finite budget,
with the generic gate frozen before execution. It passed on one response: 2567 prompt
and 472 output tokens, 8.26 seconds. Independent parser checks passed and replay added
no model calls. No further product changes were published from this repeated trial.

This removes per-trial pytest validation scripting for this pattern; it does not
eliminate trusted variant preparation or demonstrate unaided fault discovery.
The trial is a seen-task correction, not a new reliability score.
[Portable results](../.scratch/local-lights-out-factory/generic-test-adequacy-results.json)
and [fixture](../.scratch/local-lights-out-factory/leds-generic-adequacy-fixture.json)
retain the checks and local response.

Final review added explicit rejection of collection-time skips. A fresh trial with
that final gate also passed in one response (2569 prompt / 467 output, 8.19 seconds)
and replay added no calls. Fourteen targeted regressions pass. The preceding full
suite passed 428 tests and 25 subtests with eight optional Docker skips; all 49 broker
checks passed separately with Docker enabled. Ruff and mypy pass.

## Generated fault qualification, 2026-09-10

The bounded Python mutation generator proposed eight faults in the retained
leds-service parser. Independent reference tests selected six behavioral faults and
excluded two error-producing proposals. The selected set rejected the weak worker
tests on removed key trimming and accepted the repaired tests. Neither faults nor
prompt adjustments were handwritten for this step. Trusted reference behavior and
function selection were supplied by Codex.

In a separate numeric example, both generated faults qualified; an unchanged-source
control and a crashing control did not. An initial reference-wrapper preparation
error produced no selected faults and remains recorded. The corrected portable
fixture reproduces the selection in a fresh artifact store. No model calls or new
product changes were made. This demonstrates bounded fault generation against known
reference behavior, not automatic specification discovery or broad mutation coverage.

[Results](../.scratch/local-lights-out-factory/generated-faults-results.json) and
[fixture](../.scratch/local-lights-out-factory/generated-faults-fixture.json) retain
source, proposals, checks and evidence identities. Validation: 445 tests and 25 subtests
passed with Docker enabled; ruff and mypy passed.

## Prospective color-parser feature, 2026-09-10

A new leds-service feature adds strict six-digit ASCII hex parsing with optional `#`
and surrounding whitespace, preserving white fallback and LED channel order. Gates
were prepared before model calls using a trusted reference and generated mutations.
The first build halted: implementation eventually passed, but the test worker
exhausted two attempts with invalid repair responses. Reference qualification also
had a flaw: one large test stopped at its first assertion and hid later crashes.

A separately recorded preparation split reference inputs into individual tests.
Three generated faults qualified (one fewer), plus the original baseline. The second
build needed an automatic planning retry and an implementation retry, then produced
11 tests in one response with no reviewer source edits. Independent checks passed
fixed edge cases and 600 seeded colors in six forms; the suite rejected every pinned
fault. All 85 other original files were unchanged. Replay added no model calls; all
17 tests in the target's isolated tests directory passed after export.

The final implementation worker used five model responses across two attempts,
9506 prompt / 2334 output tokens, 39.28 seconds. The test worker used one response,
1557 prompt / 701 output tokens, 11.63 seconds. Planning and the failed first build
are recorded separately in [campaign results](../.scratch/local-lights-out-factory/leds-color-campaign-results.json);
these worker totals do not include them. Raw response usage is retained where invalid
protocol output prevented validated usage accounting.

Codex selected requirements, supplied reference behavior and corrected reference-test
preparation between builds. The local model wrote all shipped source. This is a
supervised new-feature trial, not intervention-free success. The model, instructions,
protocol and per-build budgets were unchanged. [Final results](../.scratch/local-lights-out-factory/leds-color-results.json),
[initial fixture](../.scratch/local-lights-out-factory/leds-color-fixture.json), and
[corrected fixture](../.scratch/local-lights-out-factory/leds-color-v2-fixture.json)
are portable. A new gate regression covers mixed assertion/error outcomes; all 15
adequacy tests passed, as did ruff/mypy. The preceding full Docker-enabled suite
passed 445 tests and 25 subtests. No factory runtime code changed in this trial.

The selected change is merged in [leds-service PR 11](https://github.com/gradrix/leds-service/pull/11).

## Repair system-instruction correction, 2026-09-10

Retained traces exposed a protocol contradiction: repair workers received the legacy
system instruction requesting complete file replacements, while user instructions
and parser enforcement required exact edits for existing files. Two rejected full-file
responses carried that contradiction. A LocalModel transport regression failed before
the fix and passed after a dedicated repair system message was introduced. Default
worker instructions and parser/hash/scope enforcement remain unchanged.

A fresh build of the same corrected color fixture passed with the same model and
budgets. Planning reproduced its previous retry. Implementation used four responses
over two attempts (one malformed hash remains), and tests passed in one response.
The preceding build used five implementation responses and one test response. This
single comparison does not establish improved failure rates. Eleven generated tests,
independent reference/fault gates and replay pass; 85 other original files remain
unchanged. No further target-product changes were published.

[Results](../.scratch/local-lights-out-factory/repair-system-results.json) retain the
conflicting traces, exact old/new system messages and fresh trial, including failed
responses and raw usage. Reconstruct with the existing corrected color fixture.
All 446 tests and 25 subtests passed with Docker enabled; ruff and mypy passed.
Hash-copy errors and planning retries remain open reliability limitations.

## Turn-bound repair targets, 2026-09-10

Workers can now use short controller-issued references instead of copying SHA256
hashes. Retained mappings bind the full current source bundle and work contract;
resolution still applies full file-hash, scope, exact-match, overlap and size checks.
Tests cover different drafts/contracts, stale turns, invisible paths, legacy repairs
and equality of tokenized/generated mappings.

A seen color trial reused the existing reviewed plan and unchanged gates, model and
budgets. Implementation used five responses over two attempts; tests passed in one
response. No malformed hashes or target-protocol errors occurred; an implementation
semantic failure still required retry. This single run does not establish improved
failure rates or speed. Planning was not re-exercised. No product changes were shipped.
Replay adds no calls and 85 other original files are preserved.
[Results](../.scratch/local-lights-out-factory/repair-handles-results.json) retain the
plan, targets, responses, costs and outcomes. All 449 tests and 25 subtests passed
with Docker enabled; ruff and mypy passed.

## Planner input/output path clarification, 2026-09-10

The retained color planner failure listed its own new test output in read_paths.
The validator still rejects it, now identifying task T2, tests/test_color.py and the
required distinction between inputs and outputs. Planning briefs explicitly describe
that distinction and report authorized-path presence from full snapshot metadata,
without loading omitted file contents. No plan normalization or dependency inference
was added.

A fresh planning-only trial on the same color request/model/budgets returned a valid
plan on its first response and compiled against the unchanged policy. The test task
reads the existing color module, writes its new test file and depends on the provider.
Usage: 2910 prompt / 1902 output tokens, 31.61 seconds. The preceding retained run
needed a source-reference retry. This is one seen-feature comparison, not a broad
planning reliability score; workers and product code were not re-executed.
[Results](../.scratch/local-lights-out-factory/planner-paths-results.json) retain the
historical rejection, proposal, raw response and compiled-plan identity. All 451 tests
and 25 subtests passed with Docker enabled; ruff/mypy passed.

## Sparse mode selection: semantic planning failure, 2026-09-10

A prospective leds-service stateful feature tested sparse mode IDs, directional
wraparound, empty-registry behavior and controlled activation. Before model calls,
216 independent cases and two reference-qualified generated faults were frozen.
Preflight excluded the original implementation from the assertion-only mutation set
because it crashes on valid activation inputs; a separate oracle rejects the original.
The reference checks still cover those activation cases. Portable reconstruction passed.

Planning returned a structurally valid plan in one response. Its acceptance prose
specified wraparound, but its interface_contracts contained a concrete algorithm with
clamping defaults. The worker copied that algorithm, failed the oracle, and proposed
five unchanged repairs. Six responses across two attempts exhausted its budget.
No implementation was accepted; tests and integration never ran. There were no
repair-target protocol errors.

A separately prepared trial reused the same proposal/source/gates/budgets with a
general instruction prioritizing requirements over planner implementation advice.
It produced the same six-response failure, including five unchanged edits. The prompt
addition was reverted. No runtime change or target-product change was shipped.
Both trials remain separate in [initial results](../.scratch/local-lights-out-factory/leds-modes-results.json)
and [instruction experiment](../.scratch/local-lights-out-factory/leds-modes-priority-results.json).
The [fixture](../.scratch/local-lights-out-factory/leds-modes-fixture.json) preserves
requirements, reference tests, fault qualification and gates.

This is a negative whole-feature qualification. Structural plan validity and working
repair transport do not establish semantic consistency between requirements and
planner advice. The next design task is to separate interface declarations from
implementation advice and prevent contradictory algorithms from acquiring contract
authority. Stronger prose alone did not resolve this example. The factory's 451 tests
and 25 subtests passed with Docker during the experiment; the reverted source matches
the preceding validated runtime, and its transport regression passed again afterward.

## Structured contracts and end-to-end regression, 2026-09-10

Issue 55 separates Python interface declarations from planner implementation advice.
Workers receive original requirements; `contracts-v2` also projects requirements and
declarations from ancestor providers whose outputs the task reads. Suggestions stay
in planning evidence. Contradictions and byte-identical failed drafts produce durable
review stops. Older profiles retain their preparation identities and replay behavior.

Eleven bounded local-GPU trials used the same pinned model/deployment and existing
fixture gates: 32 model responses, 136,034 server-reported tokens and 599.2 seconds of
recorded model-call time. This includes rejected and truncated responses. Protocols
changed during the campaign, so these totals are not a reliability-rate estimate.

| Trial | Outcome |
| --- | --- |
| Modes, escaped-document v1/v2 | Both planning responses truncated; no workers |
| Color and basic configuration, contracts-v1 | Both features accepted |
| Modes, direct-document v3 | Implementation accepted; test worker lacked provider behavior and exhausted |
| Modes, dependency-context v4 | Plan, implementation and 11 tests accepted on their first responses; integration passed |
| Color, direct-document v2 | Planning repeated checks until output truncation |
| Basic configuration, dependency-context v2 | Accepted |
| Color v3 | Accepted after a schema-validation planning retry |
| Strict configuration-test repair v1 | Accepted after a declaration-validation planning retry |
| Modes repeat v5 | Stopped with questions already answered by the original request; no workers |

The successful mode implementation passed the frozen 216-case oracle, generated
fault checks and combined gates. Other methods' ASTs and all other original files
were preserved. Running the accepted snapshot's entire pytest directory in the
pinned offline image passed **28 tests**, including earlier color/configuration tests.
The basic configuration fixture predates its known test-adequacy finding; the separate
strict repair trial uses the stronger generic adequacy fixture, and the old challenged
acceptance remains blocked. No target-source edits or plan corrections were supplied
by Codex during these builds. No target PR was published from this qualification.

Historical color and strict-parser acceptances replayed with zero new ledger events.
A historical ai-gamer halt stayed halted; the challenged parser result stayed blocked.
The factory passed **469 tests and 25 subtests** with Docker enabled; ruff and mypy
passed. Tests cover declaration authority, dependency context, direct JSON transport,
bounded truncation retries, explicit conflicts, repeated failed drafts across attempts,
and review stops surviving ledger reopen. Live successful retries above were schema
validation retries; truncation-retry behavior was exercised by transport/controller
fixtures, rather than observed in a successful live truncation recovery.

[Trial responses, plans and costs](../.scratch/local-lights-out-factory/contracts-qualification-results.json),
[combined repository tests](../.scratch/local-lights-out-factory/contracts-combined-regression-results.json),
and [historical replay](../.scratch/local-lights-out-factory/contracts-legacy-replay-results.json)
retain the evidence. Each trial records its original fixture and worker profile.
Recreate it with `prepare_repository_trial.py --worker-profile PROFILE`, adding
`--test-followup` where recorded, then `build-feature` in a fresh output directory.
Raw ledgers and artifacts remain under `.gflo/evidence/<run>/`.

This resolves the observed algorithm-advice boundary and missing dependency context.
The repeat's unnecessary questions remain an unattended-planning reliability gap.
Future work must distinguish unanswered policy from questions already grounded in
requirements, while preserving real `needs-info` stops and unchanged acceptance gates.

## Question grounding and large-file probe, 2026-09-10

Structured planning now has one bounded review of proposed questions against original
requirements. Exact quotes, request/question identities and complete question coverage
are checked; source reads are disabled during review. Unresolved, invalid or repeated
questions retain `needs-info`. Covered questions can replan within the original budget.
Semantic coverage remains a model judgment; matching quotes only proves provenance.

A fresh modes build accepted. A targeted replay seeded the exact eight-question record
from the previous failure, then used the real local model for review, replanning and
workers. The final replay accepted implementation, generated tests and integration
after a planning coverage retry. No human answers, code edits or plan corrections were
provided. Two fixtures with genuinely unspecified retention/rounding policy stayed
`needs-info` in both reviewer iterations. Earlier failed replays remain recorded:
source-reading was still offered by the transport, then schema feedback was dropped
after successful review. Both defects were corrected and regression-tested.

[Feature runs](../.scratch/local-lights-out-factory/question-grounding-feature-results.json),
[missing-policy cases](../.scratch/local-lights-out-factory/question-grounding-ambiguity-results.json),
and [combined target tests](../.scratch/local-lights-out-factory/question-grounding-combined-results.json)
retain responses, assistance and outcomes. Seeded first observations are fixture replays,
not GPU calls or fresh planning successes. Final factory checks: **480 tests and 25
subtests** with Docker; ruff/mypy pass. All **28 target tests** pass together. Historical
accepted, halted and challenged results replay with unchanged outcomes and no new events.

The user's large-file concern was also measured: a 207,814-byte, 10,002-line Python
file was indexed successfully, and its target function read as a two-line excerpt.
The current coding projection still included the whole writable file and tokenized to
**128,684 tokens**, exceeding the 16,384-token deployment limit. No generation request
was sent. The [probe](../.scratch/local-lights-out-factory/large-file-context-results.json)
includes an exact source recipe. This establishes a concrete need for bounded edit
windows; it does not establish large-file coding capability. Full-file validation and
unseen-byte preservation must accompany that next protocol.

## Bounded source-window worker (2026-09-10)

The opt-in windows-v1 profile passed a 10,002-line / 207,814-byte function edit and a
568-line repository.py argument-validation edit on the same pinned local deployment.
Maximum prompts were 3,276 and 4,814 tokens respectively; the prior whole-file large
fixture required 128,684 tokens and was refused. Each accepted run used one attempt and
three responses: read, edit, then repair after an integer-subclass test failed. Complete
candidate checks verified behavior and preservation; accepted replay added no events.

Codex wrote the tasks/gates and generic protocol. Initial fixtures had an incomplete
subclass check, a missing dependency, a cross-runtime AST comparison, and an erroneous
newline correction. Those failures remain recorded; the incomplete acceptance has a
finding. No manual candidate edits or model changes were used. The real-file candidate
remains a qualification artifact. [Portable responses, recipes and outcomes](../.scratch/local-lights-out-factory/window-qualification/README.md)
show the assistance and failures. Large-file planning and execution above 256 KiB remain
unqualified; this is not evidence of unattended whole-product reliability.

## Window planning and full-feature trials (2026-09-10)

Direct planning now uses read-only windows with the opt-in windows-v1 profile. Across
four fresh supervised feature trials on the 10,002-line file, one accepted its local
plan, implementation, eight generated tests and combined checks. The tests rejected
three injected faults. That run used six responses total and at most 3,513 prompt
tokens; replay added no events. The other three runs halted: two on excessive test
output and one on repeated planning reads followed by an omitted requirement.

The trials span generic protocol changes, so this is not a fixed-configuration success
rate. The final configuration has not repeated the complete success. A separate
navigation probe eventually quoted the actual return statement at line 5001, but used
five responses across two attempts. [Portable fixtures, responses and negative results](../.scratch/local-lights-out-factory/window-feature-qualification/README.md)
record all assistance. No model or context-limit change and no manual candidate/plan
repair was used. CPU/Docker verification passed 492 tests and 25 subtests. The new
retryable output-limit classification is covered by CPU tests; the last GPU trial
halted before reaching it. Test-task decomposition and navigation recovery are the next
experiments, not demonstrated solutions. Execution remains capped at 256 KiB.


## One test worker versus two behavior-scoped workers (2026-09-10)

Three frozen pairs used the same accepted large-file implementation, model, requirements
and aggregate six-response ceiling. Reviewed groups isolated test generation from
planning. Both approaches initially passed 2/3; split workers used 30,807 total tokens
versus 20,128 for one worker, about 53% more. One solo trial failed to repair a syntax
error using the window protocol; one split trial exceeded its output allowance.

Post-run review found a split values contribution missing its assigned default test,
although the types worker incidentally covered it in the combined suite. A held-out
mutant confirmed the gap; a retained finding now blocks reuse. Other audited accepted
contributions passed their applicable checks. Current reusable outcomes are 2/3 solo
and 1/3 split. No candidates were manually repaired or failed trials replaced.
[Portable plans, responses, generated tests, costs and findings](../.scratch/local-lights-out-factory/test-decomposition/README.md)
retain all results. Separate files worked through the existing sequential scheduler;
no shared-file editing or runtime/prompt change was needed. The small supervised sample
supports selective decomposition, not a general claim that either approach is superior.


## Planner recovery and controller-owned identity (2026-09-10)

The final fixed campaign produced valid plans in 6/6 fresh runs, all within the first
attempt using two turns. Three navigation probes correctly quoted the function at line
5001; two of three full features also passed workers, tests and integration. The third
failed a worker source-preservation gate. Accepted replay added no work.

Changes retain read context across retries, give precise validation feedback within
remaining turns and let the controller supply an omitted request identity. Explicit
wrong identities still fail. An intermediate campaign's navigation runs exhausted their
budgets while copying invalid hashes; those failures remain in [portable evidence](../.scratch/local-lights-out-factory/planner-recovery/README.md).
No model, gate, context or attempt-budget expansion was used. Full Docker regression
passed 497 tests/25 subtests, with an additional retention case verified separately.
These small supervised samples show a planner improvement, not general unattended
reliability. More local inference is acceptable when it improves checked completion;
token use remains a secondary measurement for future specialist-budget comparisons.

## Task-created draft repair (2026-09-10)

The previously rejected whole-file repair of a task-created test file passes all original
fault checks unchanged. Three fresh local-model solo trials accepted, including one
two-response draft repair. Original input files remain protected by exact window edits.
These small trials verify the regression, not general reliability.
[Portable evidence](../.scratch/local-lights-out-factory/draft-repair/README.md).

## Full per-worker retries and integration provenance (2026-09-10)

New v2 integration records cover every feature requirement and accepted contribution,
without inheriting a worker's tools. Explicit v1 policies and plans preserve replay.
503 tests and 25 subtests pass, including both version paths; four historical campaigns
replayed with zero new events.

Six frozen same-model trials gave every worker two attempts of three turns. Solo
accepted 3/3; two specialists accepted 2/3 despite twice the aggregate response allowance.
The value specialist in the failed trial invented behavior contrary to the actual code
and exhausted both attempts. Checks caught it. Default coverage was required by the
pinned gates, and all five accepted features passed assigned/combined default and
held-out subclass audits. Accepted replay added no events. No manual candidate fixes.

Actual tokens were 14,348 for solo and 50,844 for split; reliability is the primary
comparison. This small sample demonstrates no specialist advantage on this workload,
not a general ranking. [Full results and retained failure](../.scratch/local-lights-out-factory/full-worker-budgets/README.md).

## Stateful SQLite repair and failure-local windows (2026-09-10)

The factory repaired ai-gamer's move-batch transaction leak and generated five real
SQLite tests. The first accepted candidate was merged in
[ai-gamer PR 2](https://github.com/gradrix/ai-gamer/pull/2) without manual code correction.
Independent checks cover atomic insertion, rollback while locked, prior committed rows,
subsequent writes, indices/dates, and a held-out deferred failure at commit. All 22 new
and existing winner tests pass, 87 original files are preserved, and replay adds no work.

The first three full builds failed their generated tests, despite accepted implementations.
Their repair turns lacked source windows from the task-created tests. The window worker
now selects up to two failure locations from current readable drafts under its existing
byte/turn/permission limits. Five new regressions and the full factory suite pass:
508 tests and 25 subtests; four historical replays remain unchanged.

Three fresh builds with identical requests and policies accepted one. The remaining
workers continued incorrect SQLite or index assumptions even with source windows and
failure diagnostics. The accepted test worker passed its first candidate, so this small
comparison does not establish that automatic repair context caused better completion.
Model, deployment and retry budgets were unchanged. Supervised task/validator preparation,
failed preflights, every model response and both campaigns are retained in the
[portable qualification](../.scratch/local-lights-out-factory/atomic-moves/README.md).

## Bounded reasoning windows (2026-09-10)

A frozen comparison used the same model, source, independent gates, two attempts,
three turns per attempt, and 16,384 total / 6,144 output tokens in both conditions.
Low reasoning accepted 1/3 complete SQLite features versus 0/3 non-reasoning;
both accepted 0/2 retained-draft repairs. The accepted feature passed independent
commit-failure recovery and replay without new events. All requests passed the
wire-settings/budget audit. Control spent 170,118 tokens / 284.49 model seconds;
reasoning spent 142,726 / 764.37. Earlier reasoning halts explain its lower total
input/output token use; completion tokens were 45,165 versus 15,759.

Two reasoning test workers consumed their output allowance entirely in reasoning,
returning null content that bypassed the decoder's bounded truncation-retry path.
The narrow recovery fix was tested in two fresh unchanged-plan follow-ups: both
reached bounded retry, but neither completed the feature. One exhausted retries on
invented helper signatures; the other on another truncation. They used 13 responses,
109,344 tokens and 593.50 model seconds; wire/budget audits passed. No default
profile upgrade or general reliability ranking follows from this sample.
[Portable plans, drafts and all outcomes](../.scratch/local-lights-out-factory/window-reasoning/README.md).

## Repair definition visibility (2026-09-12)

An audit of seven retained generation requests found the failing helper definitions
were indexed by name/location but never requested or shown. Failure-local windows
showed the caller. A CPU reproduction through the real window projector fails an
assertion that the failed callee is visible; an experimental revision-bound lookup
supplies it with 594 additional source bytes within existing bounds. The subsequent
bad helper call remains ungrounded. Authority, ambiguity, incomplete-index and stale
source checks pass. This investigation changes no runtime policy and spends no model
responses: improved visibility is established, improved repair completion is not.
[Portable audit and CPU reproduction](../.scratch/local-lights-out-factory/definition-grounding/README.md).

## Live failed-call definition context (2026-09-12)

The new opt-in definition-context profile completed 1/2 frozen full features versus
0/2 existing low reasoning, with 0/1 retained repairs in both conditions. The accepted
feature passed held-out commit recovery and unchanged replay, but used no hints.
The retained repair received the actual failed helper definition twice and still
exhausted edit-protocol/output recovery. A generated constructor lookup was reported
missing. This establishes live bounded source delivery, not improved repair completion.
All 35 responses passed wire/budget audits; all six terminal states and four older
accepted/halted/challenged histories replayed without new events. Keep the profile
opt-in. [Frozen results and limitations](../.scratch/local-lights-out-factory/definition-qualification/README.md).
