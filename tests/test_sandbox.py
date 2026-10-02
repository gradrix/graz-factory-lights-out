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
