"""Run a delivery-rate cohort on the rig: each task once per reviewer arm, then score against hidden tests.

usage: drive.py TASKS MINED STORE STATE CONFIG RESULTS --commits C1,C2 [--arms single,ensemble,notes,plan,map,nav,mini,queued]
                [--steps STEPS_JSON] [--timeout S]

The queued arm (phase 4) runs a mined chain as `gflo queue run`, one step per objective in STEPS_JSON
({commit: [objective, ...]}), and scores the integration branch; the other arms run TASKS/<commit>/task.json.

One factory run at a time (one model slot). Results append to RESULTS (JSON lines); finished
(commit, arm) pairs are skipped, so an interrupted cohort resumes where it stopped.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gflo.overnight import FINAL  # noqa: E402
from ops.delivery.tasks import score, score_tree  # noqa: E402


# Reviewer and worker-navigation arms (roadmap phases 1-2); each overlays the base factory config.
ARMS = {
    'single': {'review': 'single'},
    'ensemble': {'review': 'ensemble'},
    'notes': {'review': 'single', 'navigation': {'handoff': True}},
    'plan': {'review': 'single', 'navigation': {'checkpoint': 12, 'max_turns': 60}},
    'map': {'review': 'single', 'navigation': {'map': True}},
    'nav': {'review': 'single', 'navigation': {'handoff': True, 'checkpoint': 12, 'max_turns': 60, 'map': True, 'stale_tests': True}},
    'mini': {'review': 'single', 'worker': 'mini-swe-agent'},  # needs mini-swe-agent on PYTHONPATH
    'queued': {'review': 'single'},  # phase 4: one `gflo queue run` step per chain commit, objectives from --steps
}


def queue_spec(args, commit):
    """The queue JSON for a mined chain: one step per commit objective, tests as the record runs them."""
    record = json.loads((Path(args.mined) / commit / 'record.json').read_text())
    command = record['test_command']
    python = command.index('python')
    steps = json.loads(Path(args.steps).read_text())[commit]
    spec = {'repo': str((Path(args.tasks) / commit / 'repo').resolve()), 'env': command[1:python],
            'pytest_args': shlex.join(command[python + 6:]),  # after "python -m pytest -q -p no:cacheprovider"
            'steps': [{'id': str(index), 'objective': text} for index, text in enumerate(steps, 1)]}
    path = Path(args.state) / 'queues' / f'{commit}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec, indent=1) + '\n')
    return path


def done(results):
    if not Path(results).exists():
        return set()
    return {(row['commit'], row['arm']) for row in map(json.loads, Path(results).read_text().splitlines()) if row.get('scored')}


def run(args, commit, arm):
    config = Path(args.state) / f'config-{arm}.json'
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps(dict(json.loads(Path(args.config).read_text()), **ARMS[arm])))
    state = Path(args.state) / arm
    environment = (Path(args.tasks) / commit / 'environment.txt').read_text().strip()
    queue = Path(args.state) / 'queues' / commit
    if arm == 'queued':
        command = [sys.executable, '-m', 'gflo', '--state', str(state), '--config', str(config), 'queue', 'run',
                   str(queue_spec(args, commit)), '--out', str(queue), '--environment', environment, '--environment-store', args.store]
    else:
        command = [sys.executable, '-m', 'gflo', '--state', str(state), '--config', str(config), 'run',
                   str(Path(args.tasks) / commit / 'task.json'), '--environment', environment, '--environment-store', args.store]
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
    row = {'commit': commit, 'arm': arm, 'exit_code': exit_code, 'elapsed_s': elapsed, 'scored': False}
    if arm == 'queued':
        if not (queue / 'queue.json').exists():
            return dict(row, run=None)
        done = json.loads((queue / 'queue.json').read_text())['done']
        steps = len(json.loads(Path(args.steps).read_text())[commit])
        committed = sum(bool(value.get('commit')) for value in done.values())
        stopped = [value['status'] for value in done.values() if not value.get('commit')]
        row.update(run=str(queue), steps=steps, committed=committed, step_runs=[value.get('run') for value in done.values()])
        try:
            row.update(score_tree(args.mined, args.tasks, args.store, commit, queue / 'integration', 'queued',
                                  'accepted' if committed == steps else (stopped or ['not started'])[0], len(done)))
            row.pop('tail', None)
            row['scored'] = committed == steps or bool(stopped) and stopped[0] in FINAL
        except Exception as error:  # keep the row; a scoring failure is evidence too
            row['score_error'] = f'{type(error).__name__}: {error}'[:500]
        return row
    found = re.search(r'^Run: ([0-9a-f]{12})$', log.read_text(), re.M)
    row['run'] = found.group(1) if found else None
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
    parser.add_argument('--steps', help='Chain step objectives for the queued arm')
    parser.add_argument('--timeout', type=int, default=4 * 3600)
    args = parser.parse_args()
    unknown = set(args.arms.split(',')) - set(ARMS)
    if unknown:
        parser.error('unknown arms: ' + ', '.join(sorted(unknown)) + '; known: ' + ', '.join(ARMS))
    if 'queued' in args.arms.split(',') and not args.steps:
        parser.error('the queued arm needs --steps')
    finished = done(args.results)
    for arm in args.arms.split(','):
        for commit in args.commits.split(','):
            if (commit, arm) in finished:
                continue
            row = run(args, commit, arm)
            with open(args.results, 'a') as output:
                output.write(json.dumps(row) + '\n')
            print(json.dumps({k: row.get(k) for k in ('commit', 'arm', 'factory_status', 'hidden_pass', 'delivered', 'elapsed_s')}), flush=True)
