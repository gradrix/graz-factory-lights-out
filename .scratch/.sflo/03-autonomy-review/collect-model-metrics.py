"""Read-only compact qualification metrics; never emits model content or keys."""
import argparse
import json
from pathlib import Path
import sqlite3
import statistics

p = argparse.ArgumentParser()
p.add_argument('state', type=Path)
p.add_argument('--candidate', required=True)
a = p.parse_args()
receipt = json.loads((a.state / 'qualification.json').read_text())
if len(receipt['results']) != 13 or 'gate_passed' not in receipt:
    raise SystemExit('Wait for the complete frozen qualification')
c = sqlite3.connect((a.state / 'state.sqlite').resolve().as_uri() + '?mode=ro', uri=True)
requests = c.execute("select count(*) from events where kind='model_wait'").fetchone()[0]
usage = [json.loads(row[0]).get('usage', {}) for row in c.execute("select data from events where kind='model_response'")]
prompts = [r['prompt_tokens'] for r in usage if isinstance(r.get('prompt_tokens'), (int, float))]
speeds, malformed, lines = [], [], 0
for path in sorted(a.state.glob('*/attempts/*/trajectory.jsonl')):
    for number, line in enumerate(path.read_text().splitlines(), 1):
        lines += 1
        try:
            entry = json.loads(line)
        except ValueError as error:
            malformed.append({'file': str(path.relative_to(a.state)), 'line': number, 'error': str(error)})
            continue
        if entry.get('event') == 'response':
            speed = entry.get('body', {}).get('timings', {}).get('predicted_per_second')
            if isinstance(speed, (int, float)):
                speeds.append(speed)
print(json.dumps(dict(candidate=a.candidate,
    scope='coder events and trajectories; excludes reviewer and question-assessment requests',
    executed_environment=receipt['environment']['observed'],
    coder_requests=requests, coder_responses=len(usage),
    max_prompt_tokens=max(prompts) if prompts else None,
    median_prompt_tokens=statistics.median(prompts) if prompts else None,
    total_completion_tokens=sum(r.get('completion_tokens', 0) for r in usage),
    generation_speed_samples=len(speeds),
    median_generation_tokens_per_s=statistics.median(speeds) if speeds else None,
    summed_task_wall_s=round(sum(r['elapsed_s'] for r in receipt['results']), 2),
    max_task_wall_s=max(r['elapsed_s'] for r in receipt['results']),
    trajectory_lines=lines, malformed_trajectory_lines=malformed), indent=2))
