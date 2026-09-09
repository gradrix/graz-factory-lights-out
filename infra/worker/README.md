# Dependency image for supervised GFLO trials

This is a trusted build step, separate from model workers. The image contains
GFLO's pinned runtime and test dependencies, not repository source. Worker containers
still use the existing broker's network, mount, memory, PID, and user restrictions.
The existing standard-library image remains the default.

The lock targets CPython 3.11 on Linux x86-64, matching the pinned Python base.
It records SHA-256 hashes for all selected wheels, including transitive dependencies.
It is not a cross-platform lock. Image byte identity can vary with build timestamps;
record the resulting local image SHA-256 in each prepared RunPlan.

From the repository root:

```sh
mkdir -p .gflo/dependency-build/wheels
cp infra/worker/requirements-cp311-linux-x86_64.lock .gflo/dependency-build/requirements.lock
cp infra/worker/Dockerfile .gflo/dependency-build/Dockerfile
docker run --rm -v "$PWD/.gflo/dependency-build:/build" python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca python -m pip download --only-binary=:all: --require-hashes --dest /build/wheels -r /build/requirements.lock
docker build --network=none -t gflo-python-dev:trial .gflo/dependency-build
docker image inspect gflo-python-dev:trial --format '{{.Id}}'
```

Downloads require network access; installation during the build uses only the
verified wheels. Trial workers never install packages or obtain network access.
The broker must qualify the resulting image before executing candidate code.
