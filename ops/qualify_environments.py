#!/usr/bin/env python3
"""Run the three frozen environment tasks with local coding and independent review."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

from gflo.environment import EnvironmentStore
from gflo.prepare import check
from gflo.review import Reviewer
from gflo.runner import Factory, save
from gflo.sandbox import Sandbox
from gflo.worker import ModelWorker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixtures', type=Path)
    parser.add_argument('preparation', type=Path, help='Cold preparation report with three checked receipt IDs')
    parser.add_argument('state', type=Path)
    parser.add_argument('--store', required=True, type=Path)
    parser.add_argument('--config', required=True, type=Path)
    args = parser.parse_args()
    if args.state.exists():
        raise ValueError('Choose an unused qualification state directory')
    manifest = json.loads((args.fixtures / 'manifest.json').read_text())
    if manifest.get('cohort') != 'environment-coding-private' or manifest.get('version') != 2:
        raise ValueError('Qualification requires frozen environment cohort v2')
    for name, expected in manifest['sha256'].items():
        if hashlib.sha256((args.fixtures / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen fixture changed: ' + name)
    config = json.loads(args.config.read_text())
    if config.get('api_key_file'):
        config['api_key_file'] = str((args.config.resolve().parent / config['api_key_file']).resolve())
    preparation = json.loads(args.preparation.read_text())
    rows = {row['profile']: row for row in preparation['profiles']}
    profiles = ('python-stdlib', 'python-api', 'node-ts')
    if set(rows) != set(profiles) or any(row.get('exit_code') != 0 or row.get('check_exit_code') != 0 for row in rows.values()):
        raise ValueError('All three cold preparations must pass before model work')
    store = EnvironmentStore(args.store)
    receipt = {'fixture_sha256': hashlib.sha256((args.fixtures / 'manifest.json').read_bytes()).hexdigest(),
               'preparation_sha256': hashlib.sha256(args.preparation.read_bytes()).hexdigest(),
               'source': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(Path('gflo').rglob('*')) if p.is_file() and '__pycache__' not in str(p)},
               'model': config['model'], 'reasoning_effort': config.get('reasoning', 'none'),
               'results': []}
    for profile in profiles:
        environment = store.resolve(rows[profile]['id'])
        if environment.profile != profile or environment.image != manifest['images'][profile]:
            raise ValueError('Prepared environment does not match frozen task runtime')
        runtime = check(environment)
        if not runtime['passed']:
            raise ValueError('Offline environment recheck failed')
        sandbox = Sandbox(config.get('image', Sandbox().image))
        sandbox.bind(environment)
        client = ModelWorker(config, sandbox)
        factory = Factory(args.state, None, sandbox.verify, cleanup=sandbox.cleanup,
                          reviewer=Reviewer(client), environment=environment, bind_environment=sandbox.bind)
        run = factory.create(args.fixtures / 'tasks' / profile / 'task.json')
        root = factory.state / run
        print(json.dumps({'profile': profile, 'run': run, 'status': 'started'}), flush=True)
        started, timed_out = time.monotonic(), False
        with (root / 'cli.log').open('w') as log:
            process = subprocess.Popen([sys.executable, '-m', 'gflo', '--state', str(factory.state),
                        '--config', str(args.config.resolve()), 'resume', run], stdout=log, stderr=subprocess.STDOUT)
            try:
                process.wait(timeout=900)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=45)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
        result = factory.status(run)
        task = json.loads((root / 'task.json').read_text())
        external = sandbox.verify(root / 'workspace', task, root / 'acceptance') if result['status'] == 'accepted' else None
        if external is not None:
            save(root / 'qualification-check.json', external)
        reviews = [json.loads(p.read_text()) for p in sorted((root / 'attempts').glob('*/review.json'))]
        row = {'profile': profile, 'run': run, 'environment': environment.id,
               'status': result['status'], 'attempts': result['attempts'], 'timeout': timed_out,
               'elapsed_s': round(time.monotonic() - started, 2), 'cli_exit_code': process.returncode,
               'review_decisions': [review['decision'] for review in reviews],
               'independent_checks_passed': None if external is None else external['passed']}
        receipt['results'].append(row)
        save(factory.state / 'qualification.json', receipt)
        print(json.dumps(row), flush=True)
    receipt['gate_passed'] = all(row['status'] == 'accepted' and row['independent_checks_passed'] and not row['timeout']
                                 for row in receipt['results'])
    save(args.state / 'qualification.json', receipt)
    return 0 if receipt['gate_passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
