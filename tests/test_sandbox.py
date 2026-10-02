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
