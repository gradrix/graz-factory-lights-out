# GFLO handoff — repository access foundation

## Current checkpoint — development repair and verified data, 2026-09-10

Owner requested every repair option EXCEPT changing the model. Keep current weights,
serving deployment and GPU configuration. Issue 45 complete: opt-in repair protocol
on the same model, sandbox development checks, exact edits for existing files,
read-only verified examples, and review packets for exhausted work. Default plain
worker and historical plan digests are preserved. Existing budgets remain finite.

Final local repair passed in one response: 6212 prompt + 1695 output tokens, 28.80s.
Twenty generated tests pass; four assertions fail on original; two potential mutants
are rejected. Runtime instrumentation verifies all four winning directions on
non-square boards, and original winner oracle passes. Ninety-one other files stayed
identical. Replay adds no worker observations. No further ai-gamer edits were pushed:
its earlier product fix remains merged; these are factory qualification artifacts.

Important limits: repair-only trial halted after three accepted tasks; assisted
planner produced malformed JSON twice, so Codex adapted a reviewed plan. Initial
assisted gate acceptance missed non-square coverage; immutable finding blocks reuse.
First correction attempt set truncated twice. Final protocol requires existing-file
edits (16 replacements, 8192 bytes total), and that fresh correction trial passed.
Do not erase failures or claim unattended planning from this supervised success.

[Results](development-repair-results.json) retain all stages.
[Repair fixture](ai-gamer-repair-fixture.json),
[verified data / reviewed plan](ai-gamer-verified-examples-fixture.json), and
[coverage correction](ai-gamer-coverage-repair-fixture.json) are portable. The helper
supports `--test-followup --reviewed-plan`; the coverage fixture is the final passing
trial input. Raw evidence: `.gflo/evidence/ai-gamer-small-repair-v1/` (final),
`ai-gamer-coverage-repair-v1/` (truncated), `ai-gamer-verified-examples-v2/` (finding),
and `ai-gamer-repair-v1/` (initial failure). Use original baseline checkout at
`.gflo/targets/ai-gamer-baseline` or clone pinned revision on another machine.

Next qualification should keep the same model, freeze domain checks before scoring,
and distinguish reviewed planning/data assistance from autonomous discovery. Planning
JSON reliability and adequacy of generated-test coverage remain limitations. The new
human-review route retains contracts/drafts/evidence; it does not reset quarantine or
silently change models. Push/merge authorization persists. License choice remains a
separate supported-release decision.


## Previous checkpoint — bounded test-generation limit, 2026-09-10

