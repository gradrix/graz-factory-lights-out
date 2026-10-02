"""Disposable Docker guardian: remove exactly its container on owner-pipe EOF.

Runs in a separate session so a killed controller cannot strand a writable job.
The Docker daemon is still trusted; daemon outages are reported as cleanup failure.
"""
import json
import select
import subprocess
import sys
import time


def main():
    spec = json.loads(sys.stdin.buffer.readline())
    process = None
    result = 130
    try:
        # Complete creation before starting any writer. Removing a name while
        # an asynchronous `docker run` is still creating it can strand a late job.
        create = [x for x in spec['args'] if x != '--rm']
        create[1] = 'create'
        created = subprocess.run(create, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, timeout=30)
        if created.returncode:
            sys.stdout.buffer.write(created.stderr)
            return created.returncode
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
