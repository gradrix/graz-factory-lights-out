#!/bin/sh
# Rebuild the private model-gate benchmark on the rig from the committed seed (docs/model-upgrade.md):
#   ops/rig_bench.sh [NAME]   (default gflo-bench, under the rig's home; refuses an existing directory)
# Needs the home-lab repository here (GFLO_HOME_LAB, default ~/repos/home-lab) and the seed passphrase in
# .gflo/bench-passphrase (otherwise gpg asks). Runs in the background (environments take a while); log:
# ~/gflo-bench-build-<rev>/build.log on the rig. The decrypted seed and repository copies are deleted after.
set -eu
rig=${GFLO_RIG:-monster-gaming-pc.lan}
name=${1:-gflo-bench}
home_lab=${GFLO_HOME_LAB:-$HOME/repos/home-lab}
git diff --quiet HEAD -- || { echo "uncommitted changes: rig-bench uses committed HEAD only; commit first"; exit 1; }
if ssh "$rig" "test -e ~/$name"; then echo "~/$name exists on $rig; move it away or pass another NAME"; exit 1; fi
rev=$(git rev-parse --short HEAD)
dir="gflo-bench-build-$rev"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
pass=""
[ -f .gflo/bench-passphrase ] && pass="--passphrase-file .gflo/bench-passphrase"
gpg --batch --quiet --pinentry-mode loopback $pass -d ops/benchmark/seed/home-lab.json.gpg > "$tmp/home-lab.json"
git -C "$home_lab" bundle create "$tmp/home-lab.bundle" --all 2>/dev/null
git bundle create "$tmp/gflo.bundle" --all 2>/dev/null
git archive --format=tar HEAD | ssh "$rig" "rm -rf ~/$dir && mkdir -p ~/$dir && tar -x -C ~/$dir && mkdir ~/$dir/src"
scp -q "$tmp/home-lab.json" "$tmp/home-lab.bundle" "$tmp/gflo.bundle" "$rig:$dir/src/"
ssh "$rig" "cd ~/$dir && cp ops/benchmark/seed/manifest.json ops/benchmark/seed/gflo.json src/ \
  && git clone -q src/home-lab.bundle src/home-lab && git clone -q src/gflo.bundle src/gflo \
  && nohup sh -c 'python3 ops/benchmark/bench.py build src ~/$name --source home-lab=src/home-lab --source gflo=src/gflo; \
  status=\$?; rm -rf src; echo BUILD EXIT \$status' > build.log 2>&1 < /dev/null &"
echo "building ~/$name on $rig in the background; log ~/$dir/build.log (ends with BUILD EXIT 0)"
