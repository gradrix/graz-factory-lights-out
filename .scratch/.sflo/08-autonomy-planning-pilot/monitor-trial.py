"""Read-only trial1 summary; run through SSH stdin on MONSTER-GAMING-PC."""
import json
from pathlib import Path
import time

stage = Path('/home/gradrix/gflo-planning-d186b93')
root = stage / 'trial-1'
launch = json.loads((stage / 'trial-1-process.json').read_bytes())
process = Path('/proc') / str(launch['pid'])
alive = process.exists() and 'Z' != (process / 'stat').read_text().rsplit(')', 1)[1].split()[0]
rows = []
for arm in sorted(root.glob('[1-4]-*')):
    row = {'arm': arm.name}
    if (arm / 'budget.json').exists():
        budget = json.loads((arm / 'budget.json').read_bytes())
        calls = budget['calls']
        row.update(calls=len(calls), remaining_s=round(budget['deadline'] - time.monotonic(), 1),
                   roles={role: sum(c['role'] == role for c in calls) for role in sorted({c['role'] for c in calls})},
                   last_call={key: calls[-1].get(key) for key in ('number', 'role', 'status')} if calls else None)
    if (arm / 'result.json').exists():
        result = json.loads((arm / 'result.json').read_bytes())
        row.update(status=result['status'], stop=result.get('stop'),
                   cleanup=result.get('cleanup_confirmed'), idle=result.get('idle_confirmed'),
                   work_s=result.get('work_elapsed_s'), child=result.get('child'))
    else:
        row['status'] = 'running' if alive else 'interrupted_or_not_published'
    rows.append(row)
print(json.dumps({'controller_alive': alive, 'pid': launch['pid'], 'arms': rows,
                  'artifact_manifest_present': (root / 'artifact-hashes.json').exists()}, indent=2))
