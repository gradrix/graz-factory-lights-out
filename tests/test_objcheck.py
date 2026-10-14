import json
from pathlib import Path
import tempfile
import unittest

from ops.delivery.objcheck import build, pytest_prefix
from ops.delivery.objective_check import count_tests, files, layout_problems

COMMAND = ['env', 'A=1', 'python', '/acceptance/check.py', '-q', '-p', 'no:cacheprovider', '-m', 'not db and not llm', 'tests']


class ObjectiveCheckTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.repo = self.root / 'repo'
        (self.repo / 'pkg').mkdir(parents=True)
        (self.repo / 'pkg' / 'core.py').write_text('X = 1\n')
        (self.repo / 'tests').mkdir()
        (self.repo / 'tests' / 'test_core.py').write_text('def test_x():\n    pass\n')

    def test_only_new_check_modules_may_be_added_and_base_files_stay_unchanged(self):
        base = files(self.repo)
        checks = self.repo / 'tests' / 'objective_checks'
        checks.mkdir()
        (checks / 'test_new.py').write_text('def test_a():\n    assert 0\nclass T:\n    def test_b(self):\n        assert 0\n')
        (checks / '__init__.py').write_text('')
        (checks / '__pycache__').mkdir()
        (checks / '__pycache__' / 'x.pyc').write_bytes(b'')
        problems, added = layout_problems(self.repo, base)
        self.assertEqual(problems, [])
        self.assertEqual(added, ['tests/objective_checks/__init__.py', 'tests/objective_checks/test_new.py'])
        self.assertEqual(count_tests(self.repo, added), 2)
        (self.repo / 'pkg' / 'core.py').write_text('X = 2\n')
        (checks / 'conftest.py').write_text('')
        (self.repo / 'pkg' / 'extra.py').write_text('')
        problems, _ = layout_problems(self.repo, base)
        self.assertEqual(problems, ['base file changed or removed: pkg/core.py',
                                    'new file outside tests/objective_checks/test_*.py: pkg/extra.py',
                                    'new file outside tests/objective_checks/test_*.py: tests/objective_checks/conftest.py'])

    def test_generator_task_keeps_the_environment_and_test_options_but_not_the_run_footer(self):
        self.assertEqual(pytest_prefix(COMMAND), (['env', 'A=1'], ['-q', '-p', 'no:cacheprovider', '-m', 'not db and not llm']))
        self.assertEqual(pytest_prefix(['python', '-m', 'pytest', '-q', 'tests']), ([], ['-q']))
        source = self.root / 'tasks' / 'c1'
        (source).mkdir(parents=True)
        import shutil
        shutil.copytree(self.repo, source / 'repo')
        (source / 'environment.txt').write_text('env-id\n')
        (source / 'task.json').write_text(json.dumps({'objective': 'Add pkg.core.double(x).\n\nHow to run tests in this project: ...',
                                                      'test_command': COMMAND, 'profile': 'python-project'}))
        self.assertEqual(build(self.root / 'tasks', self.root / 'out', ['c1']), ['c1'])
        task = json.loads((self.root / 'out' / 'c1' / 'task.json').read_text())
        self.assertTrue(task['objective'].endswith('Add pkg.core.double(x).'))
        self.assertIn("env A=1 python -m pytest -q -p no:cacheprovider -m 'not db and not llm' tests/objective_checks", task['objective'])
        self.assertEqual(task['checks'], [['env', 'A=1', 'python', '/acceptance/check.py', '-q', '-p', 'no:cacheprovider', '-m', 'not db and not llm']])
        base = json.loads((self.root / 'out' / 'c1' / 'acceptance' / 'base_files.json').read_text())
        self.assertIn('pkg/core.py', base)
        self.assertTrue((self.root / 'out' / 'c1' / 'acceptance' / 'check.py').exists())


if __name__ == '__main__':
    unittest.main()
