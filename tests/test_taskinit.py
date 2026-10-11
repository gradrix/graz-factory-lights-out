import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from gflo.taskinit import build

JUNIT = '''<testsuites><testsuite>
<testcase classname="tests.test_app" name="test_ok"/>
<testcase classname="tests.test_app" name="test_needs_db"><error message="no db"/></testcase>
<testcase classname="tests.test_app" name="test_skipped"><skipped/></testcase>
</testsuite></testsuites>'''


class Sandbox:
    def __init__(self, report=JUNIT):
        self.report, self.commands, self.cleaned = report, [], []
    def execute(self, workspace, command, **kwargs):
        self.commands.append((command, kwargs, sorted(path.name for path in Path(workspace).iterdir())))
        if self.report is not None:
            (Path(workspace) / '.gflo-junit.xml').write_text(self.report)
        return {'exit_code': 1, 'output': 'collected 3 items\nERROR: no db'}
    def cleanup(self, workspace):
        self.cleaned.append(workspace)


class TaskInitTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.repo = self.root / 'repo'
        (self.repo / 'tests').mkdir(parents=True)
        (self.repo / 'app.py').write_text('def ok():\n    return 1\n')
        (self.repo / 'tests' / 'test_app.py').write_text('def test_ok():\n    pass\n')
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=T', '-c', 'user.email=t@local', 'commit', '-qm', 'b'], check=True)

    def test_task_uses_the_project_suite_and_tolerates_only_base_failures(self):
        sandbox = Sandbox()
        result = build(self.repo, ' Make ok() return 2. ', self.root / 'task', sandbox,
                       pytest_args="-m 'not db' tests", env=['APP_TEST=1'])
        self.assertEqual(result, {'task': str(self.root / 'task' / 'task.json'), 'tests': 3, 'failing_on_base': 1,
                                  'skipped_on_base': 1, 'base_seconds': 0})
        command, options, files = sandbox.commands[0]
        self.assertEqual(command, ['env', 'APP_TEST=1', 'python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-m', 'not db',
                                   'tests', '--junitxml=/workspace/.gflo-junit.xml'])
        self.assertEqual(files, ['app.py', 'tests'])  # HEAD only, no .git
        self.assertEqual(options['timeout'], 900)  # the acceptance limit, so a suite that fits here fits there
        self.assertEqual(len(sandbox.cleaned), 1)
        task = json.loads((self.root / 'task' / 'task.json').read_text())
        self.assertEqual(task['repo'], str(self.repo.resolve()))
        self.assertEqual(task['profile'], 'python-project')
        self.assertEqual(task['checks'], [['env', 'APP_TEST=1', 'python', '/acceptance/check.py', '-q', '-p', 'no:cacheprovider',
                                           '-m', 'not db', 'tests']])
        self.assertEqual(task['test_command'], task['checks'][0])
        self.assertTrue(task['objective'].startswith('Make ok() return 2.\n\nHow to run tests in this project: env APP_TEST=1 python -m pytest'))
        self.assertIn("-m 'not db' tests", task['objective'])
        self.assertIn('1 tests already fail on the base commit', task['objective'])
        self.assertEqual(json.loads((self.root / 'task' / 'acceptance' / 'baseline_failures.json').read_text()),
                         ['tests.test_app::test_needs_db', 'tests.test_app::test_skipped'])
        self.assertIn('new failures', (self.root / 'task' / 'acceptance' / 'check.py').read_text())

    def test_refusals(self):
        with self.assertRaisesRegex(ValueError, 'Objective is empty'):
            build(self.repo, '  ', self.root / 'a', Sandbox())
        with self.assertRaisesRegex(ValueError, '(?s)produced no report.*ERROR: no db'):
            build(self.repo, 'x', self.root / 'b', Sandbox(report=None))
        failing = '<testsuite><testcase classname="t" name="a"><failure/></testcase></testsuite>'
        with self.assertRaisesRegex(ValueError, 'No test passes'):
            build(self.repo, 'x', self.root / 'c', Sandbox(report=failing))
        self.assertFalse((self.root / 'b').exists() or (self.root / 'c').exists())
        sandbox = Sandbox()
        (self.root / 'exists').mkdir()
        for out, env in ((self.root / 'exists', ()), (self.root / 'e', ['NOEQUALS'])):
            with self.assertRaisesRegex(ValueError, 'already exists|NAME=VALUE'):
                build(self.repo, 'x', out, sandbox, env=env)
        self.assertEqual(sandbox.commands, [])  # refused before the slow base run
        ticks = iter([0, 800])
        with self.assertRaisesRegex(ValueError, 'took 800 s.*allows 900 s'):
            build(self.repo, 'x', self.root / 'slow', Sandbox(), clock=lambda: next(ticks))
        self.assertFalse((self.root / 'slow').exists())
        (self.repo / 'app.py').write_text('dirty\n')
        with self.assertRaisesRegex(ValueError, 'must be clean'):
            build(self.repo, 'x', self.root / 'd', Sandbox())


if __name__ == '__main__':
    unittest.main()
