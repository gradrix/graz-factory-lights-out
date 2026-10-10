"""Run a delivery-rate cohort on the rig: each task once per reviewer arm, then score against hidden tests.

usage: drive.py TASKS MINED STORE STATE CONFIG RESULTS --commits C1,C2 [--arms single,ensemble,notes,plan,map,nav,mini] [--timeout S]

One factory run at a time (one model slot). Results append to RESULTS (JSON lines); finished
(commit, arm) pairs are skipped, so an interrupted cohort resumes where it stopped.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.delivery.tasks import score  # noqa: E402


# Reviewer and worker-navigation arms (roadmap phases 1-2); each overlays the base factory config.
ARMS = {
    'single': {'review': 'single'},
    'ensemble': {'review': 'ensemble'},
    'notes': {'review': 'single', 'navigation': {'handoff': True}},
    'plan': {'review': 'single', 'navigation': {'checkpoint': 12, 'max_turns': 60}},
    'map': {'review': 'single', 'navigation': {'map': True}},
    'nav': {'review': 'single', 'navigation': {'handoff': True, 'checkpoint': 12, 'max_turns': 60, 'map': True, 'stale_tests': True}},
    'mini': {'review': 'single', 'worker': 'mini-swe-agent'},  # needs mini-swe-agent on PYTHONPATH
}


def done(results):
    if not Path(results).exists():
        return set()
    return {(row['commit'], row['arm']) for row in map(json.loads, Path(results).read_text().splitlines()) if row.get('scored')}


def run(args, commit, arm):
    config = Path(args.state) / f'config-{arm}.json'
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps(dict(json.loads(Path(args.config).read_text()), **ARMS[arm])))
    state = Path(args.state) / arm
    command = [sys.executable, '-m', 'gflo', '--state', str(state), '--config', str(config), 'run',
               str(Path(args.tasks) / commit / 'task.json'), '--environment', (Path(args.tasks) / commit / 'environment.txt').read_text().strip(),
               '--environment-store', args.store]
    started = time.monotonic()
    log = Path(args.state) / 'logs' / f'{commit}-{arm}.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('w') as output:
        try:
            completed = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=args.timeout,
                                       cwd=Path(__file__).resolve().parents[2])
            exit_code = completed.returncode
        except subprocess.TimeoutExpired:
            exit_code = 'timeout'
    elapsed = round(time.monotonic() - started, 1)
    found = re.search(r'^Run: ([0-9a-f]{12})$', log.read_text(), re.M)
    row = {'commit': commit, 'arm': arm, 'exit_code': exit_code, 'elapsed_s': elapsed,
           'run': found.group(1) if found else None, 'scored': False}
    if found:
        try:
            row.update(score(args.mined, args.tasks, state, args.store, commit, found.group(1)))
            row.pop('tail', None)
            row['scored'] = True
        except Exception as error:  # keep the row; a scoring failure is evidence too
            row['score_error'] = f'{type(error).__name__}: {error}'[:500]
    return row


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('tasks', 'mined', 'store', 'state', 'config', 'results'):
        parser.add_argument(name)
    parser.add_argument('--commits', required=True)
    parser.add_argument('--arms', default='single,ensemble')
    parser.add_argument('--timeout', type=int, default=4 * 3600)
    args = parser.parse_args()
    unknown = set(args.arms.split(',')) - set(ARMS)
    if unknown:
        parser.error('unknown arms: ' + ', '.join(sorted(unknown)) + '; known: ' + ', '.join(ARMS))
    finished = done(args.results)
    for arm in args.arms.split(','):
        for commit in args.commits.split(','):
            if (commit, arm) in finished:
                continue
            row = run(args, commit, arm)
            with open(args.results, 'a') as output:
                output.write(json.dumps(row) + '\n')
            print(json.dumps({k: row.get(k) for k in ('commit', 'arm', 'factory_status', 'hidden_pass', 'delivered', 'elapsed_s')}), flush=True)
