#!/usr/bin/env python3
"""Bounded Stage 0 probes using local images; never downloads or starts a model."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid


SANDBOX_PROBE = r'''
import errno, json, os
from pathlib import Path
status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
try:
    Path('/gflo-write-probe').write_text('probe')
    readonly = False
except OSError as exc:
    readonly = exc.errno == errno.EROFS
print(json.dumps({
    'uid': os.getuid(),
    'capabilities': int(status['CapEff'].strip(), 16),
    'no_new_privileges': status['NoNewPrivs'].strip(),
    'seccomp': status['Seccomp'].strip(),
    'memory_max': Path('/sys/fs/cgroup/memory.max').read_text().strip(),
    'swap_max': Path('/sys/fs/cgroup/memory.swap.max').read_text().strip(),
    'pids_max': Path('/sys/fs/cgroup/pids.max').read_text().strip(),
    'cpu_max': Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
    'readonly_root': readonly,
    'interfaces': sorted(p.name for p in Path('/sys/class/net').iterdir()),
    'docker_socket_present': Path('/var/run/docker.sock').exists(),
}))
'''


def run(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'Command failed: ' + command[0])
    return result.stdout.strip()


def sandbox_checks(observed):
    expected = {
        'uid': 65534, 'capabilities': 0, 'no_new_privileges': '1',
        'seccomp': '2', 'memory_max': '134217728', 'swap_max': '0',
        'pids_max': '32', 'readonly_root': True, 'interfaces': ['lo'],
        'docker_socket_present': False,
    }
    checks = {key: observed.get(key) == value for key, value in expected.items()}
    try:
        quota, period = map(int, observed['cpu_max'].split())
        checks['cpu_limit'] = quota == period and period > 0
    except (KeyError, ValueError, AttributeError):
        checks['cpu_limit'] = False
    return checks


def container_probe(image, command, gpu=False):
    # Resolve a mutable local tag once, then execute that immutable image ID.
    identity = json.loads(run(['docker', 'image', 'inspect', image]))[0]
    name = 'gflo-target-probe-' + uuid.uuid4().hex
    args = ['docker', 'run', '--rm', '--pull', 'never', '--name', name,
            '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--memory', '128m',
            '--memory-swap', '128m', '--pids-limit', '32', '--cpus', '1',
            '--user', '65534:65534']
    if gpu:
        args += ['--gpus', 'device=0']
    args += ['--entrypoint', command[0], identity['Id'], *command[1:]]
    try:
        output = run(args)
    finally:
        # Timeout of the Docker client does not imply container termination.
        cleanup = subprocess.run(['docker', 'rm', '-f', name], capture_output=True,
                                 text=True, timeout=15)
        if cleanup.returncode and 'No such container' not in cleanup.stderr:
            raise RuntimeError('Probe cleanup failed: ' + cleanup.stderr.strip())
    return {'image_id': identity['Id'], 'repo_digests': identity.get('RepoDigests', []),
            'output': output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sandbox-image', required=True, help='Already installed Python 3 image')
    parser.add_argument('--gpu-image', required=True, help='Already installed image with nvidia-smi')
    args = parser.parse_args()
    report = {'schema_version': 1,
              'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'stage_0_complete': False,
              'limitations': ['No model loading or inference tested',
                              'Cgroup settings checked; OOM and fork-limit behavior not exercised',
                              'Disposable probe is not a validated worker broker',
                              'Rootless execution and model cache/restart behavior not qualified']}
    try:
        endpoint = os.environ.get('DOCKER_HOST')
        if not endpoint:
            endpoint = run(['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'])
        if not endpoint.startswith('unix://'):
            raise RuntimeError('Target probes require a local Unix-socket Docker daemon')
        if os.environ.get('DOCKER_CONTEXT'):
            context_endpoint = run(['docker', 'context', 'inspect', os.environ['DOCKER_CONTEXT'],
                                    '--format', '{{.Endpoints.docker.Host}}'])
            if not context_endpoint.startswith('unix://'):
                raise RuntimeError('Selected Docker context must be local')
        info = json.loads(run(['docker', 'info', '--format', '{{json .}}']))
        report['docker'] = {key: info.get(key) for key in
                            ('ServerVersion', 'KernelVersion', 'OperatingSystem', 'NCPU',
                             'MemTotal', 'CgroupVersion', 'SecurityOptions')}
        report['workspace_disk_free_bytes'] = shutil.disk_usage(Path.cwd()).free
        report['host_gpu'] = run(['nvidia-smi', '--query-gpu=name,driver_version,memory.total,memory.used',
                                  '--format=csv,noheader'])
        probe = container_probe(args.sandbox_image, ['python', '-c', SANDBOX_PROBE])
        probe['observed'] = json.loads(probe.pop('output'))
        probe['checks'] = sandbox_checks(probe['observed'])
        report['sandbox'] = probe
        report['gpu'] = container_probe(args.gpu_image, ['nvidia-smi',
                                        '--query-gpu=name,driver_version,memory.total',
                                        '--format=csv,noheader'], gpu=True)
        report['probes_passed'] = all(probe['checks'].values()) and bool(report['gpu']['output'])
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        report['error'] = str(exc)
        report['probes_passed'] = False
    print(json.dumps(report, indent=2))
    return 0 if report['probes_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
