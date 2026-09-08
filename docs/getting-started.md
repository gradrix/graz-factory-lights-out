# Getting started

## Prepare a task without a GPU

Use the installation and preparation commands in the [README](../README.md).
`examples/prepare_demo.py` produces a complete `RunPlan` for a small slug-normalization
program: source, objective, immutable input identities, independent process gates,
model profile, and broker image. Submission persists the plan and source artifacts;
status should be `ready`, with no attempts yet.

If your Python installation cannot create a virtual environment with pip, install
its venv support, or use an available system pip:

```sh
python3 -m venv --without-pip .venv
python3 -m pip --python .venv/bin/python install -r requirements-dev.lock -e .
```

`examples/work-atom.json` is a schema template with placeholder digests. Submitting
that file alone demonstrates ledger storage but does not prepare executable work.
The demo generator replaces those placeholders with verified bindings.

## Execute with a local model

Live execution requires Linux, a local Docker daemon, a compatible NVIDIA GPU and
container runtime, a downloaded model, and the pinned broker image. The measured
configuration uses an RTX 5090. Other hardware is not qualified by these results.

Set up and check the [model service](../infra/serving/README.md), then install the
broker image explicitly (the broker never pulls images):

```sh
docker pull python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca
```

Run the prepared task and inspect its result:

```sh
.venv/bin/gflo --db .gflo/demo/ledger.db run pilot-v1-01-slug
.venv/bin/gflo --db .gflo/demo/ledger.db history pilot-v1-01-slug
.venv/bin/gflo --db .gflo/demo/ledger.db report pilot-v1-01-slug
```

The model may fail; this demo permits three attempts. Success yields an accepted
immutable source artifact and gate evidence. It does not overwrite your checkout.
See [Operations](operations.md) for interruption, quarantine, and challenged results.

To use a different deployment configuration, generate the plan with
`--config PATH`. A changed plan needs a new ledger or distinct atom identity;
identical IDs cannot be reused for changed contracts. The client currently requires
the verified loopback vLLM API, including exact chat tokenization.
