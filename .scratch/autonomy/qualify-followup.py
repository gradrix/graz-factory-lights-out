"""Qualify one frozen, independently reviewed follow-up without changing its budget."""
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

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('fixtures', type=Path)
p.add_argument('state', type=Path)
p.add_argument('--manifest-sha256', required=True)
p.add_argument('--environment', required=True)
p.add_argument('--store', required=True, type=Path)
p.add_argument('--config', required=True, type=Path)
p.add_argument('--task-relative', default='task.json')
p.add_argument('--image', help='Expected pinned image when the fixture manifest omits it')
a = p.parse_args()
if a.state.exists():
    raise ValueError('Use a new state directory')
manifest_path = a.fixtures / 'manifest.json'
assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == a.manifest_sha256
manifest = json.loads(manifest_path.read_text())
for name, digest in manifest.get('sha256', manifest.get('files', {})).items():
    assert hashlib.sha256((a.fixtures / name).read_bytes()).hexdigest() == digest, name
task_path = a.fixtures / a.task_relative
task = json.loads(task_path.read_text())
assert (task['max_attempts'], task['max_turns'], task['wall_time_seconds']) == (3, 24, 900)
config = json.loads(a.config.read_text())
if config.get('api_key_file'):
    config['api_key_file'] = str((a.config.resolve().parent / config['api_key_file']).resolve())
env = EnvironmentStore(a.store).resolve(a.environment)
assert env.profile == task['profile'] and check(env)['passed']
assert env.image == (a.image or manifest['environment']['image'])
sandbox = Sandbox()
sandbox.bind(env)
client = ModelWorker(config, sandbox)
factory = Factory(a.state, None, sandbox.verify, cleanup=sandbox.cleanup,
                  reviewer=Reviewer(client), environment=env, bind_environment=sandbox.bind)
run = factory.create(task_path)
root = factory.state / run
receipt = {'run': run, 'fixture_sha256': a.manifest_sha256, 'environment': env.id,
           'model': config['model'], 'reasoning_effort': config.get('reasoning', 'none'),
           'source': {str(f): hashlib.sha256(f.read_bytes()).hexdigest()
                      for f in sorted(Path('gflo').rglob('*')) if f.is_file() and '__pycache__' not in str(f)},
           'budget_s': 900, 'timeout': False}
serving = json.loads(subprocess.run(['docker', 'inspect', 'gflo-model'], capture_output=True,
                                   text=True, timeout=15, check=True).stdout)[0]
receipt['serving'] = {'container_id': serving['Id'], 'image': serving['Image'],
                      'command': serving['Config']['Cmd']}
save(factory.state / 'qualification.json', receipt)
print(json.dumps({'run': run, 'status': 'started'}), flush=True)
started = time.monotonic()
with (root / 'cli.log').open('w') as log:
    process = subprocess.Popen([sys.executable, '-m', 'gflo', '--state', str(factory.state),
                '--config', str(a.config.resolve()), 'resume', run], stdout=log, stderr=subprocess.STDOUT)
    try:
        process.wait(timeout=900)
    except subprocess.TimeoutExpired:
        receipt['timeout'] = True
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=45)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
receipt.update(elapsed_s=round(time.monotonic()-started, 2), cli_exit_code=process.returncode,
               result=factory.status(run))
if receipt['result']['status'] == 'accepted':
    receipt['external'] = sandbox.verify(root / 'workspace', json.loads((root / 'task.json').read_text()), root / 'acceptance')
receipt['passed'] = bool(not receipt['timeout'] and receipt.get('external', {}).get('passed'))
save(factory.state / 'qualification.json', receipt)
print(json.dumps({k: receipt[k] for k in ('run', 'elapsed_s', 'timeout', 'passed', 'result')}), flush=True)
raise SystemExit(0 if receipt['passed'] else 2)
