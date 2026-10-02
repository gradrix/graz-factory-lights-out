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
from .artifacts import unpack_archive
from .guard import run
from .sandbox import DEFAULT_IMAGE


RECIPES = Path(__file__).parent / 'recipes'
NODE_IMAGE = 'sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0'


PYTHON_SMOKE = '''import json, os, platform, sqlite3, ssl, sys
from pathlib import Path
assert os.getuid() != 0, 'nonroot execution required'
assert not list(Path('/dev').glob('nvidia*')), 'GPU device exposed'
assert not Path('/var/run/docker.sock').exists(), 'Docker socket exposed'
status = dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines())
assert int(status['CapEff'].strip(),16) == 0 and status['NoNewPrivs'].strip() == '1'
assert 'eth0' not in Path('/proc/net/route').read_text(), 'offline smoke has network route'
assert sys.version_info[:2] == (3, 12), 'Python 3.12 required'
with sqlite3.connect(':memory:') as db:
    assert db.execute('select 6 * 7').fetchone()[0] == 42
runtime = {'python': platform.python_version(), 'platform': sys.platform,
           'machine': platform.machine(), 'uid': str(os.getuid()),
           'capabilities': status['CapEff'].strip(), 'gpu_devices': 'absent', 'docker_socket': 'absent'}
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


def execute(image, command, work, *, dependencies=None, output=None, timeout=60, cancelled=lambda: False,
            profile="python-stdlib", helper=None, approved=None, artifacts=None, inputs=None, online=False):
    if cancelled():
        raise ValueError('Environment preparation cancelled')
    name = 'gflo-prepare-' + uuid.uuid4().hex[:16]
    inspection = work / (name + '.json')
    args = ['docker', 'run', '--rm', '--pull', 'never', '--name', name,
            '--runtime', 'runc', '--network', 'bridge' if online else 'none', '--read-only',
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
        target = '/node_modules' if profile == 'node-ts' else '/opt/deps'
        args += ['--mount', f'type=bind,src={dependencies},dst={target},readonly']
    for source, target in [(helper, '/recipe'), (approved, '/approved'), (artifacts, '/artifacts'), (inputs, '/inputs')]:
        if source is not None:
            args += ['--mount', f'type=bind,src={Path(source).absolute()},dst={target},readonly']
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
    with preparation(store) as work:
        return smoke(environment.image, environment.dependencies, work, profile=environment.profile, cancelled=cancelled)


def smoke(image, dependencies, work, *, profile='python-stdlib', timeout=60, cancelled=lambda: False):
    helper = None
    if profile == 'node-ts':
        command = ['node', '/recipe']
        helper = RECIPES / profile / 'smoke.js'
    else:
        code = PYTHON_SMOKE
        if profile == 'python-api':
            code += "import importlib.metadata as m; runtime.update({p:m.version(p) for p in ['fastapi','uvicorn','pydantic','httpx','setuptools']})\n"
        code += "print(json.dumps(runtime))\n"
        command = ['python', '-B', '-c', code]
    result, actual = execute(image, command, work, profile=profile, helper=helper,
                             dependencies=dependencies, timeout=timeout, cancelled=cancelled)
    runtime = json.loads(result['output'])
    if runtime['platform'] != 'linux' or runtime['machine'] not in ('x86_64', 'x64'):
        raise ValueError('Unsupported environment runtime platform')
    return {'passed': True, 'runtime': runtime, 'executor': actual}


def prepare(store, profile, *, timeout=180, cancelled=lambda: False):
    if profile not in ('python-stdlib', 'python-api', 'node-ts'):
        raise ValueError('Unsupported environment profile; choose python-stdlib, python-api or node-ts')
    deadline = time.monotonic() + timeout
    def remaining():
        left = deadline - time.monotonic()
        if left <= 0:
            raise ValueError('Environment preparation deadline exceeded')
        return left
    image = NODE_IMAGE if profile == 'node-ts' else DEFAULT_IMAGE
    for base in sorted({image, DEFAULT_IMAGE}):
        installed = subprocess.run(['docker', 'image', 'inspect', base, '--format', '{{.Id}}'],
                                   capture_output=True, text=True, timeout=min(20, remaining()))
        if installed.returncode or installed.stdout.strip() != base:
            raise ValueError('Approved base image is missing; provision it before preparation: ' + base)
    with preparation(store) as work:
        approved = None if profile == 'python-stdlib' else RECIPES / profile
        metadata = {'profile': profile, 'image': image, 'platform': 'linux/amd64',
                    'recipe_sha256': hashlib.sha256(encoded({'recipe': RECIPE, 'preparer': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})).hexdigest(), 'locks': {}}
        preparation_evidence = {'bases_reused': sorted({image, DEFAULT_IMAGE}), 'package_cache': 'fresh disposable scratch'}
        if approved is not None:
            inputs = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(approved.iterdir())}
            recipe = {'version': 2, 'image': image, 'fetch_image': DEFAULT_IMAGE, 'files': inputs,
                      'preparer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      'fetch_sha256': hashlib.sha256((RECIPES / 'fetch.py').read_bytes()).hexdigest()}
            metadata['recipe_sha256'] = hashlib.sha256(encoded(recipe)).hexdigest()
            metadata['inputs'] = inputs
            metadata['locks'] = {name: digest for name, digest in inputs.items() if name in ('requirements.lock', 'package-lock.json', 'package.json', 'artifacts.json')}
            with tempfile.TemporaryFile(dir=work) as fetched:
                _, preparation_evidence['fetch_executor'] = execute(DEFAULT_IMAGE, ['python', '-B', '/recipe'], work, helper=RECIPES / 'fetch.py',
                        approved=approved, online=True, output=fetched, timeout=remaining(), cancelled=cancelled)
                fetched.seek(0)
                artifacts = unpack_archive(fetched, work / 'artifacts')
            specs = json.loads((approved / 'artifacts.json').read_text())
            if sorted(p.name for p in artifacts.iterdir()) != sorted(spec['filename'] for spec in specs):
                raise ValueError('Fetched artifact set does not match approved lock')
            metadata['artifacts'] = {}
            for spec in specs:
                data = (artifacts / spec['filename']).read_bytes()
                digest = hashlib.new(spec['algorithm'], data).hexdigest()
                if digest != spec['digest'] or len(data) > spec['max_bytes']:
                    raise ValueError('Fetched artifact hash or size does not match approved lock')
                metadata['artifacts'][spec['filename']] = spec['algorithm'] + ':' + digest
            helper = approved / ('assemble.js' if profile == 'node-ts' else 'assemble.py')
            command = ['node' if profile == 'node-ts' else 'python', '/recipe']
        else:
            artifacts = helper = None
            command = ['python', '-B', '-c', EMPTY_ARCHIVE]
        with tempfile.TemporaryFile(dir=work) as archive:
            _, preparation_evidence['assembly_executor'] = execute(image, command, work, helper=helper, approved=approved, artifacts=artifacts,
                    output=archive, timeout=remaining(), cancelled=cancelled)
            archive.seek(0)
            # Probe the exact extracted snapshot offline before constructing its
            # metadata, then smoke again in the publication transaction.
            dependencies = unpack_archive(archive, work / 'probe-deps')
            initial = smoke(image, dependencies, work, profile=profile, timeout=remaining(), cancelled=cancelled)
            metadata['runtime'] = initial['runtime']
            archive.seek(0)
            def verify(dependencies):
                result = smoke(image, dependencies, work, profile=profile, timeout=remaining(), cancelled=cancelled)
                result['preparation'] = preparation_evidence
                return result
            return store.publish(archive, metadata, verify,
                cancelled=lambda: cancelled() or time.monotonic() >= deadline)


def validate_project(store, profile, project):
    """Copy and parse only bounded manifest inputs in the approved interpreter."""
    project = Path(project).resolve()
    if profile == 'python-stdlib':
        if any((project / name).exists() for name in ('pyproject.toml', 'requirements.txt', 'package.json', 'setup.py', 'setup.cfg')):
            raise ValueError('The stdlib profile supports projects without package declarations; choose a supported packaged profile')
        return {}
    names = {'python-api': ['pyproject.toml'], 'node-ts': ['package.json', 'package-lock.json']}.get(profile)
    if names is None:
        raise ValueError('Unsupported environment profile')
    with preparation(store) as work:
        inputs = work / 'inputs'
        inputs.mkdir()
        hashes = {}
        for name in names:
            source = project / name
            if source.is_symlink() or not source.is_file() or source.stat().st_size > 65536:
                raise ValueError('Missing, linked or oversized required manifest: ' + name)
            data = source.read_bytes()
            if len(data) > 65536:
                raise ValueError('Manifest grew beyond 64 KiB: ' + name)
            (inputs / name).write_bytes(data)
            hashes[name] = hashlib.sha256(data).hexdigest()
        execute(DEFAULT_IMAGE, ['python', '-B', '/recipe', profile], work,
                helper=RECIPES / 'validate.py', inputs=inputs, approved=RECIPES / profile)
        return hashes


def infer_profile(project):
    project = Path(project)
    python = (project / 'pyproject.toml').exists()
    node = (project / 'package.json').exists()
    if python and node:
        raise ValueError('Mixed Python/Node projects require an explicit supported task profile')
    return 'node-ts' if node else 'python-api' if python else 'python-stdlib'
