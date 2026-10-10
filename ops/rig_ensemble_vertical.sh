#!/usr/bin/env bash
# Rig vertical for the opt-in ensemble review: stage a committed gflo tree to a fresh rig directory, copy the
# installed runtime config with "review": "ensemble", run real `gflo run` on the listed coding tasks one after
# another, then fetch run state (workspaces excluded) for local inspection. The installed runtime is untouched.
# Usage: ops/rig_ensemble_vertical.sh <commit> <evidence-dir> <task-dir>[,<task-dir>...]   (task dirs relative to repo)
set -euo pipefail
commit=$1 evidence=$2 tasks=$3
repo=$(git rev-parse --show-toplevel)
rig=${GFLO_RIG:-monster-gaming-pc.lan}
short=$(git -C "$repo" rev-parse --short=7 "$commit")
n=1; while [ -e "$evidence/vertical-$n-admission.json" ]; do n=$((n+1)); done; label=vertical-$n
name=gflo-ensemble-vertical-$short-$n
local_root=$repo/.gflo/$name
remote='~'/$name
ssh_rig() { ssh -o BatchMode=yes -o ConnectTimeout=10 "$rig" "$@"; }

test ! -e "$local_root"; mkdir -p "$local_root/stage"
IFS=, read -ra list <<< "$tasks"
git -C "$repo" -c tar.umask=022 archive "$commit" gflo "${list[@]}" | tar -xp -C "$local_root/stage"
for t in "${list[@]}"; do test -f "$local_root/stage/$t/task.json"; done
(cd "$local_root/stage" && find . -type f ! -name inventory.sha256 | sort | xargs sha256sum > inventory.sha256)
cat > "$evidence/$label-admission.json" <<JSON
{"status":"admitted once by rig_ensemble_vertical.sh","label":"$label","utc":"$(date -u +%FT%TZ)","commit":"$short",
 "ensemble_sha256":"$(git -C "$repo" show "$commit:gflo/ensemble.py" | sha256sum | cut -d' ' -f1)",
 "stage_inventory_sha256":"$(sha256sum "$local_root/stage/inventory.sha256" | cut -d' ' -f1)","tasks":"$tasks","rig":"$rig","stage":"$remote"}
JSON
(cd "$local_root/stage" && tar -cp .) | ssh_rig "set -e; test ! -e $remote; umask 022; mkdir -m 700 $remote; tar -xp -C $remote; cd $remote
  sha256sum -c --quiet inventory.sha256
  python3 -c 'import json,sys;c=json.load(open(sys.argv[1]));c[\"review\"]=\"ensemble\";k=c.get(\"api_key_file\")
if k and not k.startswith(\"/\"): import os;c[\"api_key_file\"]=os.path.join(os.path.dirname(sys.argv[1]),k)
json.dump(c,open(\"config.json\",\"w\"),indent=2)' ~/gflo-runtime/.gflo/config.json
  for t in ${list[*]}; do git -C \$t/source init -q 2>/dev/null || true; done; echo staged"
ssh_rig "cd $remote || exit 1; setsid nohup sh -c 'for t in ${list[*]}; do echo \"== \$t \$(date -u +%FT%TZ)\"; \
  (cd \$t/source && git add -A && git -c user.name=gflo -c user.email=gflo@local commit -qm base) || true; \
  PYTHONPATH=\$PWD PYTHONDONTWRITEBYTECODE=1 python3 -m gflo --config config.json --state runs run --environment-store ${GFLO_ENV_STORE:-/home/gradrix/gflo-stage3-25f75c3/.gflo/stage3-preparation/environments} --environment ${GFLO_ENV_ID:-36cd138cbdc332246a2db473301200117f82404a4504c675db95966645348975} \$t/task.json; echo \"exit=\$? \$(date -u +%FT%TZ)\"; done; echo finished > vertical.done' > vertical.log 2>&1 < /dev/null & echo \$! > vertical.pid"
pid=$(ssh_rig "cat $remote/vertical.pid")
# Completion is the remote done marker, or the runner process having exited; an ssh failure only retries.
deadline=$(( $(date +%s) + ${GFLO_VERTICAL_HOURS:-24} * 3600 ))
while :; do
  state=$(ssh_rig "if test -e $remote/vertical.done; then echo done; elif kill -0 $pid 2>/dev/null; then echo running; else echo exited; fi" || echo unreachable)
  case $state in done|exited) break;; esac
  if [ "$(date +%s)" -ge "$deadline" ]; then echo "vertical still $state after ${GFLO_VERTICAL_HOURS:-24}h; leaving it running at $remote" >&2; exit 3; fi
  echo "$(date +%T) $state $(ssh_rig "grep -c '^== ' $remote/vertical.log" 2>/dev/null || echo '?') tasks started"; sleep 120
done
ssh_rig "cd $remote && tar -c --exclude='*/workspace/*' runs vertical.log config.json" | tar -x -C "$local_root"
cp "$local_root/vertical.log" "$evidence/$label.log"
echo "vertical $state: $local_root"
# A runner that died before writing the done marker is a failed vertical, not a completed one.
[ "$state" = done ] || exit 4
