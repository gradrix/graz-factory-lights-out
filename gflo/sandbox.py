"""Offline command execution and independent acceptance checks."""
import hashlib
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
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
        timed_out = False
        try:
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
        finally:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            reader.join(timeout=10)
            process.stdout.close()
        output = tail.decode(errors='replace')
        if count[0] > 16384:
            output = f'[truncated {count[0] - 16384} bytes]\n' + output
        return {'command': command, 'exit_code': 124 if timed_out else process.returncode,
                'timed_out': timed_out, 'output': output, 'elapsed_s': time.monotonic() - started,
                'image': self.image}

    def verify(self, workspace, task, acceptance):
        self.cleanup(workspace)
        results = [self.execute(workspace, command, acceptance=acceptance, timeout=120)
                   for command in task['checks']]
        return {'passed': bool(results) and all(r['exit_code'] == 0 for r in results), 'checks': results}
