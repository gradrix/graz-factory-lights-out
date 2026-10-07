#!/usr/bin/env bash
# Verify cohort-2 d-cases in the approved offline image: acceptance check, shipped tests, README defect.
set -u
cd "$(dirname "$0")/../.."
IMG=sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc
box() { docker run --rm --pull never --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
  --memory 1g --cpus 2 --pids-limit 128 --tmpfs /tmp:rw,nosuid,nodev,size=128m -e PYTHONDONTWRITEBYTECODE=1 "$@"; }
for d in review-cohort-2/public/d*; do
  id=$(basename "$d"); task=$(ls -d coding-d/tasks/${id#d}-*)
  box -v "$PWD/$d/source:/workspace:ro" -v "$PWD/$task/acceptance:/acceptance:ro" -w /workspace $IMG python -B -I /acceptance/check.py >/dev/null 2>&1; acc=$?
  own=$(box -v "$PWD/$d/source:/workspace:ro" -w /workspace $IMG sh -c 'cp -r /workspace /tmp/w && cd /tmp/w && python -m unittest discover 2>&1 | tail -1')
  echo "$id acceptance_exit=$acc own_tests=$own"
done
echo "d09 README invocation:"
box -v "$PWD/review-cohort-2/public/d09/source:/workspace:ro" -w /workspace $IMG sh -c \
  "printf '%s\n' '{\"action\": \"export_csv\", \"invoices\": [{\"id\": \"a\", \"customer\": \"Ada\", \"items\": [{\"quantity\": 3, \"unit_cents\": 105}, {\"quantity\": 0, \"unit_cents\": 1}]}]}' | python cli.py; echo rc=\$?" 2>&1
