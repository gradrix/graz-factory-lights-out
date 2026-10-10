import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from gflo.worker import MAP_TOOL, SYSTEM, TOOLS, ModelWorker, navigation_aids

spec = importlib.util.spec_from_file_location('repo_map', Path(__file__).resolve().parents[1] / 'gflo/recipes/repo_map.py')
repo_map = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repo_map)

CONFIG = {'endpoint': 'http://127.0.0.1:18000', 'model': 'test'}


class Sandbox:
    def __init__(self):
        self.commands = []
    def cleanup(self, workspace):
        pass
    def execute(self, workspace, command, **kwargs):
        self.commands.append((command, kwargs))
        return {'exit_code': 0, 'output': 'map output'}
    def verify(self, *args):
        return {'passed': False}


def call(name, arguments, number='1'):
    return {'role': 'assistant', 'content': None, 'tool_calls': [{'id': number, 'type': 'function', 'function': {'name': name, 'arguments': arguments}}]}


class RepoMapTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        files = {
            'pkg/__init__.py': '',
            'pkg/core.py': '"""Core maths."""\nLIMIT = 3\n\nclass Clamp(Base):\n    def run(self, value: int) -> int:\n        return value\n\ndef clamp(value, low=0):\n    """Clamp a value."""\n    return max(low, value)\n',
            'pkg/api.py': 'from .core import clamp\n\ndef handler(x):\n    return clamp(x)\n',
            'tools/cli.py': 'import pkg.core\nprint(pkg.core.clamp(1))\n',
            'broken.py': 'def (:\n',
            'tests/test_core.py': 'from pkg.core import clamp\n',
            '.hidden/secret.py': 'def clamp(): pass\n',
        }
        for name, text in files.items():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text(text)

    def output(self, *query):
        lines = []
        repo_map.print = lines.append
        try:
            repo_map.main(['repo_map.py', str(self.root), *query])
        finally:
            del repo_map.print
        return lines[0]

    def test_overview_lists_modules_definitions_and_tests_compactly(self):
        text = self.output()
        self.assertIn('pkg/core.py — Core maths.: Clamp, clamp', text)
        self.assertIn('tools/: 1 modules (not a package): cli.py', text)
        self.assertIn('broken.py: (does not parse)', text)
        self.assertIn('tests/: 1 test modules', text)
        self.assertNotIn('secret', text)

    def test_module_query_shows_signatures_and_importers_including_relative_imports(self):
        text = self.output('/workspace/pkg/core.py')
        self.assertIn('4: class Clamp(Base)', text)
        self.assertIn('5: def run(self, value: int) -> int', text)
        self.assertIn('8: def clamp(value, low=0)  # Clamp a value.', text)
        self.assertIn('2: LIMIT = ...', text)
        self.assertIn('imported by: pkg/api.py, tests/test_core.py, tools/cli.py', text)

    def test_name_query_shows_definitions_and_usages(self):
        text = self.output('clamp')
        self.assertIn('pkg/core.py:8: def clamp(value, low=0)', text)
        self.assertIn('pkg/api.py:4: return clamp(x)', text)
        self.assertIn('tools/cli.py:2: print(pkg.core.clamp(1))', text)
        self.assertNotIn('.hidden', text)
        self.assertIn('No definition or usage', self.output('missing_name'))

    def test_output_is_bounded(self):
        for index in range(200):
            (self.root / f'module_with_a_long_descriptive_name_{index}.py').write_text('"""Doc."""\n' + '\n'.join(f'def function_{n}(): pass' for n in range(20)))
        text = self.output()  # names and docstrings are dropped first, so every module is still listed
        self.assertIn('module_with_a_long_descriptive_name_199.py', text)
        self.assertNotIn('Doc.', text)
        self.assertLessEqual(len(text), repo_map.LIMIT)
        for index in range(200, 1200):
            (self.root / f'module_with_a_long_descriptive_name_{index}.py').write_text('x = 1\n')
        text = self.output()
        self.assertLessEqual(len(text), repo_map.LIMIT + 100)
        self.assertTrue(text.endswith('query a narrower module path or name.'))


class NavigationWorkerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.workspace = Path(directory.name) / 'workspace'
        self.workspace.mkdir()
        (self.workspace / 'app.py').write_text('value = 1\n')
        self.task = {'objective': 'Fix', 'max_turns': 40, 'checks': [], 'environment': {'profile': 'python-project', 'image': 'i', 'runtime': 'r'}}

    def worker(self, navigation, replies):
        sandbox = Sandbox()
        worker = ModelWorker(dict(CONFIG, navigation=navigation), sandbox)
        self.bodies = []
        replies = iter(replies)
        def request(path, body, **kwargs):
            self.bodies.append(json.loads(json.dumps(body)))
            return {'choices': [{'message': next(replies)}]}
        worker.request = request
        return worker, sandbox

    def test_configuration_is_validated_and_off_by_default(self):
        self.assertFalse(any(navigation_aids({}).values()))
        for bad in ({'maps': True}, {'map': 'yes'}, {'checkpoint': 101}, {'max_turns': 0}, {'checkpoint': True}, []):
            with self.assertRaises(ValueError, msg=bad):
                navigation_aids({'navigation': bad})

    def test_baseline_worker_is_unchanged_when_aids_are_off(self):
        worker, _ = self.worker({}, [{'role': 'assistant', 'content': 'Done'}])
        result = worker(self.workspace, self.task, None, 1)
        self.assertNotIn('handoff', result)
        self.assertEqual(self.bodies[0]['tools'], TOOLS)
        self.assertEqual(self.bodies[0]['messages'][0]['content'], SYSTEM)
        self.assertEqual(len(self.bodies), 1)

    def test_map_tool_runs_read_only_in_the_sandbox_and_only_when_offered(self):
        worker, sandbox = self.worker({'map': True}, [call('map', '{"query":"clamp"}'), {'role': 'assistant', 'content': 'Done'}])
        worker(self.workspace, self.task, None, 1)
        self.assertIn(MAP_TOOL, self.bodies[0]['tools'])
        self.assertIn('Locate code with map', self.bodies[0]['messages'][0]['content'])
        command, options = sandbox.commands[0]
        self.assertEqual(command[:3], ['python', '-I', '-c'])
        self.assertEqual(command[-2:], ['/workspace', 'clamp'])
        self.assertTrue(options['readonly'])
        worker, sandbox = self.worker({}, [call('map', '{}'), {'role': 'assistant', 'content': 'Done'}])
        worker(self.workspace, self.task, None, 1)
        self.assertEqual(sandbox.commands, [])
        self.assertIn('Invalid tool', self.bodies[1]['messages'][-1]['content'])
        node = dict(self.task, environment={'profile': 'node-ts', 'image': 'i', 'runtime': 'r'})
        worker, _ = self.worker({'map': True}, [{'role': 'assistant', 'content': 'Done'}])
        worker(self.workspace, node, None, 1)
        self.assertEqual(self.bodies[0]['tools'], TOOLS)

    def test_handoff_notes_reach_the_next_attempt(self):
        worker, _ = self.worker({'handoff': True}, [call('run', '{"command":"ls"}'), {'role': 'assistant', 'content': 'Stopped'}, {'role': 'assistant', 'content': 'core.py:8 clamp needs low bound'}])
        result = worker(self.workspace, self.task, None, 1)
        self.assertEqual(result['handoff'], 'core.py:8 clamp needs low bound')
        self.assertEqual(self.bodies[-1]['tool_choice'], 'none')
        attempt = self.workspace.parent / 'attempts/1'
        (attempt / 'worker.json').write_text(json.dumps(result))
        worker, _ = self.worker({'handoff': True}, [{'role': 'assistant', 'content': 'Done'}, {'role': 'assistant', 'content': ''}])
        result = worker(self.workspace, self.task, {'passed': False}, 2)
        self.assertIn('core.py:8 clamp needs low bound', self.bodies[0]['messages'][-1]['content'])
        self.assertNotIn('handoff', result)  # an empty note is not carried

    def test_checkpoint_asks_for_a_plan_only_when_nothing_changed(self):
        reads = [call('run', f'{{"command":"cat app.py # {n}"}}', str(n)) for n in range(3)]
        worker, _ = self.worker({'checkpoint': 2, 'max_turns': 3}, reads)
        result = worker(self.workspace, self.task, None, 1)
        self.assertEqual(result['turns'], 3)
        self.assertEqual(len(self.bodies), 3)
        self.assertIn('without changing any file', self.bodies[2]['messages'][-1]['content'])
        self.assertNotIn('without changing any file', json.dumps(self.bodies[1]))
        worker, _ = self.worker({'checkpoint': 2}, reads[:2] + [{'role': 'assistant', 'content': 'Done'}])
        worker.sandbox.execute = lambda *a, **k: ((self.workspace / 'new.py').write_text('x = 1\n'), {'exit_code': 0, 'output': ''})[1]
        worker(self.workspace, self.task, None, 1)
        self.assertNotIn('without changing any file', json.dumps(self.bodies))


if __name__ == '__main__':
    unittest.main()
