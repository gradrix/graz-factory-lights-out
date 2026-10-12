import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gflo.queue import run_queue

# A stand-in for `python -m gflo ... run TASK`: appends the task's objective to notes.txt in a copy of the task's
# repository and leaves that diff as the run's change.patch, as an accepted run would.
FAKE_RUN = '''import json, pathlib, shutil, subprocess, sys, tempfile, uuid
state = pathlib.Path(sys.argv[sys.argv.index("--state") + 1])
task = json.loads(pathlib.Path(sys.argv[sys.argv.index("run") + 1]).read_text())
run = uuid.uuid4().hex[:12]
(state / run).mkdir(parents=True)
with tempfile.TemporaryDirectory() as directory:
    copy = pathlib.Path(directory) / "copy"
    subprocess.run(["git", "clone", "-q", task["repo"], str(copy)], check=True)
    name = "pyproject.toml" if "manifest" in task["objective"] else "notes.txt"
    with (copy / name).open("a") as notes:
        notes.write(task["objective"] + "\\n")
    subprocess.run(["git", "-C", str(copy), "add", "-A"], check=True)
    patch = subprocess.run(["git", "-C", str(copy), "diff", "--cached", "--binary"], check=True, capture_output=True).stdout
(state / run / "change.patch").write_bytes(b"garbage\\n" if "garbage" in task["objective"] else patch)
print("Run: " + run)
'''


class QueueTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        (self.repo / 'notes.txt').write_text('base\n')
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(self.repo)], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=T', '-c', 'user.email=t@local', 'commit', '-qm', 'b'], check=True)
        self.base = self.head(self.repo)
        self.spec = self.root / 'queue.json'
        self.spec.write_text(json.dumps({'repo': 'repo', 'steps': [
            {'id': 'parse', 'objective': 'step one'}, {'id': 'store', 'objective': 'step two'}, {'objective': 'step three'}]}))
        self.statuses, self.built = {}, []

    def head(self, repo):
        return subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()

    def build(self, repo, objective, out):
        self.built.append((objective, (Path(repo) / 'notes.txt').read_text()))
        out.mkdir(parents=True)
        (out / 'task.json').write_text(json.dumps({'repo': str(repo), 'objective': objective}))

    def queue(self, verdicts=(), command=None):
        verdicts = iter(verdicts)
        def status(run):
            return {'status': self.statuses.setdefault(run, next(verdicts, 'accepted'))}
        return run_queue(self.spec, self.root / 'out', state=self.root / 'state', config=self.root / 'config.json',
                         environment_store=self.root / 'envs', build_task=self.build,
                         command=command or [sys.executable, '-c', FAKE_RUN], status=status)

    def test_steps_build_on_each_other_on_a_branch_of_a_controller_owned_clone(self):
        result = self.queue()
        self.assertEqual((result['committed'], result['steps']), (3, 3))
        # each step's task starts from the previous accepted state
        self.assertEqual(self.built, [('step one', 'base\n'), ('step two', 'base\nstep one\n'),
                                      ('step three', 'base\nstep one\nstep two\n')])
        clone = self.root / 'out' / 'integration'
        self.assertEqual((clone / 'notes.txt').read_text(), 'base\nstep one\nstep two\nstep three\n')
        log = subprocess.run(['git', '-C', str(clone), 'log', '--format=%s', f'{self.base}..gflo/queue'], check=True,
                             capture_output=True, text=True).stdout.split('\n')
        self.assertTrue(log[0].startswith('gflo queue step 3 '))
        self.assertTrue(log[2].startswith('gflo queue step parse '))
        self.assertEqual(subprocess.run(['git', '-C', str(clone), 'remote'], check=True, capture_output=True, text=True).stdout, '')
        # the source repository is only read
        self.assertEqual(self.head(self.repo), self.base)
        self.assertEqual((self.repo / 'notes.txt').read_text(), 'base\n')
        self.assertNotIn('gflo/queue', subprocess.run(['git', '-C', str(self.repo), 'branch'], check=True, capture_output=True, text=True).stdout)
        self.assertIn('+step three', (self.root / 'out' / 'feature.patch').read_text())
        report = Path(result['report']).read_text()
        self.assertIn('3 of 3 steps accepted and committed', report)
        self.assertIn('the feature is complete', report)
        runs = len(self.statuses)
        self.assertEqual(self.queue()['committed'], 3)  # rerunning a finished queue starts nothing
        self.assertEqual(len(self.statuses), runs)

    def test_a_step_without_acceptance_stops_the_queue_and_stays_stopped(self):
        result = self.queue(['accepted', 'exhausted'])
        self.assertEqual(result['committed'], 1)
        report = Path(result['report']).read_text()
        self.assertIn('| store | exhausted |', report)
        self.assertIn('| 3 | not reached | — | — |', report)
        self.assertIn('Step store ended without acceptance or integration', report)
        self.assertEqual((self.root / 'out' / 'integration' / 'notes.txt').read_text(), 'base\nstep one\n')
        self.assertEqual(self.queue()['committed'], 1)  # a final outcome is not retried
        self.assertEqual(len(self.statuses), 2)

    def test_runs_that_could_not_start_are_retried_on_the_next_invocation(self):
        down = [sys.executable, '-c', 'import sys; print("GFLO: model endpoint unreachable", file=sys.stderr); sys.exit(1)']
        result = self.queue(command=down)
        self.assertEqual(result['committed'], 0)
        self.assertIn('not started: GFLO: model endpoint unreachable', Path(result['report']).read_text())
        self.assertEqual(self.queue()['committed'], 3)
        self.assertEqual(len(self.built), 3)  # the built task is reused, not rebuilt

    def test_dirty_repository_bad_specs_and_a_tampered_clone_are_refused(self):
        (self.repo / 'notes.txt').write_text('edited\n')
        with self.assertRaisesRegex(ValueError, 'must be clean'):
            self.queue()
        subprocess.run(['git', '-C', str(self.repo), 'checkout', '-q', '.'], check=True)
        for steps in ([], [{'id': 'a', 'objective': 'x'}, {'id': 'a', 'objective': 'y'}], [{'id': '../x', 'objective': 'x'}], [{'id': 'a'}]):
            self.spec.write_text(json.dumps({'repo': 'repo', 'steps': steps}))
            with self.assertRaises(ValueError):
                self.queue()
        self.spec.write_text(json.dumps({'repo': 'repo', 'steps': [{'objective': 'x'}, {'objective': 'y'}]}))
        self.queue(['accepted', 'exhausted'])
        (self.root / 'out' / 'integration' / 'notes.txt').write_text('tampered\n')
        with self.assertRaisesRegex(ValueError, 'uncommitted changes'):
            self.queue()

    def test_an_interrupted_integration_is_finished_from_the_recorded_run(self):
        self.queue()
        clone, queue_path = self.root / 'out' / 'integration', self.root / 'out' / 'queue.json'
        runs = len(self.statuses)
        queue = json.loads(queue_path.read_text())
        queue['done']['3'].pop('commit')  # committed, then interrupted before queue.json was written
        queue_path.write_text(json.dumps(queue))
        head = self.head(clone)
        self.assertEqual(self.queue()['committed'], 3)
        self.assertEqual(self.head(clone), head)  # no duplicate commit
        queue = json.loads(queue_path.read_text())
        queue['done']['3'].pop('commit')  # interrupted between apply and commit
        queue_path.write_text(json.dumps(queue))
        subprocess.run(['git', '-C', str(clone), 'reset', '-q', '--soft', 'HEAD~1'], check=True)
        self.assertEqual(self.queue()['committed'], 3)
        self.assertEqual((clone / 'notes.txt').read_text(), 'base\nstep one\nstep two\nstep three\n')
        self.assertEqual(len(self.statuses), runs)  # the accepted run is integrated, not repeated

    def test_patches_that_do_not_apply_or_change_manifests_stop_the_queue(self):
        for name, objective in (('garbage', 'garbage patch'), ('manifest', 'manifest edit')):
            self.spec.write_text(json.dumps({'repo': 'repo', 'steps': [{'objective': 'step one'}, {'objective': objective}, {'objective': 'z'}]}))
            out = self.root / name
            result = run_queue(self.spec, out, state=self.root / 'state', config=self.root / 'c', environment_store=self.root / 'e',
                               build_task=self.build, command=[sys.executable, '-c', FAKE_RUN], status=lambda run: {'status': 'accepted'})
            self.assertEqual(result['committed'], 1)
            report = Path(result['report']).read_text()
            self.assertIn('| 2 | not integrated: ' + ('git apply failed' if name == 'garbage' else 'changes dependency manifests (pyproject.toml)'), report)
            self.assertEqual(subprocess.run(['git', '-C', str(out / 'integration'), 'status', '--porcelain'], check=True,
                                            capture_output=True, text=True).stdout, '')
            built = len(self.built)
            run_queue(self.spec, out, state=self.root / 'state', config=self.root / 'c', environment_store=self.root / 'e',
                      build_task=self.build, command=[sys.executable, '-c', FAKE_RUN], status=lambda run: {'status': 'accepted'})
            self.assertEqual(len(self.built), built)  # final: not retried

    def test_changed_steps_are_refused_and_the_drive_spec_keeps_the_record_test_command(self):
        self.queue(['accepted', 'exhausted'])
        self.spec.write_text(json.dumps({'repo': 'repo', 'steps': [{'objective': 'inserted'}, {'objective': 'step one'}]}))
        with self.assertRaisesRegex(ValueError, 'steps .* changed'):
            self.queue()
        from argparse import Namespace
        import shlex
        from ops.delivery.drive import queue_spec
        mined, tasks = self.root / 'mined' / 'c1', self.root / 'tasks'
        mined.mkdir(parents=True)
        command = ['env', 'A=1', 'python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-m', 'not db and not llm', 'tests']
        (mined / 'record.json').write_text(json.dumps({'test_command': command}))
        (self.root / 'steps.json').write_text(json.dumps({'c1': ['first', 'second']}))
        spec = json.loads(queue_spec(Namespace(mined=str(self.root / 'mined'), tasks=str(tasks), steps=str(self.root / 'steps.json'),
                                               state=str(self.root / 'drive')), 'c1').read_text())
        self.assertEqual(spec['env'], ['A=1'])
        self.assertEqual(shlex.split(spec['pytest_args']), ['-m', 'not db and not llm', 'tests'])
        self.assertEqual([step['objective'] for step in spec['steps']], ['first', 'second'])
        self.assertEqual(spec['repo'], str((tasks / 'c1' / 'repo').resolve()))


if __name__ == '__main__':
    unittest.main()
