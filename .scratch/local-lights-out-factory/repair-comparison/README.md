# Small repair loop comparison

Owner chose to diagnose small-task completion before expanding to systems. This
experiment compares a single prepared Work atom and a minimal whole-file JSON loop.
It does not manually repair generated code or change the pinned model.

Both arms start with the exact retained failed Importflow parser, the same narrowed
parser requirement, the original complete parser gate, the admitted Docker image,
and six responses at most (16,384 total / 6,144 output tokens per response). The
factory retains two attempts of three turns. The minimal loop has six successive
repair turns. Both use temperature zero, seed 42 and disabled thinking.

This is a composite comparison: response protocol, context projection, draft handling
and attempt boundaries differ. It cannot isolate one protocol rule causally. A single
pair cannot establish reliability. The minimal loop is diagnostic infrastructure,
not a factory acceptance path or a production worker replacement.

## Reproduction

From the repository root:

```sh
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/repair-comparison/probe.py
PYTHONPATH=. .venv/bin/python .scratch/local-lights-out-factory/repair-comparison/run.py
```

The probe exits 1 for the retained empty-input bug. The full gate remains to detect
regressions while fixing it. The comparison refuses an existing run directory;
never reset a completed run to obtain a different result. Raw prompts, responses,
model source and broker evidence are retained under ignored
`.gflo/evidence/repair-comparison-v2/`. Portable schedule/results are beside this file.
Preparation v1 failed strict tuple parsing before inference; its directory is retained.

## Atom direction

Keep the durable Work atom contract. The original ticket 06 already specifies
cohesive behavior, purpose-specific context, failure-directed treatment and controlled
decomposition. A file is a scope boundary, not necessarily the ideal unit of behavior.
Do not introduce a new atom schema merely because this one workload failed.

Progression should qualify: standalone script creation and repair; persistent CLI
program; restartable scheduler; API plus worker; then multi-module systems. Each level
needs independent correctness checks and multiple fresh unattended successes, with
human preparation and interventions counted separately. A successful supervised
repair alone does not qualify creation from scratch or autonomous planning.

## Results

Both arms exhausted six responses without passing the complete parser gate. Factory:
20,013 tokens, task-halt. Minimal: 11,440 tokens, two distinct candidates; turns 2–6
returned identical candidate bytes. It corrected empty input, misreported malformed
CSV as row 1, then misreported a blank first data record as row 1 and stopped improving.
The factory also requested source windows twice, spending two of six responses on
reads. All six factory tokenizer/generation message and budget comparisons pass.

Neither removing project context nor switching to the minimal whole-file loop rescued
this workload. This does not prove the model is incapable, that windowing is harmless,
or that different feedback/recovery would fail. It rules out treating either change
alone as an already demonstrated solution. No runtime/default/atom-schema changes.

Next qualification should start with a small pure-stdlib script created from scratch,
then a deliberately introduced repair, with explicit expected/actual diagnostics.
Measure creation and repair separately; do not count this supervised parser attempt
as either a complete application or proof that even trivial scripts cannot be built.
