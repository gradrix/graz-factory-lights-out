# GFLO handoff — qualification exposed semantic-gate limits

## Documentation and next workload — 2026-09-08

Public navigation is now README.md → docs/getting-started.md, architecture.md,
operations.md, evaluation.md, and roadmap.md. CONTRIBUTING.md covers development.
The next proposed workload is a stateful inventory/reservation application; the
roadmap defines semantic prerequisites, a three-module slice, and ten prepared
changes in dependency waves. This turn planned that workload; it did not execute it.

Clean public snapshot verification: pinned install, prepared-demo submission,
245 tests + 25 subtests passed, eight optional Docker tests skipped; ruff, mypy,
and all public Markdown links passed. GPU onboarding was not rerun this turn.

Old public component guides and the former glossary are preserved in
`documentation-archive-2026-09-08/`. The initial removal of `.scratch/` from Git
tracking was reversed to preserve cross-machine development. Commit new handoff,
issue, research, and source files together; untracked files will not travel with
a clone. Raw `.gflo/` evidence and model caches need separate transfer or recreation.
Existing Git commits still contain the old files. Do not publish history without
review. Public release remains pending owner license choice, history/source review,
fresh-host GPU onboarding, and an audited historical evidence bundle.


## Current checkpoint — 2026-09-08

The user authorized continuing implementation and verification until meaningful questions
arise. Planning is already recorded in [the map](map.md); no new Wayfinder pass is needed
to resume the current implementation work. No commits or pushes were made in this run.
The working tree includes earlier untracked runtime files; preserve that work.

**Read [the completed evaluation](heldout-results.md) before expanding scope.** Forty
small Python tasks ran three fresh repetitions: 111 original gate acceptances, 109 verified
by the campaign checks, nine exhausted runs, two discovered false acceptances. Numerical
targets passed; the zero-false-acceptance criterion failed. Larger-build feasibility is
not established. The historical checkpoint narrative is [archived](handoff-history-2026-09-08.md).

## Implemented and verified

- Durable prepared-task ledger, immutable artifacts, fenced Attempts, Docker broker,
  independent process gates, bounded local-model turns, retries/resume, cumulative costs
  and worker candidate diffs.
- Prepared integration of accepted disjoint edits from one exact base. Pinned provider
  contracts, stale-input rejection and independent combined gates. The live provider/two-
  consumer fixture passed first attempt for every child and produced combined outputs
  42 and 84. [Task 24](issues/24-validate-prepared-integration.md).
- Context policy `bounded-python-v4`: bounded verified contract excerpts plus readable
  observed validation feedback. Three matched seen-failure pairs repaired 3/3 with readable
  feedback versus 1/3 with legacy feedback. [Task 25](issues/25-improve-bounded-validation-feedback.md).
- Acceptance findings append contradictory evidence while preserving original acceptance.
  Replay/integration reuse is blocked. Status/history expose the challenge. Ledgers with
  findings require reader version 3; stop older open controllers before upgrading.
  The two actual campaign findings are recorded and blocked.
- Latest full enabled suite: **253 tests + 25 subtests, no skips**. Ruff and mypy pass.
  Evidence: `.gflo/evidence/factory-final-v1/suite.xml`.

## Important retained evidence

- `.gflo/evidence/heldout-v1-qualified/`: frozen manifests, all 120 results and costs,
  semantic probes prepared before scoring, full semantic review, evaluation, findings.
- Its `frozen-ledger/` and `runtime-source/` preserve the pre-finding ledger/artifacts and
  the exact scoring implementation. Do not overwrite or describe seen tasks as fresh.
- `.gflo/evidence/prepared-integration-live-v1/`: actual local-model integration fixture.
- `.gflo/evidence/feedback-recovery-v1/`: three paired seen bracket-repair comparisons.
- `.gflo/evidence/dedupe-regression-v1/` and `version-sort-regression-v1/`: strengthened
  gates reject retained bad candidates and accept known-good references.
- `.gflo/evidence/semantic-repairs-v1/`: deduplication repaired on Attempt 2; version
  sorting exhausted ten attempts. `version-sort-clarified-v1/` is a separately counted
  replacement with a public tie example and extra private gate; all three attempts failed.
- [Integrity coverage](integrity-coverage.md): all fifty original rows have scoped
  accumulated evidence, not a newly scored same-build fifty-case campaign. Precise
  live tokenizer injection is a client boundary, not proof of kernel execution overlap.

## Current limitation and next work

Tasks [22](issues/22-expand-integrity-and-recovery-campaign.md) and
[26](issues/26-strengthen-semantic-gates.md) remain claimed. Stronger gates now detect the
observed bugs, but persistent version-sort repair remains a real model/worker limitation.
It repeatedly ignores zero-padding and stable-tie requirements, even with one public
counterexample. Preserve exhausted attempts and separate replacement costs. Do not add
blind retries, manually replace generated candidates, or erase Acceptance findings.

Next bounded work is diagnosis of semantic repair (including a prospectively declared
reasoning/profile comparison if appropriate), clearer public input/output contracts,
and broader gate qualification before fresh held-out scoring. Prepared integration
accepts immutable artifacts; Git promotion, automatic graph planning, cross-ledger finding
propagation and already-exported product revocation are not implemented.

The user was asked which real product/repository should shape the next integrated-build
workload, with a small Python reference application as the suggested default. No answer
has arrived. Product planning can proceed separately; it must not bypass failed qualification.

## Runtime and commands

`gflo-vllm-graphs` remains running at loopback port 30000, model `gflo-local`, using
`infra/serving/vllm-5090-graphs.example.json`: pinned Inferact/Qwen3.8-27B-NVFP4,
RTX 5090, 16K server context, graph execution, one sequence. The older eager container
is stopped. All campaign/follow-up harness processes have finished.

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check gflo
.venv/bin/mypy gflo
.venv/bin/python -m gflo --db .gflo/evidence/heldout-v1-qualified/ledger.db history heldout-v1-r1-dedupe-last
```

Enable real broker tests with the pinned `GFLO_BROKER_TEST_IMAGE` from `gflo/pilot.py`.
Campaigns declared a 256 MiB storage admission reserve; ordinary development still
uses the documented zero default. [Integration](../../docs/integration.md),
[findings](../../docs/acceptance-findings.md), [feedback](../../docs/validation-feedback.md).
