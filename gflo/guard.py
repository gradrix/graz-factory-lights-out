"""Disposable Docker guardian: remove exactly its container on owner-pipe EOF.

Runs in a separate session so a killed controller cannot strand a writable job.
The Docker daemon is still trusted; daemon outages are reported as cleanup failure.
"""
import json
from pathlib import Path
import select
import subprocess
import sys
import time


def run(args, name, timeout, *, output=None, max_output_bytes=16384, cancelled=lambda: False, inspect_path=None):
    """Supervise one guardian; optionally capture a strictly bounded binary stream.

    args/name are constructed by trusted controller code. Text commands retain a
    bounded tail; artifact transport fails if it exceeds its complete-byte cap.
    """
    import threading
    started = time.monotonic()
    process = subprocess.Popen([sys.executable, '-m', 'gflo.guard'], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE if output is not None else subprocess.STDOUT,
                               start_new_session=True)
    tail, count, failures = bytearray(), [0], []
    limited = threading.Event()

    def diagnostics(stream):
        try:
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    break
                tail.extend(chunk)
                if len(tail) > 16384:
                    del tail[:-16384]
        except (OSError, ValueError) as error:
            failures.append(str(error))
            limited.set()

    def drain():
        try:
            while True:
                chunk = process.stdout.read(65536 if output is not None else 4096)
                if not chunk:
                    break
                previous = count[0]
                count[0] += len(chunk)
                if output is not None:
                    remaining = max(0, max_output_bytes - previous)
                    if remaining:
                        output.write(chunk[:remaining])
                    if count[0] > max_output_bytes:
                        limited.set()
                else:
                    tail.extend(chunk)
                    if len(tail) > 16384:
                        del tail[:-16384]
        except (OSError, ValueError) as error:
            failures.append(str(error))
            limited.set()

    readers = [threading.Thread(target=drain, daemon=True)]
    if output is not None:
        readers.append(threading.Thread(target=diagnostics, args=(process.stderr,), daemon=True))
    timed_out = interrupted = False
    try:
        process.stdin.write((json.dumps({'args': args, 'name': name, 'timeout': timeout,
                                        'inspect_path': None if inspect_path is None else str(inspect_path)}) + '\n').encode())
        process.stdin.flush()
        for reader in readers:
            reader.start()
        while process.poll() is None:
            if limited.is_set():
                break
            if cancelled():
                interrupted = True
                break
            if time.monotonic() - started >= timeout:
                timed_out = True
                break
            time.sleep(.05)
    finally:
        process.stdin.close()  # Owner EOF removes the exact container, even on exceptions.
        try:
            process.wait(timeout=45)
        except subprocess.TimeoutExpired:
            cleanup = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
            process.kill(); process.wait(timeout=10)
            if cleanup.returncode and b'No such container' not in cleanup.stderr:
                raise RuntimeError('Container cleanup failed; preparation cannot be reused')
            raise RuntimeError('Container guardian did not stop')
        finally:
            for reader in readers:
                if reader.ident is not None:
                    reader.join(timeout=10)
            process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
    if failures:
        raise RuntimeError('Container output transport failed: ' + '; '.join(failures))
    text = tail.decode(errors='replace')
    if output is None and count[0] > 16384:
        text = f'[truncated {count[0] - 16384} bytes]\n' + text
    code = process.returncode
    if limited.is_set():
        code, text = 125, 'Environment output limit exceeded\n' + text
    elif timed_out:
        code = 124
    elif interrupted:
        code = 130
    return {'exit_code': code, 'timed_out': code == 124, 'limited': limited.is_set(),
            'output': text, 'stdout_bytes': count[0], 'elapsed_s': time.monotonic() - started}


def main():
    spec = json.loads(sys.stdin.buffer.readline())
    process = None
    result = 130
    try:
        # Complete creation before starting any writer. Removing a name while
        # an asynchronous `docker run` is still creating it can strand a late job.
        if spec['args'][:3] != ['docker', 'run', '--rm']:
            raise ValueError('Unexpected guardian command prefix')
        create = ['docker', 'create', *spec['args'][3:]]
        created = subprocess.run(create, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, timeout=30)
        if created.returncode:
            sys.stdout.buffer.write(created.stderr)
            return created.returncode
        if spec.get('inspect_path'):
            inspected = subprocess.run(['docker', 'inspect', spec['name']], capture_output=True,
                                       text=True, timeout=15, check=True)
            value = json.loads(inspected.stdout)[0]
            config = value['HostConfig']
            receipt = {'image': value['Image'], 'name': spec['name'],
                       'host': {key: config.get(key) for key in (
                           'Runtime', 'NetworkMode', 'ReadonlyRootfs', 'CapDrop', 'SecurityOpt',
                           'Memory', 'MemorySwap', 'NanoCpus', 'PidsLimit', 'ShmSize', 'Tmpfs',
                           'Devices', 'DeviceRequests')},
                       'config': {key: value['Config'].get(key) for key in ('User', 'Env', 'WorkingDir')},
                       'mounts': [{key: mount.get(key) for key in ('Type', 'Source', 'Destination', 'RW')}
                                  for mount in value['Mounts']]}
            with Path(spec['inspect_path']).open('x') as destination:
                json.dump(receipt, destination)
        if select.select([sys.stdin.buffer], [], [], 0)[0] and not sys.stdin.buffer.read(1):
            return 130
        process = subprocess.Popen(['docker', 'start', '-a', spec['name']], stdin=subprocess.DEVNULL)
        deadline = time.monotonic() + spec['timeout']
        while process.poll() is None:
            if time.monotonic() >= deadline:
                result = 124
                break
            if select.select([sys.stdin.buffer], [], [], .1)[0]:
                if not sys.stdin.buffer.read(1):
                    break
        else:
            result = process.returncode
    finally:
        try:
            cleanup = subprocess.run(['docker', 'rm', '-f', spec['name']],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=30)
            if cleanup.returncode and b'No such container' not in cleanup.stderr:
                print('Container cleanup failed; resume requires successful cleanup', file=sys.stderr)
                result = 125
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
    return result


if __name__ == '__main__':
    raise SystemExit(main())
