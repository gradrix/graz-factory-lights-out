#!/usr/bin/env bash
# Stage a committed review prototype on the 5090 rig, run it once, download and verify the trial, score it locally.
# Usage: ops/rig_trial.sh <commit> <module.py> <evidence-dir>
# Host Python is never used: packages and scoring run in python:3.12-slim with no network.
set -euo pipefail
commit=$1 module=$2 evidence=$3
repo=$(git rev-parse --show-toplevel)
gflo=/home/gradrix/repos/gflo
rig=${GFLO_RIG:-monster-gaming-pc.lan}
short=$(git -C "$repo" rev-parse --short=7 "$commit")
name=gflo-review-${module%%_prototype.py}-$short
local_root=$gflo/.gflo/$name
remote='~'/$name
trial=$gflo/.gflo/executable-review-protocol-trial-1/artifact-hashes.json
py() { docker run --rm --user "$(id -u):$(id -g)" --network none -v /home/gradrix/repos:/home/gradrix/repos \
       -w "$repo" -e PYTHONPATH="$repo" -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim python "$@"; }
ssh_rig() { ssh -o BatchMode=yes -o ConnectTimeout=10 "$rig" "$@"; }

test -z "$(git -C "$repo" status --porcelain -- ops gflo)" || { echo "uncommitted prototype changes" >&2; exit 1; }
test ! -e "$local_root" || { echo "$local_root exists; trials are never rerun" >&2; exit 1; }
mkdir -p "$local_root/stage/inputs"

# Stage: committed code, verified input packages, serving identity, contract.
py ops/review_evidence_prototype.py prepare --public-manifest evaluations/executable-review/manifest.json \
   --trial-manifest "$trial" --output "$local_root/stage/packages"
git -C "$repo" archive "$commit" gflo ops | tar -x -C "$local_root/stage"
cp "$gflo/.scratch/.sflo/08-autonomy-planning-pilot/serving-lifecycle/expected-identity.json" "$evidence/contract.md" "$local_root/stage/inputs/"
(cd "$local_root/stage" && find . -type f ! -name inventory.sha256 | sort | xargs sha256sum > inventory.sha256)
packages=$(sha256sum "$local_root/stage/packages/manifest.json" | cut -d' ' -f1)

# Transfer and verify remotely before any inference.
(cd "$local_root/stage" && tar -c .) | ssh_rig "set -e; test ! -e $remote; mkdir -m 700 $remote; tar -x -C $remote; cd $remote;
  sha256sum -c --quiet inventory.sha256; PYTHONPATH=\$PWD PYTHONDONTWRITEBYTECODE=1 python3 -c \"
import sys;sys.path[:0]=['ops','.']
import review_evidence_prototype as p;p.verify_packages('packages/manifest.json','$packages');print('stage verified')\"" \
  | tee "$local_root/staging-result.txt"

# Admission record, then dispatch once.
admission=$evidence/trial-1-admission.json
test ! -e "$admission"
cat > "$admission" <<EOF
{"status":"admitted once by rig_trial.sh","utc":"$(date -u +%FT%TZ)","prototype_commit":"$short",
 "module":"$module","module_sha256":"$(git -C "$repo" show "$commit:ops/$module" | sha256sum | cut -d' ' -f1)",
 "contract_sha256":"$(sha256sum "$evidence/contract.md" | cut -d' ' -f1)",
 "stage_inventory_sha256":"$(sha256sum "$local_root/stage/inventory.sha256" | cut -d' ' -f1)",
 "package_manifest_sha256":"$packages","rig":"$rig","stage":"$remote"}
EOF
ssh_rig "cd $remote && test ! -e trial-1 && PYTHONPATH=\$PWD PYTHONDONTWRITEBYTECODE=1 setsid nohup python3 ops/$module run \
  --manifest packages/manifest.json --manifest-sha256 $packages --config ~/gflo-runtime/.gflo/config.json \
  --identity inputs/expected-identity.json --output trial-1 --lease ~/.local/state/gflo-planning-pilot/lease \
  > trial-1-controller.log 2>&1 < /dev/null & echo \$! > trial-1.pid"

# Monitor until the controller exits.
pid=$(ssh_rig "cat $remote/trial-1.pid")
while ssh_rig "kill -0 $pid 2>/dev/null"; do
  echo "$(date +%T) running: $(ssh_rig "ls $remote/trial-1 2>/dev/null | grep -c case-" || true) cases started"; sleep 30
done

# Download, verify, score.
ssh_rig "cd $remote && tar -c trial-1 trial-1-controller.log" | tar -x -C "$local_root"
(cd "$local_root/trial-1" && jq -r 'to_entries[]|"\(.value)  \(.key)"' artifact-hashes.json | sha256sum -c --quiet)
cp "$local_root/trial-1/results.json" "$evidence/trial-results.json"
cp "$local_root/trial-1/artifact-hashes.json" "$evidence/trial-artifact-hashes.json"
cp "$local_root/stage/inventory.sha256" "$evidence/stage-inventory.sha256"
cp "$local_root/staging-result.txt" "$evidence/staging-result.txt"
if grep -q "def score" "$repo/ops/$module"; then
  py "ops/$module" score --results "$local_root/trial-1/results.json" \
     --expectations evaluations/executable-review/private/expectations.json | tee "$evidence/trial-score.json"
fi
echo "trial complete: $local_root/trial-1"
