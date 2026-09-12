# Repair definition visibility investigation

The retained helper-signature failure is a source visibility gap, with a separate
model navigation failure. Both helper names were discoverable in every retained
definition index; neither helper definition was present in any actual generation
request. The worker never requested either definition. This investigation changes
no runtime profile, prompt, model, acceptance gate or historical run.

## Retained evidence

`audit.py` reads the immutable artifacts from
`.gflo/evidence/window-reasoning-truncation-v1/feature-2-reasoning/` and exports
`visibility.json`. Its seven entries retain request, view, manifest and source
digests. Five responses belong to the test worker and two to implementation;
report order is grouped by atom, not global execution chronology.

- `RecorderDb.createPlayer` is indexed at lines 53–65; `RecorderDb.createGame`
  at 81–100. Index entries contain names/ranges, not signatures or bodies.
- Initial provider windows cover lines 1–30. The only requested provider range
  is 116–175 (`addMoves`), once in each test-worker attempt.
- The first test-worker attempt truncates after the read. The second begins
  without that requested window and spends a turn reading it again. Neither
  attempt ever requested the helper definitions, so retention alone cannot supply them.
- The first complete draft calls `createPlayer("Alice", 1000, 1000, False)` and
  `createGame(1000, 3, "tick_tack_toe")`. Development feedback identifies the first
  bad call; automatic windows add caller lines 7–31, not the callee definition.
- On its last turn the worker changes the player calls to one argument and leaves
  the game call unchanged. Final validation fails on `RecorderDb.createGame()`
  taking one to two positional arguments rather than four. No further turn remains.
- The actual repair request contains neither `def createPlayer(` nor
  `def createGame(`, including in projected diagnostics. Raw diagnostic records
  contain validator command text; that is not equivalent to model-visible source.
- All manifests fit 16,384 total / 6,144 reserved output tokens. The repair prompt
  uses 7,388 tokens. No source-window omission is reported. The 64-entry definition
  listing is truncated, but both relevant entries survive: truncation does not
  explain their missing bodies.

## CPU reproduction and bounded bridge experiment

Run from the repository root; the probe needs no GPU, Docker or historical store:

```sh
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/definition-grounding/probe.py
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/definition-grounding/probe.py --bridge
```

The first command intentionally exits 1 with
`Failed callee definition absent from repair view`. The second exits 0. The portable
fixture retains the actual provider bytes and failed draft, plus a minimized
diagnostic containing the same path, line and qualified TypeError name. The probe
uses the real `window_view` with a minimal Work atom; it reproduces the visibility
symptom, not the full model run or execution of the failed tests.

| CPU condition | Windows | Source bytes | Failed callee visible | Next callee visible |
| --- | ---: | ---: | --- | --- |
| Existing caller-window behavior | 3 | 3,769 | No | No |
| Experimental qualified-name bridge | 4 | 4,363 | Yes | No |

The experiment treats the qualified TypeError name as a navigation hint, queries
the existing revision-bound symbol index, requires one hit with complete coverage,
checks it against authoritative source, and passes a bounded read to `window_view`.
It admits at most two hints with 25 lines each, retaining the existing eight-window
and 12,000-byte bounds. Read-only provider targets remain read-only; missing read
authority and prohibited paths reject. Generic renamed helpers work, while duplicate
names, incomplete indexing, missing symbols and excluded scope produce no hint.
Stale definition reads reject. This is a conservative feasibility experiment, not
a production resolver for Python dynamic dispatch or arbitrary exception formats.

The measured change supplies 594 bytes of previously absent source. It is not merely
rewording a prompt. It does not reveal the later bad call, prove correct use of the
new source, measure tokenizer fit after the addition, or demonstrate repair success.
No new model responses were spent and no candidate was manually corrected.

## Decision

A prospective, explicitly versioned runtime qualification is warranted. Do not alter
historical window profiles based on this CPU result. The next task must pin precedence
and omission reporting for automatic definition hints, exercise ambiguity and authority
boundaries, and compare fresh finite runs with unchanged requirements and independent
gates. Preserve the sequential-helper failure as a regression: a failed-callee-only
bridge may still leave a different invented call for the final gate to reject.
Do not infer neighboring receiver bindings from names alone or add domain-specific advice.
See [Qualify bounded failed-call definition context](../issues/69-qualify-failed-call-definition-context.md).

To regenerate the retained audit (requires separately transferred raw artifacts):

```sh
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/definition-grounding/audit.py
```

Initial harness setup incorrectly passed JSON arrays to strict Python-mode validation;
switching to the repository's JSON record parser fixed that setup error before the
visibility comparison. Neither setup nor the experiment invoked a model.
