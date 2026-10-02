# First local pilot — 2026-10-01

## Outcome

The new factory executes bounded tasks locally, preserves their source repositories, retains failure evidence and produces reviewable patches. Three realistic fixture projects completed on MONSTER-GAMING-PC with Flash Coder configured for 131072 context and Q4 KV. **Two initially check-passing patches needed independent review corrections.** This is a useful first task runner, not qualification for unattended large-project integration.

| Scenario | Initial run | Review outcome | Local-model follow-up | Total run wall time |
|---|---:|---|---:|---:|
| Fix invoice decimal money handling | 72 s, 1 attempt | Missing CSV value/header handling and quoted-name preservation needed correction | 83 s + 34 s | 188 s |
| Add atomic SQLite inventory reservations | 97 s, 1 attempt | Unnecessary SQL padding and a tautological condition rejected | 47 s | 144 s |
| Build a JSONL log-summary CLI | 101 s, 1 attempt | Focused semantic review passed | None | 101 s |

Times are sums of measured factory-run wall times, excluding setup, human/independent review time and earlier exploratory runs. Follow-ups are separate immutable runs whose tasks link the reviewed run; the rejected artifacts were preserved. The local model performed all generated-project repairs. No generated changes were merged into an existing project.

The log-summary worker also encountered a failed quality check during its initial attempt: a regression test tried writing a temporary fixture into the read-only source tree. It moved that fixture to temporary storage, passed the check and then passed the controller's final verification.

Initial final checks ran 4 operator invoice tests plus 17 generated regressions; 2 inventory tests (including concurrent processes) plus 11 regressions; and 3 log-summary tests plus 8 regressions. Invoice acceptance was subsequently strengthened with missing-value, missing-header and exact quoted-name probes. The original unfixed inputs fail their acceptance checks.

## What the experiments exposed

An earlier invoice exploration produced regression methods without `test_` prefixes. Unittest reported zero tests and exited successfully. It also left scratch CSVs. The example quality gate now requires at least three discovered tests, documentation and no scratch artifacts; a controlled factory test proves both rejections against a passing control.

Passing functional tests did not catch the inventory model adding 400 redundant `AND 1` predicates to an already atomic UPDATE. Independent review rejected that complexity. The model removed it and retained the guarded update and affected-row result. Invoice's omitted edge cases were turned into executable checks and repaired. These findings justify a future independent local patch-review assignment before considering automatic integration.

The review stage in this pilot was performed by the development assistant and an independent checker. **A second autonomous local-model reviewer is not implemented in the released runtime.** Runtime status `accepted` means the frozen executable checks passed; broader semantic approval is separate. The default deliverable is a patch for review.

## Runtime evidence

- **23 maintained tests pass locally and on the rig.** They cover failure-to-repair, budget exhaustion, frozen acceptance, source preservation, CLI, offline Docker execution, read-only verification, timeouts and zero-test rejection.
- **Coverage: 92.9% of statements, 79.8% of branches, 90.1% combined.** The Makefile gate requires at least 85% combined. Remaining gaps include defensive filesystem validation, uncommon CLI error paths, some cleanup/output-limit paths and the long scheduling deadline. Coverage covers `gflo/`, not the serving launcher, model internals or Windows startup.
- Independent process-death probes found and then verified repairs for an early attempt-directory crash, stale accepted artifacts and orphan-container cleanup before recovery observation. Patch application and model-independent CLI status passed.
- The original vLLM rollback passed eleven checks, including original identities and an authenticated generation. Flash was then restored as the active service. Deployed runtime file hashes match the checked local candidate.

## Model and context limits

The installed profile measured **95.35 tokens/s** on the last two of three short 256-token generations. This is warmed decoding throughput, not end-to-end task throughput or long-context speed.

The initial three on-rig tasks reached maximum prompts of **11809**, **14824** and **16928** tokens. They therefore qualify small tasks at the configured 128K capacity, not coding across a full 128K input. Earlier work exercised near-full retrieval on the exact Flash/Q4 profile; that remains retrieval evidence. No concurrency, cold Windows boot, large-project agent benchmark or universal model ranking is claimed.

The tested export is pruned Flash-Next GSQ-RCO Coder and uses host-mapped lookup data as well as GPU VRAM. Model, runtime and image are local and pinned. Prepared tasks need no cloud account or Internet access; the rig, WSL/Docker, local storage and electricity must remain available.

## Evidence and reproduction

[Published measurement receipt](evidence/first-pilot.json) records run IDs, timings, token counts, check outcomes, repair lineage and measured coverage. [Coverage output](evidence/coverage.txt) records the executed suite. Run `make test` and `make coverage` for the maintained runtime checks; use the README and examples to create fresh local-model trials.

Full prompts, private Git snapshots and historical development probes remain local operational evidence, outside version control. A clone includes the current source, tests, fixtures, measurements and documentation; it does not include private run databases or model weights. Repeated model trials can differ from the recorded runs.

The next increments are defined in the [autonomy roadmap](roadmap.md). The first pilot motivates independent local review before automatic integration.
