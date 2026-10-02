# Independent coding qualification cohort B

Twelve new coding tasks prepared after the question-triage change was requested. No task/model run informed these implementations or acceptance cases. This cohort covers different topics from cohort A: dependency ordering, sliding rate limits, retries, config overlays, log escaping, manifest validation, compare-and-set versions, grouped batch responses, schema migration, weighted LRU, event watermarks, and Unicode indexing. Each source is a clean committed repository with domain.py, api.py and cli.py. Changes must preserve an existing useful action while adding a feature across domain/API/CLI.

## Isolation and budgets

Only stage each task's source and objective into the coder context. Acceptance remains in the separate acceptance directory; private references, oracles and validation records must not enter coder or reviewer contexts. Start each run with fresh context. The separate ambiguous queue-policy fixture is evaluated by transcript for an irreducible product question; it is outside the twelve-task denominator. Do not erase cohort A's unnecessary questions or original results.

Frozen budget: three attempts, 24 turns per attempt, 900 seconds per task. run-budget.json is authoritative for evaluation; wall_time_seconds is included as task metadata, but the evaluation harness must enforce the wall clock because current runner may not consume that field. Python 3.12+ and UTF-8 environment are explicitly included in each objective.

## Independent evidence

private/validation.json records twelve baseline failures and twelve reference passes on CPython 3.12.12. Each oracle checks retained behavior, new API results, CLI integration, input immutability, and domain-specific boundaries. Invalid cases only cover explicit contractual validation. Some oracles exhaust small state spaces or use independent invariants/permutations. The reference is a witness that the stated objective is implementable; passing acceptance is not a substitute for semantic review of the complete objective.

Reproduce a witness by materializing private/references/NN.json into an empty temporary directory and running the corresponding acceptance/check.py with that directory as cwd, using Python 3.12+ and -B -I. Baseline fixtures should fail only because the new action is missing, after retained behavior checks have passed. No GPU, network or external service is involved in preparation.

manifest.json binds all non-Git files and every source commit; MANIFEST.sha256 binds the manifest itself. Freeze before model exposure. Any later correction must create a new version and preserve original results, rather than silently replacing this cohort.
