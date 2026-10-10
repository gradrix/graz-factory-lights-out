import json
from pathlib import Path
import tempfile
import unittest

import test_runner
from gflo.ensemble import BATTERY, battery
from gflo.review import SCOPE_NOTE, CandidateContentError, review_scope
from gflo.runner import Factory, changed_lines


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
        with self.assertRaisesRegex(CandidateContentError, 'exceed independent review bounds'):
            review_scope(root, {'changed_paths': sorted(big)})  # no hunks known: whole files exceed the bounds

    def test_without_changed_paths_large_projects_still_fail_closed(self):
        root = self.workspace({f'lib/m{index}.py': 'x' * 1000 for index in range(250)})
        with self.assertRaisesRegex(CandidateContentError, 'too large'):
            review_scope(root, {})

    def test_large_changed_files_are_reviewed_through_exact_line_hunks(self):
        lines = [f'value_{index} = {index}' for index in range(1, 12001)]
        root = self.workspace({'big.py': '\n'.join(lines), **{f'lib/m{index}.py': 'x' * 1000 for index in range(250)}})
        files, note = review_scope(root, {'changed_paths': ['big.py'], 'changed_lines': {'big.py': [[5000, 5001]]}})
        shown = files['big.py'].split('\n')
        self.assertEqual(len(shown), 12000)
        self.assertEqual(shown[4999], 'value_5000 = 5000')
        self.assertEqual(shown[4959], 'value_4960 = 4960')
        self.assertEqual(shown[0], '# ... unchanged lines not shown ...')  # each elided run starts with a marker
        self.assertEqual(shown[4958], '')
        self.assertEqual(shown[5040], 'value_5041 = 5041')
        self.assertEqual(shown[5041], '# ... unchanged lines not shown ...')
        self.assertEqual(shown[100], '')
        self.assertIn('line numbers are exact', note)

    def test_unified_diff_ranges_are_parsed(self):
        diff = (b'diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -3 +3,2 @@\n-x\n+y\n+z\n@@ -10,2 +11,0 @@\n-q\n-r\n'
                b'diff --git a/new.py b/new.py\n--- /dev/null\n+++ b/new.py\n@@ -0,0 +1,3 @@\n+a\n+b\n+c\n')
        self.assertEqual(changed_lines(diff), {'a.py': [[3, 4], [11, 11]], 'new.py': [[1, 3]]})

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
            self.assertEqual(task['changed_lines'], {'app.py': [[1, 1]], 'tests/test_app.py': [[1, 1]]})
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
