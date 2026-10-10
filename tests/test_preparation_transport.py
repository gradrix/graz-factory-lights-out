import io
import os
import unittest

from docker_support import requires_docker
import tempfile
import json
from pathlib import Path
import uuid

from gflo.guard import run
from gflo.sandbox import DEFAULT_IMAGE


class PreparationTransportTests(unittest.TestCase):
    def command(self, code):
        name = 'gflo-prep-test-' + uuid.uuid4().hex[:12]
        args = ['docker', 'run', '--rm', '--pull', 'never', '--name', name,
                '--runtime', 'runc', '--network', 'none', '--read-only',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--memory', '128m', '--memory-swap', '128m', '--cpus', '1',
                '--pids-limit', '16', '--shm-size', '16m', '--user', f'{os.getuid()}:{os.getgid()}',
                DEFAULT_IMAGE, 'python', '-c', code]
        return name, args

    @requires_docker
    def test_binary_output_is_separate_from_bounded_diagnostics(self):
        name, args = self.command('import sys;sys.stdout.buffer.write(bytes(range(256)));print("diagnostic",file=sys.stderr)')
        output = io.BytesIO()
        with tempfile.TemporaryDirectory() as directory:
            inspect = Path(directory) / 'executor.json'
            result = run(args, name, 15, output=output, max_output_bytes=256, inspect_path=inspect)
            receipt = json.loads(inspect.read_text())
            self.assertEqual(receipt['host']['Runtime'], 'runc')
            self.assertEqual(receipt['host']['NetworkMode'], 'none')
            self.assertTrue(receipt['host']['ReadonlyRootfs'])
            self.assertEqual(receipt['host']['Memory'], 128 * 1024 * 1024)
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(output.getvalue(), bytes(range(256)))
        self.assertIn('diagnostic', result['output'])

    @requires_docker
    def test_transport_overflow_cannot_be_reported_as_success(self):
        name, args = self.command('import sys;sys.stdout.buffer.write(b"x"*65536)')
        output = io.BytesIO()
        result = run(args, name, 15, output=output, max_output_bytes=1024)
        self.assertNotEqual(result['exit_code'], 0)
        self.assertTrue(result['limited'])
        self.assertLessEqual(len(output.getvalue()), 1024)
        self.assertIn('output limit', result['output'])
