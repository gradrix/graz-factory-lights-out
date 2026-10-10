import json
from pathlib import Path
import tempfile
import unittest

import test_runner
from gflo.ensemble import BATTERY, battery
from gflo.review import SCOPE_NOTE, CandidateContentError, review_scope
from gflo.runner import Factory


class ReviewScopeTests(unittest.TestCase):
    def workspace(self, files):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for name, data in files.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_bytes(data if isinstance(data, bytes) else data.encode())
        return root

    def test_small_project_is_reviewed_whole_as_before(self):
        root = self.workspace({'app.py': 'x = 1\n', 'tests/test_app.py': 'pass\n'})
        files, note = review_scope(root, {'changed_paths': ['app.py']})
        self.assertEqual(sorted(files), ['app.py', 'tests/test_app.py'])
        self.assertEqual(note, '')
        with self.assertRaisesRegex(CandidateContentError, 'Non-text'):
            review_scope(self.workspace({'app.py': 'x\n', 'cache.pyc': b'\xff\x00'}), {'changed_paths': ['app.py']})

    def test_large_project_shows_only_changed_files_with_a_scope_note(self):
        big = {f'lib/m{index}.py': 'x' * 1000 for index in range(250)}
        root = self.workspace({**big, 'app.py': 'x = 2\n', 'fixtures/run.fit': b'\xff\x00\x01', 'tests/test_app.py': 'pass\n'})
        files, note = review_scope(root, {'changed_paths': ['app.py', 'fixtures/run.fit', 'removed.py', 'tests/test_app.py']})
        self.assertEqual(sorted(files), ['app.py', 'fixtures/run.fit', 'tests/test_app.py'])
        self.assertIn('binary file changed, 3 bytes', files['fixtures/run.fit'])
        self.assertEqual(note, SCOPE_NOTE)
        with self.assertRaisesRegex(CandidateContentError, 'Changed files exceed'):
            review_scope(root, {'changed_paths': sorted(big)})

    def test_without_changed_paths_large_projects_still_fail_closed(self):
        root = self.workspace({f'lib/m{index}.py': 'x' * 1000 for index in range(250)})
        with self.assertRaisesRegex(CandidateContentError, 'too large'):
            review_scope(root, {})

    def test_ensemble_battery_runs_the_operator_test_command(self):
        self.assertEqual(battery(None), BATTERY)
        runner, documented = battery(['env', 'A=1', 'python', '-m', 'pytest', '-m', 'not db'])
        self.assertIn("cd /tmp/p && env A=1 python -m pytest -m 'not db' > /tmp/out", runner)
        self.assertEqual(documented, BATTERY[1])


class RunnerReviewScopeTests(unittest.TestCase):
    setUp = test_runner.RunnerTests.setUp

    def test_reviewer_receives_controller_computed_changed_paths(self):
        seen = []
        def worker(workspace, task, previous, attempt):
            (workspace / 'app.py').write_text('value = 2\n')
            (workspace / 'tests').mkdir()
            (workspace / 'tests' / 'test_app.py').write_text('pass\n')
            return {}
        def reviewer(workspace, task):
            seen.append(task['changed_paths'])
            return {'decision': 'pass', 'findings': [], 'question': ''}
        factory = Factory(self.root / 'state', worker, lambda *a: {'passed': True}, reviewer=reviewer)
        result = factory.resume(factory.create(self.task))
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(seen, [['app.py', 'tests/test_app.py']])


    def test_review_timeout_fails_the_attempt_instead_of_stopping_the_run(self):
        calls = []
        def worker(workspace, task, previous, attempt):
            (workspace / 'app.py').write_text(f'value = {attempt}\n')
            return {}
        def reviewer(workspace, task):
            calls.append(1)
            if len(calls) == 1:
                raise TimeoutError('timed out')
            return {'decision': 'pass', 'findings': [], 'question': ''}
        factory = Factory(self.root / 'state', worker, lambda *a: {'passed': True}, reviewer=reviewer)
        run = factory.create(self.task)
        result = factory.resume(run)
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(result['attempts'], 2)
        first = json.loads((factory.state / run / 'attempts/1/verification.json').read_text())
        self.assertIn('review timed out', first['reviewability']['error'])


if __name__ == '__main__':
    unittest.main()
