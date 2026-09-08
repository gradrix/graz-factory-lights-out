# Contributing

GFLO is an experimental Python runtime. Start with the [architecture](docs/architecture.md)
and [roadmap](docs/roadmap.md). License selection is pending before public release.

## Development

Install the environment using the [README](README.md), then run:

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check gflo
.venv/bin/mypy gflo
git diff --check
```

Docker enforcement tests are opt-in. Set `GFLO_BROKER_TEST_IMAGE` to the pinned
Python image from [Getting started](docs/getting-started.md) before pytest to enable
them. They exercise real container limits; default skipped tests are not evidence
that those limits work on your host. Live model and fault-injection harnesses in
`scripts/` are separate from normal development checks.

## Source map

| Path | Responsibility |
| --- | --- |
| `gflo/records.py`, `ledger.py`, `artifacts.py` | Contracts, durable state, immutable evidence |
| `gflo/controller.py`, `worker.py`, `model.py`, `feedback.py` | Prepared execution and bounded inference |
| `gflo/broker.py`, `gates.py` | Isolated processes and trusted validation |
| `gflo/integration.py` | Prepared combined candidates and dependency checks |
| `gflo/history.py`, `reporting.py`, `cli.py` | Inspection and command interface |
| `tests/` | Automated runtime and recovery checks |
| `scripts/`, `infra/serving/` | Qualification harnesses and local serving |

Keep behavior changes accompanied by focused evidence for the affected authority,
recovery, or validation boundary. Distinguish new qualification from follow-ups on
seen failures. Update the relevant guide instead of appending a chronological log.

## Continue on another machine

Commit source changes together with the handoff, issues, and research in `.scratch/`,
then transfer those commits through your development remote or a Git bundle.
Untracked files do not travel with a clone. Start with the
[handoff](.scratch/local-lights-out-factory/HANDOFF.md) and follow its active issue links;
the [roadmap](docs/roadmap.md) provides the shorter overview.

Runtime artifacts under ignored `.gflo/`, local serving overrides, and model caches
need separate transfer or recreation. Code development and new tests do not require
old run artifacts; inspecting or resuming a historical run does. Stop controllers
and transfer its ledger, SQLite WAL state, and artifact store consistently.

Keep user-facing guides in `docs/`. A public release can use a reviewed source
snapshot without removing the development history from this repository.
Agent workflow conventions are in [AGENTS.md](AGENTS.md).
