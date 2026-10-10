"""Offline command execution and independent acceptance checks."""
import hashlib
import os
from pathlib import Path
import subprocess
import uuid

from .guard import run as guarded_run
from .environment import EnvironmentStore

DEFAULT_IMAGE = 'sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'


PACKAGE_TESTS = """import os, pathlib, shutil, subprocess, sys, tempfile
with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    project, installed, wheels = root/'project', root/'installed', root/'wheels'
    shutil.copytree('/workspace', project, ignore=shutil.ignore_patterns('__pycache__', '.git'))
    subprocess.run([sys.executable, '-m', 'pip', 'wheel', str(project), '--no-index',
                    '--no-deps', '--no-build-isolation', '--wheel-dir', str(wheels)], check=True, cwd=root)
    built = list(wheels.glob('*.whl'))
    if len(built) != 1: raise ValueError('Project must produce one wheel')
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps',
                    '--target', str(installed), str(built[0])], check=True, cwd=root)
    env = dict(os.environ, PYTHONPATH=str(installed)+os.pathsep+'/opt/deps')
    subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(project/'tests')],
                   check=True, cwd=root, env=env)
"""


class Sandbox:
    def __init__(self, image=DEFAULT_IMAGE):
        if not (image.startswith('sha256:') or '@sha256:' in image):
            raise ValueError('Sandbox image must be pinned by digest or local image ID')
        self.image = image
        self.environment = None
        self.observe = lambda *a, **kw: None

    def bind(self, environment):
        self.environment = environment
        if environment is not None:
            self.environment = EnvironmentStore(environment.store).resolve(environment.id, environment.receipt_hash)

    def cleanup(self, workspace):
        label = hashlib.sha256(str(Path(workspace).resolve()).encode()).hexdigest()
        result = subprocess.run(['docker', 'ps', '-aq', '--filter', 'label=gflo.workspace=' + label],
                                capture_output=True, text=True, timeout=15, check=True)
        ids = result.stdout.split()
        if ids:
            subprocess.run(['docker', 'rm', '-f', *ids], capture_output=True, timeout=30, check=True)

    def execute(self, workspace, command, *, acceptance=None, timeout=60, readonly=False):
        workspace = Path(workspace).resolve()
        environment = self.environment
        if environment is not None:
            environment = EnvironmentStore(environment.store).resolve(environment.id, environment.receipt_hash)
        image = environment.image if environment is not None else self.image
        name = 'gflo-job-' + uuid.uuid4().hex[:16]
        label = hashlib.sha256(str(workspace).encode()).hexdigest()
        args = ['docker', 'run', '--rm', '--pull', 'never', '--name', name,
                '--label', 'gflo.workspace=' + label, '--network', 'none', '--runtime', 'runc',
                '--shm-size', '16m',
                '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--memory', '1g', '--memory-swap', '1g', '--cpus', '2', '--pids-limit', '128',
                '--user', f'{os.getuid()}:{os.getgid()}', '--init',
                '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m',
                '--env', 'PYTHONDONTWRITEBYTECODE=1', '--env', 'HOME=/tmp',
                '--mount', f'type=bind,src={workspace},dst=/workspace' + (',readonly' if acceptance or readonly else ''),
                '--workdir', '/workspace']
        if acceptance:
            args += ['--mount', f'type=bind,src={Path(acceptance).resolve()},dst=/acceptance,readonly']
        if environment is not None:
            target = '/node_modules' if environment.profile == 'node-ts' else '/opt/deps'
            args += ['--mount', f'type=bind,src={environment.dependencies},dst={target},readonly']
            if environment.profile != 'node-ts':
                args += ['--env', 'PYTHONPATH=/opt/deps']
        args += [image, *command]
        self.observe('container_running', name=name, timeout_s=timeout, readonly=bool(acceptance or readonly))
        result = None
        try:
            result = guarded_run(args, name, timeout)
        finally:
            self.observe('container_finished', name=name,
                         exit_code=None if result is None else result['exit_code'])
        return {'command': command, 'image': image,
                **{key: result[key] for key in ('exit_code', 'timed_out', 'output', 'elapsed_s')}}

    def verify(self, workspace, task, acceptance):
        self.cleanup(workspace)
        if self.environment is not None:
            for name, digest in task.get('environment_inputs', {}).items():
                path = Path(workspace) / name
                if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536 or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    return {'passed': False, 'checks': [{'exit_code': 1, 'output': 'Frozen environment manifest changed: ' + name}]}
            if self.environment.profile == 'python-project':
                from .prepare import manifest_names
                added = sorted(set(manifest_names(workspace)) - set(task.get('environment_inputs', {})))
                if added:
                    return {'passed': False, 'checks': [{'exit_code': 1, 'output': 'Dependency manifest added after the environment was frozen: ' + ', '.join(added)}]}
        commands = list(task['checks'])
        # The current profile is Python stdlib. Generated regressions supplement
        # the immutable external checks and must not be silently left unexecuted.
        if task.get('test_command'):
            # The operator names how this project runs its own and generated tests.
            commands.append(list(task['test_command']))
        elif (self.environment is None or self.environment.profile != 'node-ts') and (Path(workspace) / 'tests').is_dir():
            if self.environment is not None and self.environment.profile == 'python-api':
                commands.append(['python', '-B', '-c', PACKAGE_TESTS])
            elif self.environment is not None and self.environment.profile == 'python-project':
                commands.append(['python', '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests'])
            else:
                commands.append(['python', '-B', '-m', 'unittest', 'discover', '-s', 'tests'])
        # Real project suites (python-project) need longer than the bounded fixture checks.
        timeout = 900 if self.environment is not None and self.environment.profile == 'python-project' else 120
        results = [self.execute(workspace, command, acceptance=acceptance, timeout=timeout)
                   for command in commands]
        return {'passed': bool(results) and all(r['exit_code'] == 0 for r in results), 'checks': results}
