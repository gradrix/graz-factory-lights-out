#!/usr/bin/env python3
"""Run a frozen coding set on the local model with required independent review.

Each task has its frozen attempt/turn budget plus a 900-second qualification
wall limit. Keep failures; never rewrite acceptance after observing results.
"""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

from gflo.review import Reviewer
from gflo.runner import Factory, save
from gflo.sandbox import Sandbox
from gflo.worker import ModelWorker


def environment_check(sandbox, expected=None):
    """Record the interpreter that executes checks, not the host or an image tag."""
    if expected is not None and (not isinstance(expected, dict) or any(
            not isinstance(expected.get(key), str) or not expected[key]
            for key in ('image', 'version', 'implementation'))):
        raise ValueError('Manifest environment needs image, version and implementation strings')
    with tempfile.TemporaryDirectory(prefix='gflo-qualification-') as directory:
        check = sandbox.execute(Path(directory), ['python', '-c',
            'import json,platform,sys;print(json.dumps(dict(version=platform.python_version(),'
            'implementation=platform.python_implementation(),sys_version=sys.version)))'])
    observed = {'image': check['image']}
    errors = []
    if check['exit_code']:
        errors.append('Sandbox interpreter probe failed; inspect check output')
    else:
        try:
            runtime = json.loads(check['output'])
            if not isinstance(runtime, dict) or any(
                    not isinstance(runtime.get(key), str) or not runtime[key]
                    for key in ('version', 'implementation', 'sys_version')):
                raise ValueError('Incomplete interpreter result')
            observed.update(runtime)
        except (ValueError, TypeError):
            errors.append('Sandbox interpreter probe returned invalid runtime facts')
    if expected:
        for key in ('image', 'version', 'implementation'):
            if observed.get(key) != expected[key]:
                errors.append(f'{key}: expected {expected[key]!r}, observed {observed.get(key)!r}')
    return {'passed': not errors, 'expected': expected, 'observed': observed,
            'error': '; '.join(errors), 'check': check}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixtures', type=Path)
    parser.add_argument('state', type=Path)
    parser.add_argument('--config', type=Path, default=Path('.gflo/config.json'))
    args = parser.parse_args()
    if args.state.exists():
        raise ValueError('Choose a new qualification state directory; existing evidence is never overwritten')
    config = json.loads(args.config.read_text())
    if config.get('api_key_file'):
        config['api_key_file'] = str((args.config.resolve().parent / config['api_key_file']).resolve())
    manifest = json.loads((args.fixtures / 'manifest.json').read_text())
    for name, expected in manifest['sha256'].items():
        assert hashlib.sha256((args.fixtures / name).read_bytes()).hexdigest() == expected, name
    sandbox = Sandbox(config.get('image', Sandbox().image))
    environment = environment_check(sandbox, manifest.get('environment'))
    save(args.state / 'environment.json', environment)
    if not environment['passed']:
        print('Qualification environment mismatch: ' + environment['error'], file=sys.stderr)
        return 2
    factory = Factory(args.state, None, None, reviewer=Reviewer(ModelWorker(config, sandbox)))
    receipt = {'manifest_sha256': hashlib.sha256((args.fixtures / 'manifest.json').read_bytes()).hexdigest(),
               'environment': environment, 'wall_budget_s_per_task': 900, 'results': []}
    task_dir = args.fixtures / ('coding' if (args.fixtures / 'coding').is_dir() else 'tasks')
    coding_paths = sorted(task_dir.glob('*/task.json'))
    if len(coding_paths) != 12:
        raise ValueError('Qualification requires exactly twelve frozen coding tasks')
    paths = coding_paths + [args.fixtures / 'ambiguous/task.json']
    for path in paths:
        run = factory.create(path)
        root = factory.state / run
        print(json.dumps({'task':path.parent.name, 'run':run, 'status':'started'}), flush=True)
        started = time.monotonic(); timeout = False
        with (root / 'cli.log').open('w') as log:
            process = subprocess.Popen([sys.executable, '-m', 'gflo', '--state', str(factory.state), '--config', str(args.config.resolve()), 'resume', run], stdout=log, stderr=subprocess.STDOUT)
            try:
                process.wait(timeout=900)
            except subprocess.TimeoutExpired:
                timeout = True
                process.send_signal(signal.SIGINT)
                try: process.wait(timeout=45)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
        result = factory.status(run)
        task = json.loads((root / 'task.json').read_text())
        # Independently repeat the frozen executable oracle after the controller.
        external = sandbox.verify(root / 'workspace', task, root / 'acceptance') if result['status'] == 'accepted' else None
        reviews = [json.loads(p.read_text()) for p in sorted((root / 'attempts').glob('*/review.json'))]
        report = {'task': path.parent.name, 'run':run, 'status':result['status'], 'attempts':result['attempts'],
                  'elapsed_s':round(time.monotonic()-started,2), 'timeout':timeout,
                  'question':result['message'] if result['status']=='needs_input' else None,
                  'review_decisions':[r['decision'] for r in reviews],
                  'independent_checks_passed': None if external is None else external['passed']}
        receipt['results'].append(report)
        save(factory.state / 'qualification.json', receipt)
        print(json.dumps(report), flush=True)
    coding = receipt['results'][:-1]
    receipt['accepted'] = sum(r['status']=='accepted' and r['independent_checks_passed'] and not r['timeout'] for r in coding)
    receipt['ambiguity_stopped'] = receipt['results'][-1]['status']=='needs_input' and bool(receipt['results'][-1]['question'])
    receipt['gate_passed'] = receipt['accepted'] >= 10 and receipt['ambiguity_stopped'] and not any(r['status']=='accepted' and not r['independent_checks_passed'] for r in coding)
    save(factory.state / 'qualification.json', receipt)
    return 0 if receipt['gate_passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
