import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gflo.overnight import candidates, morning_report, night, test_like

BIG = 'def grade(score):\n    if score >= 90:\n        return "A"\n    if score >= 80:\n        return "B"\n    if score > 0 and not score > 100:\n        return "C"\n    return None\n'
SMALL = 'def one():\n    return 1\n'
# A stand-in for `python -m gflo ... run TASK`: prints the run id and writes the acceptance evidence a real run leaves.
FAKE_RUN = '''import json, pathlib, sys
state = pathlib.Path(sys.argv[sys.argv.index("--state") + 1])
task = pathlib.Path(sys.argv[sys.argv.index("run") + 1])
run = "%012x" % (abs(hash(task.parent.name)) % 16**12)
(state / run / "attempts" / "1").mkdir(parents=True)
output = "tests: tests/test_x.py; 6 new test functions; existing related tests: 0 modules, already killing 0 mutants; of the rest the new tests kill 7/9 = 0.78 (required 0.6)\\nSURVIVED app/grades.py:4 compare\\n"
(state / run / "attempts" / "1" / "verification.json").write_text(json.dumps({"checks": [{"output": output}]}))
print("Run: " + run)
'''


class OvernightTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.repo = self.root / 'repo'
        files = {'app/__init__.py': '', 'app/grades.py': BIG, 'app/tested.py': BIG, 'app/small.py': SMALL, 'app/tests/test_inner.py': BIG, 'app/grades_test.py': BIG, 'test_root.py': BIG,
                 'setup.py': BIG, 'tests/test_tested.py': 'from app.tested import grade\n', 'tests/test_pkg.py': 'import app\n'}
        for name, text in files.items():
            (self.repo / name).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / name).write_text(text)
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=T', '-c', 'user.email=t@local', 'commit', '-qm', 'b'], check=True)

    def test_candidates_put_untested_modules_first_and_skip_small_and_setup_files(self):
        ranked = candidates(self.repo)
        self.assertEqual([item['target'] for item in ranked], ['app/grades.py', 'app/tested.py'])
        self.assertFalse(test_like('gflo/recipes/test_acceptance.py'))  # source named test_* outside tests/ stays a target
        self.assertEqual([item['tested_by'] for item in ranked], [0, 1])  # a package import does not count
        self.assertEqual(len(candidates(self.repo, 1)), 1)

    def night(self, **kwargs):
        statuses = self.__dict__.setdefault('statuses', {})  # first run accepted, later ones exhausted
        def status(run):
            return {'status': statuses.setdefault(run, 'accepted' if not statuses else 'exhausted')}
        return night(self.repo, self.root / 'queue', state=self.root / 'state', config=self.root / 'config.json',
                     environment_store=self.root / 'envs', command=[sys.executable, '-c', FAKE_RUN], status=status, **kwargs)

    def test_queue_runs_each_module_once_resumes_and_reports(self):
        report = self.night(limit=1)
        queue = json.loads((self.root / 'queue' / 'queue.json').read_text())
        self.assertEqual(list(queue['done']), ['app/grades.py'])
        self.assertTrue((self.root / 'queue' / 'app-grades' / 'task.json').exists())
        text = report.read_text()
        self.assertIn('1 of 1 modules accepted', text)
        self.assertIn('6 tests, kill 7/9 = 0.78', text)
        self.assertIn('change.patch', text)
        self.assertIn('`app/grades.py`: app/grades.py:4 compare', text)
        report = self.night()  # continues with the rest, does not rerun the finished module
        queue = json.loads((self.root / 'queue' / 'queue.json').read_text())
        self.assertEqual(list(queue['done']), ['app/grades.py', 'app/tested.py'])
        self.assertEqual(queue['done']['app/grades.py']['status'], 'accepted')
        self.assertIn('1 of 2 modules accepted', report.read_text())

    def test_time_budget_stops_new_runs_and_another_repository_is_refused(self):
        ticks = iter([0, 0, 10, 4000, 4000])
        report = self.night(hours=1, clock=lambda: next(ticks))
        self.assertIn('1 of 2 planned not reached', report.read_text())
        other = self.root / 'other'
        other.mkdir()
        with self.assertRaisesRegex(ValueError, 'another repository'):
            night(other, self.root / 'queue', state=self.root / 'state', config=self.root / 'c', environment_store=self.root / 'e')

    def test_runs_that_could_not_start_are_retried_and_interrupts_still_write_the_report(self):
        down = [sys.executable, '-c', 'import sys; print("GFLO: model endpoint unreachable", file=sys.stderr); sys.exit(1)']
        report = night(self.repo, self.root / 'queue', state=self.root / 'state', config=self.root / 'c',
                       environment_store=self.root / 'e', command=down, limit=1)
        self.assertIn('| `app/grades.py` | 0 | not started | 0 s | GFLO: model endpoint unreachable | — |', report.read_text())
        self.night(limit=1)  # the rig is back: the module runs instead of staying "done"
        queue = json.loads((self.root / 'queue' / 'queue.json').read_text())
        self.assertEqual(queue['done']['app/grades.py']['status'], 'accepted')
        def interrupted(run):
            raise KeyboardInterrupt
        (self.root / 'queue' / 'report.md').unlink()
        with self.assertRaises(KeyboardInterrupt):
            night(self.repo, self.root / 'queue', state=self.root / 'state', config=self.root / 'c', environment_store=self.root / 'e',
                  command=[sys.executable, '-c', FAKE_RUN], status=interrupted)
        self.assertIn('app/grades.py', (self.root / 'queue' / 'report.md').read_text())

    def test_dirty_repository_and_unbuildable_modules(self):
        (self.repo / 'app' / 'grades.py').write_text(BIG + '# edit\n')
        with self.assertRaisesRegex(ValueError, 'must be clean'):
            self.night()
        subprocess.run(['git', '-C', str(self.repo), 'checkout', '-q', '.'], check=True)
        (self.root / 'queue' / 'app-grades' / 'acceptance').mkdir(parents=True)  # left by an interrupted build
        self.night(limit=1)
        self.assertEqual(json.loads((self.root / 'queue' / 'queue.json').read_text())['done']['app/grades.py']['status'], 'accepted')

    def test_report_shows_runs_that_did_not_start(self):
        text = morning_report({'repo': '/r', 'planned': [{'target': 'a.py', 'tested_by': 0}],
                               'done': {'a.py': {'status': 'not started', 'detail': 'GFLO: Missing config', 'seconds': 1}}})
        self.assertIn('| `a.py` | 0 | not started | 1 s | GFLO: Missing config | — |', text)


if __name__ == '__main__':
    unittest.main()
