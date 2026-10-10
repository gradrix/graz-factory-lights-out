#!/bin/sh
# Fast local guardrail: the full unit suite in a throwaway container without network.
# Container-executing tests skip here (no Docker CLI inside); ops/rig_check.sh runs them on the rig.
set -eu
root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
exec docker run --rm --user "$(id -u):$(id -g)" --network none -v "$root:$root:ro" -w "$root" \
  -e HOME=/tmp -e PYTHONPATH="$root" -e PYTHONDONTWRITEBYTECODE=1 python:3.12@sha256:63828510c8b5ccce3bf0d6fabd6f3d17d4effa1ffe690f80a67c8e2d394e03ee \
  python -m unittest discover -s tests "$@"
