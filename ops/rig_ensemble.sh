#!/usr/bin/env bash
# Stage a committed ensemble prototype and the public review cohort on the 5090 rig, run the listed cases once,
# download and verify artifacts, and score locally against private expectations (never staged).
# Usage: ops/rig_ensemble.sh <commit> <evidence-dir> <comma-separated case ids> [run-label]
set -euo pipefail
commit=$1 evidence=$2 cases=$3 label_hint=${4:-}
repo=$(git rev-parse --show-toplevel)
gflo=/home/gradrix/repos/gflo
rig=${GFLO_RIG:-monster-gaming-pc.lan}
short=$(git -C "$repo" rev-parse --short=7 "$commit")
n=1; while [ -e "$evidence/trial-$n-admission.json" ]; do n=$((n+1)); done; label=trial-$n
name=gflo-review-ensemble-$short-$label
local_root=$gflo/.gflo/$name
remote='~'/$name
cohort=evaluations/review-cohort-2
py() { docker run --rm --user "$(id -u):$(id -g)" --network none -v /home/gradrix/repos:/home/gradrix/repos \
       -w "$repo" -e PYTHONPATH="$repo" -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim python "$@"; }
ssh_rig() { ssh -o BatchMode=yes -o ConnectTimeout=10 "$rig" "$@"; }

test -z "$(git -C "$repo" status --porcelain -- ops gflo $cohort)" || { echo "uncommitted prototype changes" >&2; exit 1; }
test ! -e "$local_root"; mkdir -p "$local_root/stage/inputs"
git -C "$repo" archive "$commit" gflo ops "$cohort/manifest.json" "$cohort/public" | tar -xp -C "$local_root/stage"
test ! -e "$local_root/stage/$cohort/private"
cp "$gflo/.scratch/.sflo/08-autonomy-planning-pilot/environment-bindings.json" \
   "$gflo/.scratch/.sflo/08-autonomy-planning-pilot/serving-lifecycle/expected-identity.json" \
   "$evidence/contract.md" "$local_root/stage/inputs/"
(cd "$local_root/stage" && find . -type f ! -name inventory.sha256 | sort | xargs sha256sum > inventory.sha256)
manifest_sha=$(sha256sum "$local_root/stage/$cohort/manifest.json" | cut -d' ' -f1)

(cd "$local_root/stage" && tar -cp .) | ssh_rig "set -e; test ! -e $remote; umask 022; mkdir -m 700 $remote; tar -xp -C $remote; cd $remote;
  sha256sum -c --quiet inventory.sha256; PYTHONPATH=\$PWD PYTHONDONTWRITEBYTECODE=1 python3 -c \"
import sys;sys.path[:0]=['ops','.']
import review_ensemble as r;m=r.verify_cohort('$cohort/manifest.json','$manifest_sha');print('stage verified',len(m['cases']),'cases')\"" \
  | tee "$local_root/staging-result.txt"

cat > "$evidence/$label-admission.json" <<EOF
{"status":"admitted once by rig_ensemble.sh","label":"$label","hint":"$label_hint","utc":"$(date -u +%FT%TZ)",
 "prototype_commit":"$short","module_sha256":"$(git -C "$repo" show "$commit:ops/review_ensemble.py" | sha256sum | cut -d' ' -f1)",
 "contract_sha256":"$(sha256sum "$evidence/contract.md" | cut -d' ' -f1)","cohort_manifest_sha256":"$manifest_sha",
 "stage_inventory_sha256":"$(sha256sum "$local_root/stage/inventory.sha256" | cut -d' ' -f1)","cases":"$cases","rig":"$rig","stage":"$remote"}
EOF
ssh_rig "cd $remote && PYTHONPATH=\$PWD PYTHONDONTWRITEBYTECODE=1 setsid nohup python3 ops/review_ensemble.py run \
  --manifest $cohort/manifest.json --manifest-sha256 $manifest_sha --bindings inputs/environment-bindings.json \
  --config ~/gflo-runtime/.gflo/config.json --identity inputs/expected-identity.json --output trial \
  --cases $cases --lease ~/.local/state/gflo-planning-pilot/lease > controller.log 2>&1 < /dev/null & echo \$! > trial.pid"

pid=$(ssh_rig "cat $remote/trial.pid")
while ssh_rig "kill -0 $pid 2>/dev/null"; do
  echo "$(date +%T) running: $(ssh_rig "ls $remote/trial 2>/dev/null | grep -vc json" || true) cases started"; sleep 60
done

ssh_rig "cd $remote && tar -c --exclude=candidate trial controller.log" | tar -x -C "$local_root"
(cd "$local_root/trial" && jq -r 'to_entries[]|"\(.value)  \(.key)"' artifact-hashes.json | sha256sum -c --quiet)
cp "$local_root/trial/results.json" "$evidence/$label-results.json"
cp "$local_root/trial/artifact-hashes.json" "$evidence/$label-artifact-hashes.json"
cp "$local_root/stage/inventory.sha256" "$evidence/$label-stage-inventory.sha256"
py ops/review_ensemble.py score --results "$local_root/trial/results.json" \
   --expectations $cohort/private/expectations.json | tee "$evidence/$label-score.json"
echo "trial complete: $local_root/trial"
