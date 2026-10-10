#!/bin/sh
# Mine gflo's own history on the rig: mine_gflo.sh GFLO_GIT OUT STORE COMMITS
# Tests needing Docker or git cannot run in the sandbox image and drop out on both sides.
set -eu
exec python3 "$(dirname "$0")/mine.py" "$1" . "$2" --store "$3" --commits "$4" --marker 'not docker_only'
