"""Offline command execution and independent acceptance checks."""
import hashlib
import json
import sys
import os
from pathlib import Path
import subprocess
import threading
import time
import uuid

DEFAULT_IMAGE = 'sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578'


class Sandbox:
    def __init__(self, image=DEFAULT_IMAGE):
        if not (image.startswith('sha256:') or '@sha256:' in image):
            raise ValueError('Sandbox image must be pinned by digest or local image ID')
        self.image = image
        self.observe = lambda *a, **kw: None

    def cleanup(self, workspace):
        label = hashlib.sha256(str(Path(workspace).resolve()).encode()).hexdigest()
        result = subprocess.run(['docker', 'ps', '-aq', '--filter', 'label=gflo.workspace=' + label],
                                capture_output=True, text=True, timeout=15, check=True)
        ids = result.stdout.split()
        if ids:
            subprocess.run(['docker', 'rm', '-f', *ids], capture_output=True, timeout=30, check=True)

    def execute(self, workspace, command, *, acceptance=None, timeout=60):
        workspace = Path(workspace).resolve()
        name = 'gflo-job-' + uuid.uuid4().hex[:16]
        label = hashlib.sha256(str(workspace).encode()).hexdigest()
        args = ['docker', 'run', '--rm', '--pull', 'never', '--name', name,
                '--label', 'gflo.workspace=' + label, '--network', 'none',
                '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--memory', '1g', '--memory-swap', '1g', '--cpus', '2', '--pids-limit', '128',
                '--user', f'{os.getuid()}:{os.getgid()}', '--init',
                '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m',
                '--env', 'PYTHONDONTWRITEBYTECODE=1', '--env', 'HOME=/tmp',
                '--mount', f'type=bind,src={workspace},dst=/workspace' + (',readonly' if acceptance else ''),
                '--workdir', '/workspace']
        if acceptance:
            args += ['--mount', f'type=bind,src={Path(acceptance).resolve()},dst=/acceptance,readonly']
        args += [self.image, *command]
        started = time.monotonic()
        self.observe('container_running', name=name, timeout_s=timeout, readonly=bool(acceptance))
        process = subprocess.Popen([sys.executable, '-m', 'gflo.guard'], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        process.stdin.write((json.dumps({'args': args, 'name': name, 'timeout': timeout}) + '\n').encode())
        process.stdin.flush()
        tail = bytearray()
        count = [0]

        def drain():
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    return
                count[0] += len(chunk)
                tail.extend(chunk)
                if len(tail) > 16384:
                    del tail[:-16384]

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        try:
            process.wait(timeout=timeout + 45)
        finally:
            process.stdin.close()  # EOF tells the guardian to stop even during cancellation.
            try:
                process.wait(timeout=45)
            except subprocess.TimeoutExpired:
                # Fail closed: do not continue verification after a stuck cleanup.
                self.cleanup(workspace)
                process.kill()
                process.wait(timeout=10)
                raise RuntimeError('Container guardian did not stop')
            reader.join(timeout=10)
            process.stdout.close()
            self.observe('container_finished', name=name, exit_code=process.returncode)
        timed_out = process.returncode == 124
        output = tail.decode(errors='replace')
        if count[0] > 16384:
            output = f'[truncated {count[0] - 16384} bytes]\n' + output
        return {'command': command, 'exit_code': 124 if timed_out else process.returncode,
                'timed_out': timed_out, 'output': output, 'elapsed_s': time.monotonic() - started,
                'image': self.image}

    def verify(self, workspace, task, acceptance):
        self.cleanup(workspace)
        commands = list(task['checks'])
        # The current profile is Python stdlib. Generated regressions supplement
        # the immutable external checks and must not be silently left unexecuted.
        if (Path(workspace) / 'tests').is_dir():
            commands.append(['python', '-B', '-m', 'unittest', 'discover', '-s', 'tests'])
        results = [self.execute(workspace, command, acceptance=acceptance, timeout=120)
                   for command in commands]
        return {'passed': bool(results) and all(r['exit_code'] == 0 for r in results), 'checks': results}
