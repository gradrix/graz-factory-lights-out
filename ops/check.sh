#!/bin/sh
# Fast local guardrail: the full unit suite in a throwaway container without network.
# Container-executing tests skip here (no Docker CLI inside); ops/rig_check.sh runs them on the rig.
set -eu
root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
exec docker run --rm --user "$(id -u):$(id -g)" --network none -v "$root:$root:ro" -w "$root" \
  -e HOME=/tmp -e PYTHONPATH="$root" -e PYTHONDONTWRITEBYTECODE=1 python:3.12 \
  python -m unittest discover -s tests "$@"
