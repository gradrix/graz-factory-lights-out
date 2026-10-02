#!/usr/bin/env python3
"""Manage the pinned, local Flash Coder service on MONSTER-GAMING-PC."""
import argparse
import json
from pathlib import Path
import subprocess
import secrets
import time
import urllib.request

NAME = 'gflo-model'
IMAGE = 'sha256:249ed60fdd67b96db472e16f945af5aaba565b20159d192ba378035b6d136a1c'
ROOT = Path.home() / 'benchmark-5090/flash'
STATE = Path.home() / '.local/state/gflo-model'


def docker(*args, check=True):
    return subprocess.run(['docker', *args], check=check, capture_output=True, text=True)


def inspect(name):
    result = docker('inspect', name, check=False)
    return json.loads(result.stdout)[0] if result.returncode == 0 else None


def get(path):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    headers = {'Authorization': 'Bearer ' + (STATE / 'api-key').read_text().strip()}
    request = urllib.request.Request('http://127.0.0.1:18000' + path, headers=headers)
    with opener.open(request, timeout=5) as response:
        return json.load(response)


def remove_owned():
    current = inspect(NAME)
    if current:
        if current['Config'].get('Labels', {}).get('gflo.owner') != 'model-service':
            raise RuntimeError('Container name belongs to another owner')
        docker('rm', '-f', NAME)


def restore():
    saved = json.loads((STATE / 'rollback.json').read_text())
    original = inspect('local-vllm')
    if not original or original['Id'] != saved['container_id']:
        raise RuntimeError('Original container identity changed; inspect before rollback')
    remove_owned()
    policy = saved['restart']
    restart = policy['Name']
    if restart == 'on-failure' and policy.get('MaximumRetryCount'):
        restart += ':' + str(policy['MaximumRetryCount'])
    docker('update', '--restart', restart, 'local-vllm')
    docker('start', 'local-vllm')
    print('Original vLLM container started; allow its model to load.')


def up(context):
    required = [ROOT / 'runtime/llama-b11284/llama-server',
                ROOT / 'Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf',
                ROOT / 'Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00002-of-00002.gguf']
    if not all(p.is_file() for p in required):
        raise RuntimeError('Pinned runtime/weights missing; install study artifacts first')
    docker('image', 'inspect', IMAGE)
    original = inspect('local-vllm')
    if not original:
        raise RuntimeError('Original rollback container is missing')
    STATE.mkdir(parents=True, exist_ok=True)
    rollback = STATE / 'rollback.json'
    if not rollback.exists():
        rollback.write_text(json.dumps({'container_id': original['Id'],
                                       'restart': original['HostConfig']['RestartPolicy']}, indent=2))
    if json.loads(rollback.read_text())['container_id'] != original['Id']:
        raise RuntimeError('Rollback identity mismatch')
    key = STATE / 'api-key'
    if not key.exists():
        key.touch(mode=0o600)
        key.write_text(secrets.token_urlsafe(32) + '\n')
    key.chmod(0o600)
    remove_owned()
    docker('update', '--restart', 'no', 'local-vllm')
    docker('stop', '-t', '40', 'local-vllm')
    cache = 'q4_0'  # Experiment: context allocation changes alone.
    args = ['run', '-d', '--pull', 'never', '--name', NAME,
            '--label', 'gflo.owner=model-service', '--restart', 'unless-stopped',
            '--network', 'bridge', '--gpus', 'all', '--shm-size', '8g',
            '-p', '127.0.0.1:18000:8000', '-v', str(ROOT) + ':/model:ro', '-v', str(key) + ':/run/model-key:ro',
            '--entrypoint', '/model/runtime/llama-b11284/llama-server', IMAGE,
            '--model', '/model/' + required[1].name, '--alias', 'flash-next-coder',
            '--host', '0.0.0.0', '--port', '8000', '-ngl', '99', '-fa', 'on',
            '-c', str(context), '-np', '1', '--cache-type-k', cache, '--cache-type-v', cache,
            '--offline', '--api-key-file', '/run/model-key', '--reasoning', 'auto', '--jinja', '--fit', 'off', '-b', '512', '-ub', '512',
            '-lm', 'mmap', '--lazy-mode', 'on']
    try:
        docker(*args)
        for _ in range(240):
            current = inspect(NAME)
            if not current or not current['State']['Running']:
                raise RuntimeError('Model exited: inspect docker logs gflo-model')
            try:
                get('/health')
                props = get('/props')
                actual = props['default_generation_settings']['n_ctx']
                if actual != context:
                    raise RuntimeError(f'Context mismatch: {actual}')
                result = {'context': actual, 'cache': cache, 'image': IMAGE,
                          'container_id': current['Id'], 'endpoint': 'http://127.0.0.1:18000',
                          'model': get('/v1/models')['data'][0]['id'], 'command': args}
                (STATE / 'profile.json').write_text(json.dumps(result, indent=2))
                print(json.dumps(result, indent=2))
                return
            except (OSError, KeyError):
                time.sleep(2)
        raise RuntimeError('Model readiness timed out')
    except BaseException:
        restore()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['up', 'status', 'rollback'])
    parser.add_argument('--context', type=int, choices=[65536, 98304, 131072], default=131072)
    args = parser.parse_args()
    if args.action == 'up':
        up(args.context)
    elif args.action == 'rollback':
        restore()
    else:
        current = inspect(NAME)
        print(json.dumps({'running': bool(current and current['State']['Running']),
                          'models': get('/v1/models') if current and current['State']['Running'] else None}, indent=2))


if __name__ == '__main__':
    main()
