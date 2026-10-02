import tempfile
from pathlib import Path
import unittest

from gflo.sandbox import Sandbox, DEFAULT_IMAGE


class SandboxTests(unittest.TestCase):
    def test_real_offline_sandbox_and_readonly_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / 'workspace'
            workspace.mkdir()
            acceptance = Path(directory) / 'acceptance'
            acceptance.mkdir()
            sandbox = Sandbox(DEFAULT_IMAGE)
            result = sandbox.execute(workspace, ['python', '-c', "from pathlib import Path; Path('result.txt').write_text('ok'); print(Path('/proc/net/route').read_text())"])
            self.assertEqual(result['exit_code'], 0, result)
            self.assertEqual((workspace / 'result.txt').read_text(), 'ok')
            self.assertNotIn('eth0', result['output'])
            result = sandbox.execute(workspace, ['sh', '-c', 'echo changed > result.txt'], acceptance=acceptance)
            self.assertNotEqual(result['exit_code'], 0)
            self.assertEqual((workspace / 'result.txt').read_text(), 'ok')
            result = sandbox.execute(workspace, ['sh', '-c', 'sleep 20'], timeout=1)
            self.assertTrue(result['timed_out'])

    def test_killed_owner_does_not_leave_container_writer(self):
        import subprocess
        import sys
        import time
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            code = '''import sys
from gflo.sandbox import Sandbox
Sandbox().execute(sys.argv[1], ['sh','-c','while true; do echo x >> ticks; sleep .1; done'])
'''
            owner = subprocess.Popen([sys.executable, '-c', code, directory], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                for _ in range(100):
                    if (workspace / 'ticks').exists(): break
                    time.sleep(.1)
                self.assertTrue((workspace / 'ticks').exists())
                owner.kill(); owner.wait()
                time.sleep(2)
                before = (workspace / 'ticks').stat().st_size
                time.sleep(.4)
                self.assertEqual((workspace / 'ticks').stat().st_size, before, 'orphan writer continued after owner death')
            finally:
                if owner.poll() is None: owner.kill(); owner.wait()
                Sandbox().cleanup(workspace)

    def test_closed_owner_pipe_never_starts_a_new_writer(self):
        import json
        import subprocess
        import sys
        import uuid
        with tempfile.TemporaryDirectory() as directory:
            name = 'gflo-job-' + uuid.uuid4().hex[:16]
            args = ['docker', 'run', '--rm', '--pull', 'never', '--name', name,
                    '--network', 'none', '--mount', f'type=bind,src={directory},dst=/workspace',
                    DEFAULT_IMAGE, 'sh', '-c', 'echo unsafe > /workspace/started']
            spec = json.dumps({'args': args, 'name': name, 'timeout': 10}) + '\n'
            result = subprocess.run([sys.executable, '-m', 'gflo.guard'], input=spec, text=True, capture_output=True, timeout=45)
            self.assertEqual(result.returncode, 130, result)
            self.assertFalse((Path(directory) / 'started').exists())
            self.assertNotEqual(subprocess.run(['docker', 'inspect', name], capture_output=True).returncode, 0)
