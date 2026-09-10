# GFLO — local software factory

GFLO runs prepared Python coding tasks with a local LLM, validates their output in
isolated containers, and keeps a durable history of changes, failures, and evidence.
It can plan and build bounded features under prewritten validation policies, combine
accepted changes against pinned inputs, and validate the combined result. Repository
snapshots support text search and revision-bound Python definition lookup.

**Experimental developer preview.** The original 120-run evaluation verified 109 runs
and discovered two false acceptances. Larger-build reliability is still unqualified.
Read the [evaluation](docs/evaluation.md) before relying on the results.

## Start here

Requires Python 3.11+; the development environment was tested with Python 3.13.5.
From a source checkout:

```sh
python3 scripts/setup.py
```

This creates `.venv`, installs pinned dependencies, prepares the demo, and reports
CPU/Docker readiness. To inspect prerequisites without installing:

```sh
python3 scripts/setup.py --check-only
```

The default setup downloads Python packages and checks Docker availability, but
does not start a model or execute worker code. It prepares real, hash-bound work. To execute
it, follow [Getting started](docs/getting-started.md) for the local GPU service and broker.

## Documentation

- [Getting started](docs/getting-started.md): installation, first run, and prerequisites.
- [Architecture](docs/architecture.md): authority, isolation, and supported boundaries.
- [Operations](docs/operations.md): run, resume, inspect changes, integrate, and audit.
- [Product intake](docs/product-intake.md): bounded planning, reviewed task graphs, and escalation.
- [Evaluation](docs/evaluation.md): measured results and reproduction limits.
- [Roadmap](docs/roadmap.md): next workload and public-release readiness.
- [Contributing](CONTRIBUTING.md): development checks and repository layout.

The documentation follows the short entry point and linked guides used by
[SFLO](https://github.com/simonasrazm/simon-factory-lights-out) and
[Gas City](https://github.com/gastownhall/gascity). GFLO is a separate experiment.

The repository is public as an experimental developer preview. No license has
been selected yet; a supported release and license choice remain pending.
