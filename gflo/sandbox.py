"""Offline command execution and independent acceptance checks."""
import hashlib
import os
from pathlib import Path
import subprocess
import uuid

from .guard import run as guarded_run
from .environment import EnvironmentStore

DEFAULT_IMAGE = 'sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'


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

    def execute(self, workspace, command, *, acceptance=None, timeout=60):
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
                '--mount', f'type=bind,src={workspace},dst=/workspace' + (',readonly' if acceptance else ''),
                '--workdir', '/workspace']
        if acceptance:
            args += ['--mount', f'type=bind,src={Path(acceptance).resolve()},dst=/acceptance,readonly']
        if environment is not None:
            target = '/node_modules' if environment.profile == 'node-ts' else '/opt/deps'
            args += ['--mount', f'type=bind,src={environment.dependencies},dst={target},readonly']
            if environment.profile != 'node-ts':
                args += ['--env', 'PYTHONPATH=/opt/deps']
        args += [image, *command]
        self.observe('container_running', name=name, timeout_s=timeout, readonly=bool(acceptance))
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
        commands = list(task['checks'])
        # The current profile is Python stdlib. Generated regressions supplement
        # the immutable external checks and must not be silently left unexecuted.
        if (self.environment is None or self.environment.profile != 'node-ts') and (Path(workspace) / 'tests').is_dir():
            commands.append(['python', '-B', '-m', 'unittest', 'discover', '-s', 'tests'])
        results = [self.execute(workspace, command, acceptance=acceptance, timeout=120)
                   for command in commands]
        return {'passed': bool(results) and all(r['exit_code'] == 0 for r in results), 'checks': results}
