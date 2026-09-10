# Bounded reasoning with source windows

This qualification compares low-effort reasoning with non-reasoning on the same pinned
local model, deployment and source. Reliability and checked coverage are primary;
token use and latency are secondary. No existing profile or policy is silently upgraded.

## Explicit protocol

`vllm-python-worker-windows-reasoning-low-v1` uses the same window reads, exact edits,
task-created draft replacement, failure-local context and original requirement authority
as `vllm-python-worker-windows-v1`. Every worker turn requests `enable_thinking=true`
and `reasoning_effort=low`. Planning remains on the non-reasoning window profile.
Reasoning consumes the reviewed output reservation; it does not add attempts or turns.
Existing profiles and historical replay retain their meaning.

## Frozen comparison

Ten plans were persisted before inference. Three pairs execute the previously generated
and reviewed full-feature plans from atomic-moves-v4. Two pairs start from the unchanged
failed test drafts in atomic-moves-v2 trials 1/2, creating new repair work with those
files as immutable inputs. Old quarantined attempts are never reset. The repair task
may edit only tests; the accepted implementation and real schema remain read-only.
No planner calls are made in this controlled comparison.

Each pair differs only in worker profile. Both get 16,384 total / 6,144 output tokens,
two attempts and three turns per attempt. Full features reserve twelve responses;
repair tasks reserve six. The total finite campaign reservation is 1,572,864 tokens.
Source, original requirements and independent gates are unchanged. No SQLite-specific
prompt additions or manual candidate corrections are permitted.

The reference implementation and tests pass all frozen integration checks. Both
retained drafts fail their test gate before inference. Accepted outcomes are separately
audited with the held-out deferred-foreign-key commit failure, and replay must add no
work. Wire evidence must bind tokenization and generation to the same settings and
6144-token reservation. `schedule.json` and `preflight.json` retain preparation evidence.

## Reproduction

Use the pinned ai-gamer checkout documented in `../atomic-moves/README.md`, the same
provisioned local endpoint and pinned Docker image. From the factory root:

```sh
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/window-reasoning/campaign.py
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/window-reasoning/report.py
```

The campaign refuses an existing `.gflo/evidence/window-reasoning-v1` directory.
`frozen-features.json` and `retained-drafts.json` preserve all inputs needed from earlier
runs; the old raw databases are not required. All ten plan digests were reconstructed
from those portable fixtures and the pinned Git snapshot before publication. The
reference methods, validators and held-out check are reused from `../atomic-moves/`.
This is a small controlled experiment on one feature, not a general profile ranking.

## Frozen results

| Work | Non-reasoning | Low reasoning |
| --- | ---: | ---: |
| Full features | 0/3 accepted | 1/3 accepted |
| Retained draft repairs | 0/2 accepted | 0/2 accepted |
| Model responses | 25 | 17 |
| Total tokens | 170,118 | 142,726 |
| Completion tokens | 15,759 | 45,165 |
| Model seconds | 284.49 | 764.37 |

Every recorded tokenizer/generation pair passed the wire-settings and budget audit.
The one accepted feature passed the independent deferred-commit recovery audit;
accepted replay added no events. Reasoning text was actually returned by the endpoint.
The smaller reasoning total-token count reflects earlier halts, not greater efficiency.
Neither condition establishes reliable completion; the sample cannot rank profiles.
No model candidates were manually corrected.

Control feature 2/3 repeated a draft whose rollback happened outside the writer lock.
Other control failures included incorrect SQLite foreign-key assumptions and invented
constructor/helper signatures. Reasoning feature 2/3 reached accepted implementations
but their test workers consumed all 6144 output tokens in reasoning, returning
`finish_reason=length` with `content=null`. The decoder classified that as a protocol
failure before the existing bounded truncation-retry path. Issue 67 tracks the narrow
fix and fresh follow-ups; these ten original outcomes remain unchanged.

## Reasoning-only truncation follow-up

Issue 67 permits null content only for a length-terminated response on the new
reasoning window profile. It still validates token accounting, assistant role,
absence of native tools/refusal, and finite output/context budgets before issuing
the existing retryable truncation diagnostic. Partial output and reasoning are never
applied. Other profiles retain their previous response semantics.

`truncation.py` freezes the same feature-2/3 plan digests in fresh ledgers before
inference, with unchanged source, gates, model and reservations (393,216 total tokens).
It uses portable input fixtures and `schedule.json`; no old attempt is resumed/reset.
Run and export separately:

```sh
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/window-reasoning/truncation.py
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/window-reasoning/report.py \
  --campaign .gflo/evidence/window-reasoning-truncation-v1 \
  --output .scratch/local-lights-out-factory/window-reasoning/truncation-results.json
```

Both follow-ups halted (0/2 full features); both implementation workers accepted.
Feature 2 recovered from truncation, emitted tests, corrected an invented createPlayer
call, then exhausted its budget with an invented createGame signature. Feature 3
recovered once and exhausted its second attempt on another truncated response. All
three length responses took the accounted retry path, with no partial candidate
applied and no infrastructure halt. Total cost: 13 responses, 109,344 tokens and
593.50 model seconds. All wire/budget audits passed. No integrated candidate existed
for a held-out acceptance audit. This confirms protocol recovery, not improved feature
reliability. Issue 68 investigates definition grounding before proposing further changes.

Final verification: 515 factory tests plus 25 subtests, Ruff, typing of 34 modules and
four unchanged historical replays pass. Raw artifacts remain under ignored `.gflo/`;
portable fixtures, schedules and reports are tracked here.
