"""Trusted, bounded preparation recipes and offline environment checks."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

from .environment import EnvironmentStore, discard, encoded
from .guard import run
from .sandbox import DEFAULT_IMAGE


PYTHON_SMOKE = '''import json, platform, sqlite3, ssl, sys
assert sys.version_info[:2] == (3, 12), 'Python 3.12 required'
with sqlite3.connect(':memory:') as db:
    assert db.execute('select 6 * 7').fetchone()[0] == 42
print(json.dumps({'python': platform.python_version(), 'platform': sys.platform,
                  'machine': platform.machine()}))
'''
EMPTY_ARCHIVE = "import sys,tarfile; tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.USTAR_FORMAT).close()"
RECIPE = {'profile': 'python-stdlib', 'version': 1, 'image': DEFAULT_IMAGE,
          'smoke': PYTHON_SMOKE, 'archive': EMPTY_ARCHIVE,
          'limits': {'memory': '1g', 'cpus': '1', 'pids': '128', 'shm': '16m',
                     'work': '480m', 'tmp': '16m'}}


@contextmanager
def preparation(store):
    """Own full preparation lifetime, separate from the publication lease."""
    with (store.root / '.preparation.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another environment preparation owns this store') from None
        for stale in store.root.glob('.work-*'):
            discard(stale)
        work = Path(tempfile.mkdtemp(prefix='.work-', dir=store.root))
        try:
            yield work
        finally:
            discard(work)


def execute(image, command, work, *, dependencies=None, output=None, timeout=60, cancelled=lambda: False):
    if cancelled():
        raise ValueError('Environment preparation cancelled')
    name = 'gflo-prepare-' + uuid.uuid4().hex[:16]
    inspection = work / (name + '.json')
    args = ['docker', 'run', '--rm', '--pull', 'never', '--name', name,
            '--runtime', 'runc', '--network', 'none', '--read-only',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--memory', '1g', '--memory-swap', '1g', '--cpus', '1',
            '--pids-limit', '128', '--shm-size', '16m',
            '--user', f'{os.getuid()}:{os.getgid()}', '--init',
            '--tmpfs', '/work:rw,nosuid,nodev,size=480m,mode=1777',
            '--tmpfs', '/tmp:rw,nosuid,nodev,size=16m,mode=1777',
            '--workdir', '/work', '--env', 'HOME=/tmp',
            '--env', 'PYTHONDONTWRITEBYTECODE=1', '--env', 'PYTHONPATH=/opt/deps',
            '--env', 'PIP_CONFIG_FILE=/dev/null', '--env', 'PIP_NO_INDEX=1']
    if dependencies is not None:
        args += ['--mount', f'type=bind,src={dependencies},dst=/opt/deps,readonly']
    args += [image, *command]
    result = run(args, name, timeout, output=output, max_output_bytes=128 * 1024 * 1024,
                 cancelled=cancelled, inspect_path=inspection)
    if result['exit_code']:
        raise ValueError(f"Environment container failed ({result['exit_code']}): {result['output']}")
    if cancelled():
        raise ValueError('Environment preparation cancelled')
    actual = json.loads(inspection.read_text())
    if actual['image'] != image:
        raise ValueError('Environment executor image changed')
    # Container names and private staging paths are execution locations, not
    # recipe identity. Preserve observed destination/type/access in the receipt.
    actual.pop('name')
    actual['config']['Env'] = sorted(actual['config']['Env'])
    actual['mounts'].sort(key=lambda mount: mount['Destination'])
    for mount in actual['mounts']:
        mount.pop('Source', None)
    return result, actual


def check(environment, *, cancelled=lambda: False):
    store = EnvironmentStore(environment.store)
    environment = store.resolve(environment.id, environment.receipt_hash)
    if environment.profile != 'python-stdlib':
        raise ValueError('Unsupported environment check profile')
    with preparation(store) as work:
        return smoke(environment.image, environment.dependencies, work, cancelled=cancelled)


def smoke(image, dependencies, work, *, timeout=60, cancelled=lambda: False):
    result, actual = execute(image, ['python', '-B', '-c', PYTHON_SMOKE], work,
                             dependencies=dependencies, timeout=timeout, cancelled=cancelled)
    runtime = json.loads(result['output'])
    if runtime['platform'] != 'linux' or runtime['machine'] != 'x86_64':
        raise ValueError('Unsupported environment runtime platform')
    return {'passed': True, 'runtime': runtime, 'executor': actual}


def prepare(store, profile, *, timeout=180, cancelled=lambda: False):
    if profile != 'python-stdlib':
        raise ValueError('Unsupported environment profile; currently implemented: python-stdlib')
    deadline = time.monotonic() + timeout
    def remaining():
        left = deadline - time.monotonic()
        if left <= 0:
            raise ValueError('Environment preparation deadline exceeded')
        return left
    installed = subprocess.run(['docker', 'image', 'inspect', DEFAULT_IMAGE, '--format', '{{.Id}}'],
                               capture_output=True, text=True, timeout=min(20, remaining()))
    if installed.returncode or installed.stdout.strip() != DEFAULT_IMAGE:
        raise ValueError('Approved Python base image is missing; provision it before preparation')
    with preparation(store) as work:
        initial = smoke(DEFAULT_IMAGE, None, work, timeout=remaining(), cancelled=cancelled)
        metadata = {'profile': profile, 'image': DEFAULT_IMAGE, 'platform': 'linux/amd64',
                    'recipe_sha256': hashlib.sha256(encoded(RECIPE)).hexdigest(),
                    'locks': {}, 'runtime': initial['runtime']}
        with tempfile.TemporaryFile(dir=work) as archive:
            execute(DEFAULT_IMAGE, ['python', '-B', '-c', EMPTY_ARCHIVE], work,
                    output=archive, timeout=remaining(), cancelled=cancelled)
            archive.seek(0)
            return store.publish(archive, metadata,
                lambda dependencies: smoke(DEFAULT_IMAGE, dependencies, work,
                                           timeout=remaining(), cancelled=cancelled),
                cancelled=lambda: cancelled() or time.monotonic() >= deadline)
