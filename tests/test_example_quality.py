from pathlib import Path
import shutil
import tempfile
import unittest
from gflo.sandbox import Sandbox


class ExampleQualityTests(unittest.TestCase):
    def test_zero_tests_and_scratch_files_fail_against_passing_control(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / 'workspace'
            (workspace / 'tests').mkdir(parents=True)
            acceptance = root / 'acceptance'
            acceptance.mkdir()
            shutil.copy2(Path(__file__).resolve().parents[1] / 'examples/check_project.py', acceptance / 'quality.py')
            (workspace / 'README.md').write_text('Usage: python app.py\n' + 'A small documented test fixture. ' * 4)
            test = workspace / 'tests/test_app.py'
            code = 'import unittest\nclass Tests(unittest.TestCase):\n' + ''.join(f'    def test_{n}(self): self.assertEqual({n}, {n})\n' for n in range(3))
            test.write_text(code)
            sandbox = Sandbox()
            def check():
                return sandbox.execute(workspace, ['python', '-I', '/acceptance/quality.py'], acceptance=acceptance)
            self.assertEqual(check()['exit_code'], 0)
            test.write_text(code.replace('def test_', 'def case_'))
            result = check()
            self.assertNotEqual(result['exit_code'], 0)
            self.assertIn('found 0', result['output'])
            test.write_text(code)
            (workspace / 'scratch.csv').write_text('temporary')
            result = check()
            self.assertNotEqual(result['exit_code'], 0)
            self.assertIn('scratch.csv', result['output'])
