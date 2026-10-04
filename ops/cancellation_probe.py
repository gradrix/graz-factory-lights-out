#!/usr/bin/env python3
"""Disposable one-request lifecycle experiment; never installed with GFLO."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from planning_pilot_prototype import pilot_lease, strict_probe

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gflo.worker import ModelWorker

BODY = {
    'model': 'flash-next-coder', 'temperature': 0, 'max_tokens': 4096,
    'reasoning_effort': 'medium', 'thinking_budget_tokens': 1024,
    'chat_template_kwargs': {'enable_thinking': True},
    'messages': [
        {'role': 'system', 'content': 'Follow the counting instruction. Do not use tools.'},
        {'role': 'user', 'content': 'Print consecutive integers from 1 through 2000, one integer per line, without explanation.'},
    ],
}
WORK_SECONDS, CLEANUP_SECONDS = 60, 150


def save(path, value):
    raw = json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode()
    if len(raw) > 1024 * 1024:
        raise ValueError('Evidence capacity')
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def group_absent(pid):
    try:
        os.killpg(pid, 0)
        return False
    except ProcessLookupError:
        return True


def stop_client(client, deadline):
    """Reap the direct child and verify its entire owned group is absent."""
    actions = []
    for sig, allowance in ((signal.SIGTERM, 2), (signal.SIGKILL, 3)):
        client.poll()
        if group_absent(client.pid):
            break
        if time.monotonic() >= deadline:
            break
        try:
            os.killpg(client.pid, sig)
            actions.append(sig.name)
        except ProcessLookupError:
            pass
        until = min(deadline, time.monotonic() + allowance)
        while time.monotonic() < until:
            client.poll()
            if group_absent(client.pid):
                break
            time.sleep(min(.05, max(0, until - time.monotonic())))
    client.poll()
    return {'actions': actions, 'returncode': client.returncode,
            'group_absent': group_absent(client.pid)}


def request_child(config_path, output):
    # Credentials remain inside ModelWorker transport; never serialize config.
    config = json.loads(Path(config_path).read_bytes())
    if config['model'] != BODY['model']:
        raise ValueError('Model alias drift')
    client = ModelWorker(config, None)
    save(output / 'client-started.json', {'pid': os.getpid(), 'monotonic': time.monotonic()})
    try:
        result = client.request('/v1/chat/completions', BODY, timeout=WORK_SECONDS,
                                max_response_bytes=1024 * 1024)
        save(output / 'response.json', result)
        save(output / 'client-complete.json', {'monotonic': time.monotonic(), 'kind': 'response'})
        return 0
    except Exception as error:
        save(output / 'client-complete.json', {'monotonic': time.monotonic(),
             'kind': 'error', 'error_type': type(error).__name__})
        return 2


def validate_admission(path, identity_path=None, config_path=None, lease_path=None):
    receipt = json.loads(Path(path).read_bytes())
    if receipt.get('approved') is not True or receipt.get('experiment') != 'single-request-cancellation':
        raise ValueError('Missing frozen admission')
    files = receipt.get('prototype_files')
    if not isinstance(files, dict) or 'ops/cancellation_probe.py' not in files or 'ops/planning_pilot_prototype.py' not in files:
        raise ValueError('Incomplete candidate binding')
    for name, expected in files.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid admission path')
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
            raise ValueError('Candidate changed after admission')
    if receipt.get('request_sha256') != hashlib.sha256(json.dumps(BODY, sort_keys=True).encode()).hexdigest():
        raise ValueError('Request changed after admission')
    evidence = receipt.get('evidence')
    if not isinstance(evidence, dict) or set(evidence) != {'contract', 'controlled_tests', 'security_review'}:
        raise ValueError('Missing admission evidence')
    for kind, binding in evidence.items():
        if not isinstance(binding, dict) or set(binding) != {'path', 'sha256'}:
            raise ValueError('Invalid evidence binding')
        if hashlib.sha256(Path(binding['path']).read_bytes()).hexdigest() != binding['sha256']:
            raise ValueError('Admission evidence changed')
    if evidence['contract']['sha256'] != '992ed9637b164e68cf3093cca817938ccd7ec31593813b789e69927964c8d7c9':
        raise ValueError('Cancellation contract changed')
    if identity_path is None or hashlib.sha256(Path(identity_path).read_bytes()).hexdigest() != receipt.get('identity_sha256'):
        raise ValueError('Serving identity binding changed')
    config = json.loads(Path(config_path).read_bytes()) if config_path is not None else {}
    public = {key: config.get(key) for key in ('endpoint', 'model', 'reasoning')}
    if public != receipt.get('public_config') or public != {
            'endpoint': 'http://127.0.0.1:18000', 'model': 'flash-next-coder', 'reasoning': 'medium'}:
        raise ValueError('Inference profile changed')
    if lease_path is None or str(Path(lease_path).expanduser().absolute()) != receipt.get('lease_path'):
        raise ValueError('Pilot lease binding changed')
    return receipt


def experiment(args):
    admission = validate_admission(args.admission, args.identity, args.config, args.lease)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    save(output / 'admission.json', admission)
    save(output / 'request.json', BODY)
    events = []
    started = time.monotonic()
    client = None
    cancelled = False
    stop_at = None
    observed_busy = False
    outcome = 'inconclusive'
    result = {'charged_requests': 0, 'outcome': outcome}

    def event(kind, **facts):
        events.append({'elapsed_s': time.monotonic() - started, 'kind': kind, **facts})
        save(output / 'events.json', events)

    def cancel(signum, frame):
        nonlocal cancelled, stop_at
        cancelled = True
        if stop_at is None:
            stop_at = time.monotonic()

    previous = {sig: signal.signal(sig, cancel) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        work_deadline = started + WORK_SECONDS
        for _ in range(2):
            observation = strict_probe(args.config, args.identity, work_deadline)
            event('preflight', observation=observation)
            if observation.get('state') != 'idle' or cancelled:
                result['outcome'] = 'admission_refused'
                return result
            time.sleep(min(1, max(0, work_deadline - time.monotonic())))
        if time.monotonic() >= work_deadline or cancelled:
            result['outcome'] = 'admission_refused'
            return result
        # Durable debit is made before a client exists; no replay/reset path.
        consumed = Path(args.lease).expanduser().parent / 'consumed-cancellation-probes'
        consumed.mkdir(mode=0o700, exist_ok=True)
        marker = consumed / hashlib.sha256(Path(args.admission).read_bytes()).hexdigest()
        with marker.open('xb') as stream:
            stream.write(b'Admission consumed; interrupted or failed calls cannot retry.\n')
            stream.flush()
            os.fsync(stream.fileno())
        result['charged_requests'] = 1
        save(output / 'debit.json', {'count': 1, 'limit': 1, 'monotonic': time.monotonic()})
        if cancelled or time.monotonic() >= work_deadline:
            result['outcome'] = 'cancelled_before_dispatch'
            return result
        client = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
            '--client', '--config', args.config, '--output', str(output)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True)
        event('client_launched', pid=client.pid)
        while not cancelled and time.monotonic() < work_deadline and client.poll() is None:
            observation = strict_probe(args.config, args.identity, work_deadline)
            event('active_observation', observation=observation)
            if observation.get('state') == 'busy':
                # strict_probe validates health, exact identity and typed slot.
                observed_busy = True
                break
            if observation.get('state') == 'unknown':
                break
            time.sleep(min(.2, max(0, work_deadline - time.monotonic())))
        stop_at = stop_at or time.monotonic()
        cleanup_deadline = stop_at + CLEANUP_SECONDS
        alive_before_stop = client.poll() is None
        completed_before_stop = (output / 'client-complete.json').exists() or (output / 'response.json').exists()
        event('stop_transition', observed_busy=observed_busy, alive=alive_before_stop,
              completed=completed_before_stop, cancelled=cancelled)
        cleanup = stop_client(client, cleanup_deadline)
        event('client_cleanup', **cleanup)
        idle_count = 0
        while cleanup['group_absent'] and time.monotonic() < cleanup_deadline:
            observation = strict_probe(args.config, args.identity, cleanup_deadline)
            event('cleanup_observation', observation=observation)
            idle_count = idle_count + 1 if observation.get('state') == 'idle' else 0
            if idle_count == 2:
                break
            time.sleep(min(1, max(0, cleanup_deadline - time.monotonic())))
        completed = (output / 'client-complete.json').exists() or (output / 'response.json').exists()
        terminated = cleanup['returncode'] in (-signal.SIGTERM, -signal.SIGKILL)
        clean = cleanup['group_absent'] and idle_count == 2 and time.monotonic() <= cleanup_deadline
        passed = (observed_busy and alive_before_stop and not completed_before_stop and
                  not completed and terminated and clean and not cancelled and stop_at < work_deadline)
        result.update(outcome='passed' if passed else ('inconclusive' if clean else 'cleanup_unresolved'),
                      observed_busy=observed_busy, cleanup=cleanup, settled_idle=idle_count == 2,
                      cancelled=cancelled, elapsed_s=time.monotonic() - started,
                      cleanup_s=time.monotonic() - stop_at)
        return result
    except Exception as error:
        result.update(outcome='failed', error_type=type(error).__name__)
        return result
    finally:
        if client is not None and not group_absent(client.pid):
            stop_at = stop_at or time.monotonic()
            emergency = stop_client(client, stop_at + CLEANUP_SECONDS)
            event('exception_cleanup', **emergency)
            result['outcome'] = 'cleanup_unresolved'
        save(output / 'result.json', result)
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--client', action='store_true')
    for name in ('config', 'output'):
        parser.add_argument('--' + name, required=True)
    for name in ('identity', 'lease', 'admission'):
        parser.add_argument('--' + name)
    args = parser.parse_args()
    if args.client:
        return request_child(args.config, Path(args.output))
    if not all((args.identity, args.lease, args.admission)):
        parser.error('Supervisor requires identity, lease and frozen admission')
    with pilot_lease(Path(args.lease)):
        result = experiment(args)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['outcome'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
