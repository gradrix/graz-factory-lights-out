import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gflo.testfactory import RECIPE, build

spec = importlib.util.spec_from_file_location('test_acceptance', RECIPE)
acceptance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acceptance)

SOURCE = '''def clamp(value, low, high):
    if low > high:
        raise ValueError("low above high")
    if value < low:
        return low
    if value > high:
        return high
    return value


def is_valid(name):
    return bool(name) and not name.startswith("_")
'''

STRONG = '''import unittest
from calc import clamp, is_valid


class ClampTests(unittest.TestCase):
    def test_inside_and_bounds(self):
        self.assertEqual(clamp(5, 1, 10), 5)
        self.assertEqual(clamp(1, 1, 10), 1)
        self.assertEqual(clamp(10, 1, 10), 10)

    def test_outside(self):
        self.assertEqual(clamp(-3, 1, 10), 1)
        self.assertEqual(clamp(30, 1, 10), 10)

    def test_invalid_bounds(self):
        with self.assertRaises(ValueError):
            clamp(1, 5, 2)
        self.assertEqual(clamp(4, 4, 4), 4)

    def test_names(self):
        self.assertTrue(is_valid("name"))
        self.assertFalse(is_valid("_private"))
        self.assertFalse(is_valid(""))
'''

WEAK = '''import unittest
from calc import clamp


class ClampTests(unittest.TestCase):
    def test_runs(self):
        self.assertIsNotNone(clamp(5, 1, 10))
'''


class MutationTests(unittest.TestCase):
    def test_every_site_yields_a_distinct_valid_mutant(self):
        produced = list(acceptance.mutants(SOURCE, 100))
        kinds = {site[0] for site, _ in produced}
        self.assertEqual(kinds, {'compare', 'operator', 'drop_not', 'return_none'})
        for _, source in produced:
            self.assertNotEqual(source, ast.unparse(ast.parse(SOURCE)))
            ast.parse(source)
        self.assertEqual(len(list(acceptance.mutants(SOURCE, 3))), 3)
        self.assertEqual([site for site, _ in acceptance.mutants(SOURCE, 3)],
                         [site for site, _ in acceptance.mutants(SOURCE, 3)])  # deterministic

    def test_constants_change_and_negation_drops(self):
        sources = [source for site, source in acceptance.mutants('def f(x):\n    return not x or 2\n', 20)]
        self.assertIn('def f(x):\n    return x or 2', sources)
        self.assertIn('def f(x):\n    return not x or 3', sources)

    def test_smells_reject_tests_without_real_assertions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test_x.py'
            path.write_text('import pytest\n\ndef test_none():\n    f()\n\ndef test_true():\n    assert True\n\n'
                            'def test_ok():\n    assert f() == 1\n\ndef test_raises():\n    with pytest.raises(ValueError):\n        f()\n\n'
                            'class T:\n    def test_method(self):\n        self.assertEqual(f(), 1)\n')
            self.assertEqual(acceptance.smells(path), [f'{path}::test_none has no meaningful assertion',
                                                       f'{path}::test_true has no meaningful assertion'])


class AcceptanceTests(unittest.TestCase):
    def project(self, tests=None, source=SOURCE):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        workspace = root / 'workspace'
        (workspace / 'tests').mkdir(parents=True)
        (workspace / 'calc.py').write_text(SOURCE)
        (workspace / 'tests' / '__init__.py').write_text('')
        config = {'targets': ['calc.py'], 'threshold': 0.6, 'max_mutants': 30, 'runs': 2,
                  'runner': [sys.executable, '-m', 'unittest', '{tests}'],
                  'base': {'calc.py': acceptance.digest(workspace / 'calc.py')},
                  'base_tests': {'tests/__init__.py': acceptance.digest(workspace / 'tests' / '__init__.py')}}
        (root / 'config.json').write_text(json.dumps(config))
        (workspace / 'calc.py').write_text(source)
        if tests is not None:
            (workspace / 'tests' / 'test_calc.py').write_text(tests)
        return str(root / 'config.json'), workspace

    def test_strong_new_tests_pass(self):
        self.assertEqual(acceptance.main(*self.project(STRONG)), 0)

    def test_weak_tests_fail_the_mutation_threshold(self):
        self.assertEqual(acceptance.main(*self.project(WEAK)), 1)

    def test_changed_source_or_missing_tests_fail(self):
        self.assertEqual(acceptance.main(*self.project(STRONG, source=SOURCE + '\nX = 1\n')), 1)
        self.assertEqual(acceptance.main(*self.project(None)), 1)

    def test_failing_new_tests_fail(self):
        self.assertEqual(acceptance.main(*self.project(STRONG.replace('clamp(5, 1, 10), 5', 'clamp(5, 1, 10), 6'))), 1)


class BuildTests(unittest.TestCase):
    def test_build_writes_task_and_refuses_bad_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / 'repo'
            (repo / 'tests').mkdir(parents=True)
            (repo / 'calc.py').write_text(SOURCE)
            (repo / 'tests' / 'test_old.py').write_text('def test_old():\n    assert 1 == 1\n')
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(repo), '-c', 'user.name=T', '-c', 'user.email=t@local', 'commit', '-qm', 'b'], check=True)
            task = json.loads(build(repo, ['calc.py'], Path(directory) / 'out', profile='python-stdlib').read_text())
            config = json.loads((Path(directory) / 'out' / 'acceptance' / 'test_task.json').read_text())
            self.assertEqual(task['checks'], [['python', '/acceptance/test_acceptance.py']])
            self.assertIn('60% of those mutants', task['objective'])
            self.assertEqual(sorted(config['base']), ['calc.py'])
            self.assertEqual(sorted(config['base_tests']), ['tests/test_old.py'])
            self.assertEqual(config['runner'], ['python', '-m', 'unittest', '{tests}'])
            with self.assertRaisesRegex(ValueError, 'tracked non-test'):
                build(repo, ['tests/test_old.py'], Path(directory) / 'out2')


if __name__ == '__main__':
    unittest.main()
