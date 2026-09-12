# Failed-call definition context qualification

`vllm-python-worker-windows-definitions-low-v1` is a new opt-in profile. It retains
low reasoning and the existing exact-edit protocol while adding bounded navigation
from qualified Python TypeError names to definitions in the authorized current source.
No old profile, model, deployment, requirement or gate is changed.

The runtime considers at most four distinct qualified names and requests at most two
25-line definition windows. A complete revision-bound index must yield exactly one
hit. Missing names, ambiguous names, incomplete indexes, unavailable read authority
and exhausted hint budget are explicit. Admitted hints become shown or omitted
according to the ordinary source-window bounds. Hint names are not verified Python
receiver bindings; implicit/generated constructors are not resolved.

Priority is explicit reads, definition hints, failure locations, initial headers.
The existing eight-window, 12,000-source-byte and 4,096-byte-per-window limits apply.
Normal tokenizer admission reserves output before generation; hints grant no turns,
write authority or acceptance. The new profile retains the reasoning-only truncation
recovery path. Historical profiles do not receive the new metadata or reads.

## Frozen experiment

Six plans are prepared before inference: two paired complete SQLite features and one
paired repair of the exact failed helper-call test draft. Within each pair, only the
worker profile differs: existing low reasoning versus definition-context low reasoning.
The original requirements, independent gates and accepted provider bytes are pinned.
The portable `retained-source.json` is the actual previously failed draft with its
accepted provider, not a manually repaired candidate. Its source digest is
`d481738089b78045424211531f3116e6bfb47c73f5a88bae3c17a0f5de7d1b5e`.

Each worker gets two attempts, three turns per attempt and 16,384 total / 6,144
reserved output tokens. The six runs reserve 60 responses / 983,040 tokens in total.
Reference gate checks pass before inference; the retained failed draft fails its
unchanged test gate. No planner calls or reset historical attempts are involved.

`results.json` retains portable costs, outcomes, hint visibility, evidence identities,
held-out audit status and replay results. Full model/process records are under
ignored `.gflo/evidence/definition-context-v1/`; transfer those separately for forensic
replay. The script preserves failed outcomes. Acceptance is post-audited with the
independent deferred-commit recovery check; contradictory evidence blocks reuse.
Both accepted and halted states must replay without new events.

## Reproduce

Use the pinned checkout and model deployment from `../window-reasoning/README.md`.
The campaign refuses an existing output directory.

```sh
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/definition-qualification/campaign.py
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/definition-qualification/report.py
.venv/bin/pytest -q tests/test_definition_context.py tests/test_windows.py tests/test_symbols.py
```

CPU regressions cover the actual failed helper, generic names, multiple hints,
ambiguity, incomplete/missing definitions, prohibited paths, missing read authority,
current-source rebinding, read-only exact-edit rejection, and byte/count exhaustion
with explicit-read priority. The full suite passed 529 tests and 25 subtests with
Docker enabled; the subsequently added count-bound regression also passes. Lint and
typing pass. Four historical accepted/halted/challenged replays retain their states
without new events (`legacy-replay.json`).

Interpret a hint appearing separately from complete repair. A successful run that
never uses a hint does not establish a causal benefit from the bridge. This small
comparison cannot establish unattended project reliability or a default-profile upgrade.

## Results and decision

| Frozen work | Existing low reasoning | Definition-context low reasoning |
| --- | ---: | ---: |
| Complete features accepted | 0/2 | 1/2 |
| Retained repair accepted | 0/1 | 0/1 |
| Responses | 18 | 17 |
| Actual tokens | 160,318 | 155,327 |
| Model seconds | 860.54 | 873.68 |

The accepted feature passed its independent deferred-commit audit and replay. All six
terminal states replay unchanged. Wire evidence verifies matched tokenization/generation,
low reasoning, 6,144 output reservation and 16,384 total ceiling for all 35 responses.
The largest prompt was 8,142 tokens, leaving the reviewed output reservation intact.

The accepted definition-context feature used no hints. A failed feature reported
Move.__init__ missing because the index contains no explicit generated constructor.
The retained definition-context repair received RecorderDb.createPlayer's real source
twice, proving that the bridge supplies previously absent context in live inference.
It still failed: first-attempt output tried whole-file replacement for an immutable
input, and the second attempt exhausted its output allowance. The retained control
also failed truncation and exact-edit protocol checks. No partial edits were accepted,
candidate manually repaired, or retry budget reset.

Keep this capability opt-in. These outcomes do not demonstrate improved repair
completion or justify a new default. Proceed to a complete small-project trial with
the established non-reasoning window profile. Reliability remains the priority;
the decision is based on missing evidence of improvement, not token savings.