ai-gamer [PR 1](https://github.com/gradrix/ai-gamer/pull/1) is merged at
9a0a4384b9b727c02f0f2c168c7abc43a4e076bf. Local implementation unchanged;
Codex wrote the merged tests. Seventeen cases pass, eight genuine assertions fail
on the original, and no other baseline errors occur. Independent winner oracle passes.

Issue 43 now exposes remaining turns and actual output allowance in tokenized worker
instructions. 412 factory tests and 25 subtests passed with Docker enabled. Same-policy
follow-up produced two candidates but failed semantics. Issue 44 then split tests
into four files: gaps and anti-diagonals passed first try; potential failed with a
winning draw fixture then truncated; rectangles never ran. No integration acceptance.
See [budget results](worker-turn-budget-results.json),
[split results](ai-gamer-split-tests-results.json), and
[split fixture](ai-gamer-split-tests-fixture.json). Both issues are resolved as measured
experiments, not as a claim that test-generation reliability is solved.

**Current qualification blocker:** the pinned worker cannot reliably repair generated
semantic test fixtures within these finite budgets, even after decomposition. Do not
present the merged product fix as unattended end-to-end success. Future work should
prospectively compare a smaller repair representation or another qualified worker
profile on the same failing case; preserve failures, budget totals and independent
checks. Correct-board injection would be a different, more supervised task.
No owner decision was needed for the delivered work. License choice remains separate.
Raw evidence: `.gflo/evidence/ai-gamer-turn-budget-v1/` and
`.gflo/evidence/ai-gamer-split-tests-v1/`. Portable helper with `--test-followup`
reconstructs the new split request/source from the pinned baseline clone.


## Previous checkpoint — real ai-gamer qualification, 2026-09-10

Owner delegated target/task choice and reaffirmed continuing until actual blockers.
Chose ai-gamer rule correctness; [merged PR 1](https://github.com/gradrix/ai-gamer/pull/1)
contains unchanged local-LLM implementation and 17 Codex-authored regression cases.
Oracle passed all 19,683 3x3 boards plus larger-board probes; new tests reject original.
All 86 other original files preserved. Issues 40–42 resolved; 410 factory tests and
25 subtests passed with Docker enabled; ruff/mypy passed.

**No end-to-end autonomous success:** initial plain implementation failed; reasoning
4K output truncated; low reasoning 6K repaired implementation but test generation
quarantined. Separate plain tests also failed/truncated/exhausted reads. Reviewer
finished tests directly. Original task/oracle were prepared and gate feedback exposes
reference code. See [results](ai-gamer-winners-results.json) and
[fixture](ai-gamer-winners-fixture.json). Raw evidence is ignored under
`.gflo/evidence/ai-gamer-winners-v1/`; target checkout `.gflo/targets/ai-gamer`.
The portable helper reconstructs original or `--test-followup` snapshots from a
pinned clone without executing target code. Existing legacy tests have stale imports;
training/server/dashboard remain unqualified.

Factory fixes: snapshot capture preserves opaque blobs; text selections still reject
them. Policy planning stays plain while workers retain their selected profile.
Standalone low-reasoning profile is explicit, not a changed default. Next actionable
work: diagnose read/turn exhaustion before broadening product tasks. Push permission
persists; license selection remains separate from engineering progress.


## Previous checkpoint — unfamiliar feature and replay qualification, 2026-09-10

Issues 38/39 complete. Recursive settings feature passed three fresh builds, nine
tasks in nine attempts, plus independent final gates. Planning used 1/2/2 calls;
failed initial proposals remain recorded. Each build preserved 60 archive files and
the existing decoder. Prepared exact-definition queries selected the four execution
files; no model-driven navigation is claimed. See [results](navigation-feature-results.json)
and [portable fixture](navigation-feature-fixture.json). The existing preparation
script reconstructed the exact snapshot in a fresh ledger.

Portability checks caught JSON mapping order changing required-gate list order under
one policy digest. New lists are deterministic. Replay preserves old order only when
all gate specifications and every other WorkAtom field match. Four regressions, all
three new ledgers and both prior board-comparison ledgers replayed without model calls.
Full Docker-enabled suite: 406 passed, 25 subtests, no skips; ruff/mypy passed.

Owner asked to continue until a blocker or human decision. Asked which real repository
and concrete feature should be the first larger-product qualification target; no target
was previously selected. That determines languages, dependency setup, build workload,
and useful dependency-navigation work. Continue with their answer; do not invent a
production target or claim scaffold trials establish million-line support. License
choice remains separately open for a supported public release. All raw evidence stays
ignored under `.gflo/evidence/`; tracked portable records are enough to resume planning.


## Previous checkpoint — memory qualification, 2026-09-10

Issue 30 is resolved after exact reproduction and kernel confirmation: Docker's OOM
flag remained false despite same-container max/oom/oom_kill increments. Qualification
now uses a trusted supervisor and killed allocator child, requiring local kernel
counter increases and clean completion. Limits unchanged; exit 137 alone never passes.
All 100 prospective full qualifications passed; real unrelated kills/no-allocation
failed as required. Full suite with Docker enabled: 402 passed, 25 subtests, no skips.
[Portable evidence](memory-qualification-results.json) retains all failed baselines.

Issue 38 is now running a new recursive-settings feature with 60 archive decoys,
definition-derived explicit context, fixed independent recursive/alias/invalid-value
checks, and the existing policy build. Do not treat prepared symbol selection as
model-driven navigation. Owner requests continued work until actual blockers or
human decisions; push authorization remains active.


## Previous checkpoint — Python definition navigation, 2026-09-10

Issue 37 adds snapshot-bound Python definition shards/indexes and CLI navigation,
with exact source/scope/analyzer binding, explicit skipped-file/truncation coverage,
and reuse of unchanged same-path analysis. This does not resolve callers or provide
automatic model context selection. Real GFLO core: 27 files parsed in 0.332 s, all
27 reused in 0.007 s; five definition/source-read probes passed. See
[results](symbol-navigation-results.json) and [guide](../../docs/product-intake.md).
Validation: 384 passed, eight optional Docker skips, 25 subtests; ruff/mypy passed.

Owner requested continued engineering until a real blocker or human decision.
Next in progress: reproduce and diagnose issue 30 before broader live feature trials.
The original full qualification failed on repetition 14; memory-only reproduction
failed on repetition 35 with exit 137/OOMKilled false. No enforcement was relaxed.
Raw diagnosis work is under `.gflo/evidence/memory-qualification-v1/`.


## Previous checkpoint — policy build handoff, 2026-09-10

Issue 36 closes manual task-review assembly for policy-covered features.
`build-feature` accepts an exact request-bound FeaturePolicy: file checks, integration
checks, bounded inputs, environment/model, and maximum budget. It uses single planning,
compiles the task graph deterministically and runs existing reviewed progression.
Model acceptance prose never selects commands or relaxes policy. Repeating the same
build reuses planning and replays accepted execution; changed bindings reject.
Interrupted/exhausted planning needs a new output directory, not a hidden retry.

Actual local-model checkout trial: initial planning response missing fields, second
attempt valid; all three worker tasks accepted in one attempt each and final checks
passed. Replay added no recorded model calls. Missing rounding policy returned two
questions in one call and started no workers. See [results](policy-build-results.json),
[fixture](policy-build-fixture.json), and [guide](../../docs/product-intake.md).
`scripts/prepare_policy_trial.py` reconstructs the exact fixture source/policy in a
fresh ledger. Raw receipts remain ignored in `.gflo/evidence/policy-build-v1/`.

Validation: 375 tests passed, eight optional Docker skips, 25 subtests; ruff/mypy.
This qualifies the handoff on a seen product; it is not unfamiliar navigation or
self-authored independent checks. The owner clarified to prioritize necessary work,
not autonomy for its own sake. Next: broader product and context-selection trials,
revision-bound symbol lookup, and issue 30 memory qualification. No recursive
organization, automatic environment provisioning, Git promotion, or large-build
claim was added. Single planning stays default. Push authorization remains active.


## Previous checkpoint — optional specialist board, 2026-09-10

Issue 35 implemented `plan-feature --board`: bounded independent specialist reports,
exact synthesis references/dispositions, and immediate clarification on any specialist
question/blocker. This is optional planning policy above the existing core; execution,
independent review/gates, and recovery are unchanged. It follows the original decision
to borrow SFLO/Gas City contracts without adopting their runtimes.

Both single and board plans passed all three tasks on an unfamiliar checkout feature.
Board planning cost 29,628 versus 8,294 tokens; no additional quality benefit was shown.
Single stays default. Initial protocol/advice-limit failures and the board ambiguity
synthesis failure remain recorded. A later early-blocker live probe returned questions
in one call. See [results](board-comparison-results.json),
[fixture](board-comparison-fixture.json), and [evaluation](../../docs/evaluation.md).
Raw evidence is ignored under `.gflo/evidence/board-comparison-v1/`.

Validation: 360 tests, eight optional Docker skips, 25 subtests; ruff/mypy passed.
Next: repeated varied product and navigation/selection trials, then revision-bound
symbol lookup and larger isolated builds. No recursive management or million-line
qualification is claimed. Issue 30 memory qualification remains open; no enforcement
was weakened. License selection remains an owner decision for a supported release.


## Previous checkpoint — reviewed feature progression, 2026-09-10

Owner asked to continue implementation and test whether the local model can handle
manager responsibility. Implemented `gflo.progression`/`run-feature`: sequential
reviewed DAG execution, exact accepted-base snapshots, retained predecessor evidence,
findings rechecked before direct consumer execution/reuse, independent final gates,
and replay from immutable records. No Git/workspace promotion occurs. `prepare-task`
stays root-only; internal progression preserves dependencies and original plan/review
bindings. New snapshot provenance profile does not weaken legacy worker restrictions.

`plan-feature`/`check-plan` now support RepositoryFeatureRequest with explicit bounded
source selection. Planning v3 supports PlanQuestions (`needs-info`) without invented
tasks, bounded read history and explicit output envelope. Missing paths may be supplied
by declared ancestors but must exist at consumer preparation. Questioned plans cannot
execute. Snapshot request import remains compatible through gflo.preparation.

Live evidence: original four-task expense plan executed three times, 12 accepted tasks
in 12 attempts; each build passed independent combined gates including 25 generated
valid inputs and five invalid inputs. Replay made no new model calls; omitted archive
bytes survived. Updated planner's three-task plan also passed one full execution.
Ambiguous currency/month request initially exhausted six rereads; clarification v3
first produced malformed outer envelopes, then explicit wrapper wording yielded
blocking product questions in one turn. Preserve all failures as separate observations.
See [results](feature-progression-results.json), [portable fixture](feature-progression-fixture.json),
and [product intake](../../docs/product-intake.md). `scripts/prepare_feature_trial.py`
reconstructed the exact fixture snapshot in a fresh output directory without model
or source execution. Raw receipts/model exchanges remain ignored in
`.gflo/evidence/feature-progression-v1/` and need separate transfer.

Validation: 353 tests passed, eight optional Docker skips, 25 subtests; ruff/mypy
passed. Original 120-run and earlier campaign scores/findings are unchanged.
This qualifies one scaffolded product and a narrow ambiguity probe, not general CEO
or recursive-manager ability. Next: varied product/interface ambiguity and navigation
selection trials with explicit success targets; then revision-bound symbol indexing,
larger isolated builds, and hierarchical budgets where evidence justifies them.
No human decision currently blocks those engineering qualifications. Push/merge
authorization remains active; license/public supported-release decisions remain open.

## Previous checkpoint — reviewed snapshot root tasks, 2026-09-10


`gflo/preparation.py` and `gflo prepare-task` bridge RepositoryFeatureRequest +
PlanProposal + controller-authored PlanReview to PreparedTask/legacy RunPlan.
Reviews bind exact request/proposal digests and provide context/execution paths,
ProcessGates, model/deployment, and budgets. Full snapshot identity is bound in the
new run's source revision. Legacy schemas are unchanged. Only independent root
tasks prepare; dependent tasks reject until accepted-base progression exists.
Preparation publishes artifacts without submitting/running. Candidate lifting
produces a proposed snapshot, not acceptance or promotion.

16 new tests; full suite 337 passed, eight optional skips, 25 subtests. Ruff/mypy
passed. Docker fixture matched correct output and rejected faulty output:
360,033-byte repository, 75-byte execution source, omitted file identity preserved.
No LLM was exercised. See [results](preparation-results.json) and
[product intake](../../docs/product-intake.md). Legacy plan-feature still uses
FeatureRequest bundles; snapshot-backed model drafting is not implemented.

Next: accepted-base progression with acceptance/finding checks and independent
combined gates, then repeated multi-task feature trials. Do not prepare consumers
by deleting dependencies or relabeling unaccepted candidate snapshots. Recursive
managers, automated intake/environment setup, larger builds, indexing, and million-
line work remain unqualified. No human decision blocks that engineering slice.
Owner push/merge authorization remains active.

## Previous checkpoint — repository access, 2026-09-10

Repository access first slice complete: `gflo/repository.py`, `repository_cli.py`,
and 21 tests. CLI captures immutable Git-visible dirty source, reads/searches/selects
within scope and budgets, and applies digest-bound edits preserving omitted files.
Legacy bundle identities remain unchanged. See [results](repository-access-results.json).
Actual GFLO capture: 193 files / 1,534,270 bytes; execution subset: 22 files /
237,538 serialized bytes. Untouched identities preserved. Host: 321 tests passed,
25 subtests, eight optional skips; Docker consumer subset: 14 passed. Initial Docker
capture tests failed because its pinned image lacks Git; retain that evidence.
No LLM was exercised by this source-infrastructure trial.

Next actionable slice: migrate reviewed-plan preparation to snapshot references and
explicit context/execution selections, with independently trusted gates and current
base checks. Existing `FeatureRequest`, `RunPlan`, and candidate construction still
use bundles. Do not enlarge broker limits or claim full-repository validation from
selected inputs. Symbol/dependency indexing remains future work. Capture requires a
quiescent worktree; edits verify all original bytes; no cross-store export or GC.

## Previous checkpoint — 2026-09-09

Owner authorized merging and pushing all completed work. History filter `091654a`
was merged into main at `0d30d48` and pushed. No further merge/push permission is
needed for this authorized work. GitHub repository is already PUBLIC; no license
selected. Keep the experimental-preview wording; a supported release is not ready.

Added `gflo plan-feature` and `gflo check-plan`. The model proposes tasks,
dependencies, interfaces, acceptance descriptions, and unresolved questions from
an immutable FeatureRequest. Trusted validation checks structural coverage, scope,
source references, environment catalog, dependency cycles, and overlapping writes.
A valid draft does NOT authorize execution or create trusted acceptance gates.

One live compact-summary feature trial produced four tasks (renderer, CLI, tests,
docs) with matching proposed interfaces and no blocking questions after iterative
improvements. Earlier failures exposed deployment artifact omission, context
accumulation, truncation, and excessive routine questions. All results retained.
Planning v2: 12K/4K non-thinking, two attempts × three turns, two-file reading window,
bounded AST interface index. Implementation-worker budgets are unchanged.
No implicit resume; existing output directories refused. Raw immutable observations
remain even when a run halts; summary files can be incomplete after process death.

Added `python3 scripts/setup.py`: creates/reuses a venv, installs pinned dependencies,
prepares/submits a demo, reports CPU/Docker readiness. `--check-only` does not install.
`--start-model` uses existing service doctor/up and pulls the pinned broker image;
model cache and NVIDIA/Docker host prerequisites still need provisioning. Clean
venv setup and repeat setup passed; the default path runs no model/worker code.

Verification: 300 passed, eight optional Docker skips, 25 subtests; ruff and mypy
passed. The previous history self-trial passed 279 tests per generated candidate
in Docker; previous stateful campaign passed three builds. Original failed campaign
scores and findings remain unchanged. Huge-system capability remains unqualified.

## Continue

- Owner requires a migration path to large repositories. [ADR 0001](../../docs/adr/0001-repository-snapshots-and-bounded-task-inputs.md)
  and [issue 32](issues/32-separate-repository-access-from-task-bundles.md) define
  repository snapshots, bounded context, and separate execution inputs. The first
  source-access slice is complete. Wire plan materialization through it next; preserve
  old digests. No index/graph capability is implemented.

- [Issue 30](issues/30-diagnose-memory-qualification-halts.md): reproduce intermittent
  exit-137/no-OOM-flag resource checks without weakening enforcement.
- Materialize reviewed plans into WorkAtoms with independently reviewed ProcessGates,
  pinned environment/source bindings, and dependency-aware accepted-base progression.
  Do not execute arbitrary commands or treat model-written tests as sole acceptance.
- Qualify generated test tasks against trusted reference and faulty implementations,
  then broaden planning trials beyond this seen feature.
- GPU/model-cache provisioning remains the main onboarding gap. License selection
  remains an owner decision before a supported release.

[Planning results](planning-trial-results.json), [self-trial results](self-history-trial-results.json),
and [stateful results](stateful-inventory-feedback-results.json) are portable.
Raw planning evidence: `.gflo/evidence/planning-trial-v1/`, final `run-v2-defaults-1`.
Requests and deployment/profile files are retained there; source hashes/proposals
are in portable results. Raw artifacts/images require separate transfer/recreation.
The isolated history checkout remains at `.gflo/self-trial-checkout` for reference.
Keep `.scratch/` version-controlled. Issues 29 and 31 resolved; 30 ready-for-agent.

Final validation: 423 tests and 25 subtests passed with Docker checks enabled;
ruff and mypy passed. The model weights and serving deployment were unchanged.
