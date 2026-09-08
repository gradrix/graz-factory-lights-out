# GFLO — local software factory

GFLO is an experiment in autonomous software production using a local model. It runs
prepared Python Work atoms through bounded worker views, isolated execution, independent
gates and a durable SQLite/artifact ledger. Worker changes, failed attempts and evidence
remain reviewable. Prepared integration combines accepted edits against pinned inputs.

The latest forty-task, three-repeat evaluation verified **109/120 runs** and found
**two false acceptances**. Numerical targets passed, but progression to larger-build
claims is blocked. See the [results and limitations](.scratch/local-lights-out-factory/heldout-results.md).

- [Current handoff and next work](.scratch/local-lights-out-factory/HANDOFF.md)
- [Installation and durable ledger](docs/ledger.md)
- [Worker/model client](docs/worker.md) and [controller CLI](docs/controller.md)
- [Execution broker and gates](docs/broker.md)
- [Prepared integration](docs/integration.md)
- [Acceptance findings](docs/acceptance-findings.md) and [readable repair feedback](docs/validation-feedback.md)
- [Serving setup](infra/serving/README.md) and [qualified RTX 5090 graph profile](infra/serving/vllm-5090-graphs.example.json)
- [Planning map](.scratch/local-lights-out-factory/map.md)

Run local checks in the pinned development environment:

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check gflo
.venv/bin/mypy gflo
```

Docker qualification tests require `GFLO_BROKER_TEST_IMAGE` with the pinned image;
see the broker documentation. Latest enabled suite: 253 tests and 25 subtests passed,
no skips. Autonomous product planning, Git promotion and general large-build capability
remain unqualified. SFLO and Gas City are architectural references; no automatic cloud
fallback is included.
