#!/bin/sh
# Full suite, including real Docker sandbox tests, on the rig against a snapshot of the working tree's HEAD
# (or of a tree-ish given as $1). Leaves ~/gflo-runtime untouched.
# Known rig-only failures: .scratch/autonomy/issues/10-seed-read-timestamp-granularity.md.
set -eu
rig=${GFLO_RIG:-monster-gaming-pc.lan}
tree=${1:-HEAD}
dir="gflo-check-$(git rev-parse --short "$tree^{tree}")"
git archive --format=tar "$tree" | ssh "$rig" "rm -rf ~/$dir && mkdir ~/$dir && tar -x -C ~/$dir && cd ~/$dir &&
  { PYTHONDONTWRITEBYTECODE=1 timeout 1800 python3 -m unittest discover -s tests > suite.log 2>&1; rc=\$?; };
  grep -E '^(FAIL|ERROR):' suite.log; tail -3 suite.log; cd ~ && rm -rf ~/$dir; exit \$rc"
