#!/bin/sh
# Model gate on the rig (docs/model-upgrade.md): snapshot HEAD to ~/gflo-gate-<rev>, then run
# ops/benchmark/gate.py in the background against the private benchmark ~/gflo-bench.
#   ops/rig_gate.sh LABEL [--smoke | --suites small,features,tests]
# Results: ~/gflo-bench/runs/LABEL (report.md, summary.json); log: gate.log there. Rerun the same command, at the
# same commit, to resume; gate.py refuses to mix code revisions or model profiles in one LABEL.
set -eu
rig=${GFLO_RIG:-monster-gaming-pc.lan}
label=${1:?usage: ops/rig_gate.sh LABEL [--smoke | --suites LIST]}
shift
git diff --quiet HEAD -- || { echo "uncommitted changes: rig-gate runs committed HEAD only; commit first"; exit 1; }
rev=$(git rev-parse --short HEAD)
dir="gflo-gate-$rev"
busy=$(ssh "$rig" 'ps -eo pid,cmd | grep -E "python3 -m gflo|ops/delivery/drive.py|ops/benchmark/gate.py" | grep -v grep' || true)
if [ -n "$busy" ]; then echo "model slot in use on $rig:"; echo "$busy"; exit 1; fi
git archive --format=tar HEAD | ssh "$rig" "mkdir -p ~/$dir && tar -x -C ~/$dir"
out="\$HOME/gflo-bench/runs/$label"
ssh "$rig" "mkdir -p $out && cd ~/$dir && GFLO_CODE=$rev nohup python3 ops/benchmark/gate.py run ~/gflo-bench $out \
  --config ~/gflo-runtime/.gflo/config.json $* >> $out/gate.log 2>&1 < /dev/null &"
echo "started on $rig: code $rev, results in ~/gflo-bench/runs/$label (gate.log, report.md)"
