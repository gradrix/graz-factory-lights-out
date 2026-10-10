import ast
import hashlib
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
    def project(self, tests=None, source=SOURCE, base_tests=None, extra=None):
        """Config path and candidate workspace; base_tests are test modules already at the base commit."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        workspace = root / 'workspace'
        base_files = {'tests/__init__.py': '', **(base_tests or {})}
        for name, text in {'calc.py': SOURCE, **base_files}.items():
            for place in (workspace, root / 'base_tests') if name != 'calc.py' else (workspace,):
                (place / name).parent.mkdir(parents=True, exist_ok=True)
                (place / name).write_text(text)
        config = {'targets': ['calc.py'], 'threshold': 0.6, 'max_mutants': 30, 'runs': 2, 'budget_seconds': 120,
                  'runner': [sys.executable, '-m', 'unittest', '{tests}'],
                  'base': {'calc.py': acceptance.digest(workspace / 'calc.py')},
                  'base_tests': {name: acceptance.digest(workspace / name) for name in base_files}}
        (root / 'test_task.json').write_text(json.dumps(config))
        (workspace / 'calc.py').write_text(source)
        if tests is not None:
            (workspace / 'tests' / 'test_calc.py').write_text(tests)
        for name, text in (extra or {}).items():
            (workspace / name).parent.mkdir(parents=True, exist_ok=True)
            if text is None:
                (workspace / name).unlink()
            else:
                (workspace / name).write_text(text)
        return str(root / 'test_task.json'), workspace

    def test_strong_new_tests_pass(self):
        self.assertEqual(acceptance.main(*self.project(STRONG)), 0)

    def test_weak_tests_fail_the_mutation_threshold(self):
        self.assertEqual(acceptance.main(*self.project(WEAK)), 1)

    def test_changed_source_or_missing_tests_fail(self):
        self.assertEqual(acceptance.main(*self.project(STRONG, source=SOURCE + '\nX = 1\n')), 1)
        self.assertEqual(acceptance.main(*self.project(None)), 1)

    def test_failing_new_tests_fail(self):
        self.assertEqual(acceptance.main(*self.project(STRONG.replace('clamp(5, 1, 10), 5', 'clamp(5, 1, 10), 6'))), 1)

    def test_tests_on_source_text_are_rejected(self):
        hashing = ('import hashlib, unittest\n\nclass T(unittest.TestCase):\n    def test_source(self):\n'
                   '        text = open("calc.py").read()\n        self.assertEqual(len(text), %d)\n' % len(SOURCE))
        self.assertEqual(acceptance.main(*self.project(hashing)), 1)

    def test_touching_existing_strong_tests_earns_nothing(self):
        config, workspace = self.project(base_tests={'tests/test_calc.py': STRONG})
        (workspace / 'tests' / 'test_calc.py').write_text(STRONG + '\n# touched\n')
        self.assertEqual(acceptance.main(config, workspace), 1)

    def test_existing_strong_tests_leave_nothing_to_earn(self):
        extra = STRONG.replace('class ClampTests', 'class MoreTests').replace('def test_names', 'def test_more_names')
        config, workspace = self.project(base_tests={'tests/test_calc.py': STRONG}, extra={'tests/test_more.py': extra})
        self.assertEqual(acceptance.main(config, workspace), 1)

    def test_files_outside_tests_and_base_tests_are_protected(self):
        self.assertEqual(acceptance.main(*self.project(STRONG, extra={'pytest.ini': '[pytest]\naddopts = -p no:x\n'})), 1)
        self.assertEqual(acceptance.main(*self.project(STRONG, extra={'pkg/test_utils.py': 'X = 1\n'})), 1)
        config, workspace = self.project(STRONG, base_tests={'tests/test_old.py': 'def test_old():\n    assert 1 == 1\n'},
                                         extra={'tests/test_old.py': None})
        self.assertEqual(acceptance.main(config, workspace), 1)

    def test_tests_on_ast_or_bytecode_are_rejected(self):
        probe = ('import ast, hashlib, unittest\n\nclass T(unittest.TestCase):\n    def test_tree(self):\n'
                 '        tree = ast.dump(ast.parse(open("calc.py").read()))\n'
                 '        self.assertEqual(hashlib.sha256(tree.encode()).hexdigest(), %r)\n'
                 % hashlib.sha256(ast.dump(ast.parse(SOURCE)).encode()).hexdigest())
        self.assertEqual(acceptance.main(*self.project(probe)), 1)
        self.assertNotEqual(ast.dump(ast.parse(acceptance.equivalent(SOURCE))), ast.dump(ast.parse(SOURCE)))

    def test_test_support_cannot_silence_existing_tests(self):
        copied = STRONG.replace('class ClampTests', 'class Copied').replace('def test_', 'def test_copied_')
        silencer = 'import os, sys\nif any("test_old" in a for a in sys.argv):\n    os._exit(0)\n'
        config, workspace = self.project(base_tests={'tests/test_old.py': STRONG},
                                         extra={'tests/test_new.py': copied, 'tests/__init__.py': silencer})
        self.assertEqual(acceptance.main(config, workspace), 1)  # changed support file
        config, workspace = self.project(base_tests={'tests/test_old.py': STRONG},
                                         extra={'tests/test_new.py': copied, 'tests/conftest.py': silencer})
        self.assertEqual(acceptance.main(config, workspace), 1)  # new support file
        config, workspace = self.project(base_tests={'tests/test_old.py': STRONG}, extra={'tests/test_new.py': copied})
        self.assertEqual(acceptance.main(config, workspace), 1)  # copied strength earns nothing

    def test_failing_existing_tests_do_not_count_as_kills(self):
        failing = 'import unittest\nimport calc\n\nclass Old(unittest.TestCase):\n    def test_broken(self):\n        self.assertEqual(calc.clamp(1, 0, 2), 2)\n'
        config, workspace = self.project(STRONG, base_tests={'tests/test_old.py': failing})
        self.assertEqual(acceptance.main(config, workspace), 0)

    def test_removing_existing_test_functions_is_rejected(self):
        config, workspace = self.project(base_tests={'tests/test_calc.py': WEAK})
        (workspace / 'tests' / 'test_calc.py').write_text(STRONG)
        self.assertEqual(acceptance.main(config, workspace), 1)

    def test_existing_tests_reaching_the_target_through_a_package_still_count(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        workspace = root / 'workspace'
        strong = STRONG.replace('from calc import clamp, is_valid', 'from pkg import clamp, is_valid')
        base = {'tests/__init__.py': '', 'tests/test_core.py': strong}
        for name, text in {'pkg/__init__.py': 'from .core import *\n', 'pkg/core.py': SOURCE, **base}.items():
            (workspace / name).parent.mkdir(parents=True, exist_ok=True)
            (workspace / name).write_text(text)
        for name, text in base.items():
            (root / 'base_tests' / name).parent.mkdir(parents=True, exist_ok=True)
            (root / 'base_tests' / name).write_text(text)
        config = {'targets': ['pkg/core.py'], 'threshold': 0.6, 'max_mutants': 30, 'runs': 1, 'budget_seconds': 120,
                  'runner': [sys.executable, '-m', 'unittest', '{tests}'],
                  'base': {name: acceptance.digest(workspace / name) for name in ('pkg/__init__.py', 'pkg/core.py')},
                  'base_tests': {name: acceptance.digest(workspace / name) for name in base}}
        (root / 'test_task.json').write_text(json.dumps(config))
        (workspace / 'tests' / 'test_core.py').write_text(
            strong + '\n\nclass Extra(unittest.TestCase):\n    def test_extra(self):\n        self.assertEqual(clamp(2, 1, 3), 2)\n')
        self.assertEqual(acceptance.main(str(root / 'test_task.json'), workspace), 1)
        self.assertEqual(acceptance.module_name('src/pkg/core.py'), 'pkg.core')
        self.assertTrue(acceptance.imports_target('from pkg import clamp\n', {'pkg.core'}))

    def test_only_new_test_functions_are_smell_checked(self):
        smoke = 'import unittest\nfrom calc import clamp\n\nclass Smoke(unittest.TestCase):\n    def test_smoke(self):\n        clamp(1, 0, 2)\n'
        config, workspace = self.project(base_tests={'tests/test_calc.py': smoke})
        (workspace / 'tests' / 'test_calc.py').write_text(smoke + '\n\n' + STRONG.replace('import unittest\n', ''))
        self.assertEqual(acceptance.main(config, workspace), 0)


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
            self.assertIn('at least 60% of the mutants the existing tests miss', task['objective'])
            self.assertEqual(sorted(config['base']), ['calc.py'])
            self.assertEqual(sorted(config['base_tests']), ['tests/test_old.py'])
            self.assertEqual(config['runner'], ['python', '-m', 'unittest', '{tests}'])
            self.assertTrue((Path(directory) / 'out' / 'acceptance' / 'base_tests' / 'tests' / 'test_old.py').is_file())
            with self.assertRaisesRegex(ValueError, 'max_mutants'):
                build(repo, ['calc.py'], Path(directory) / 'out3', max_mutants=0)
            with self.assertRaisesRegex(ValueError, 'outside tests'):
                build(repo, ['tests/test_old.py'], Path(directory) / 'out2')


if __name__ == '__main__':
    unittest.main()
