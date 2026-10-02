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
        process = subprocess.Popen(spec['args'], stdin=subprocess.DEVNULL)
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
