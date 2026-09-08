# GFLO — local software factory

GFLO runs prepared Python coding tasks with a local LLM, validates their output in
isolated containers, and keeps a durable history of changes, failures, and evidence.
It can combine accepted changes against pinned inputs and validate the combined result.

**Experimental developer preview.** The latest evaluation verified 109 of 120 runs
and discovered two false acceptances. Larger-build reliability is still unqualified.
Read the [evaluation](docs/evaluation.md) before relying on the results.

## Start here

Requires Python 3.11+; the development environment was tested with Python 3.13.5.
From a source checkout:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock -e .
.venv/bin/python examples/prepare_demo.py > /tmp/gflo-demo-plan.json
.venv/bin/gflo --db .gflo/demo/ledger.db submit-run /tmp/gflo-demo-plan.json
.venv/bin/gflo --db .gflo/demo/ledger.db status pilot-v1-01-slug
```

This prepares real, hash-bound work without contacting a model or Docker. To execute
it, follow [Getting started](docs/getting-started.md) for the local GPU service and broker.

## Documentation

- [Getting started](docs/getting-started.md): installation, first run, and prerequisites.
- [Architecture](docs/architecture.md): authority, isolation, and supported boundaries.
- [Operations](docs/operations.md): run, resume, inspect changes, integrate, and audit.
- [Evaluation](docs/evaluation.md): measured results and reproduction limits.
- [Roadmap](docs/roadmap.md): next workload and public-release readiness.
- [Contributing](CONTRIBUTING.md): development checks and repository layout.

The documentation follows the short entry point and linked guides used by
[SFLO](https://github.com/simonasrazm/simon-factory-lights-out) and
[Gas City](https://github.com/gastownhall/gascity). GFLO is a separate experiment.

No license has been selected yet. Publication and license selection remain pending.
