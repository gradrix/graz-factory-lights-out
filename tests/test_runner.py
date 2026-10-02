import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from gflo.runner import Factory


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        (self.repo / 'app.py').write_text('value = 0\n')
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=Test', '-c', 'user.email=test@local', 'commit', '-qm', 'base'], check=True)
        self.acceptance = self.root / 'acceptance'
        self.acceptance.mkdir()
        (self.acceptance / 'check.py').write_text('assert True\n')
        self.task = self.root / 'task.json'
        self.task.write_text(json.dumps({'repo': str(self.repo), 'objective': 'Set value to 2', 'acceptance': str(self.acceptance), 'checks': [['python', '-I', '/acceptance/check.py']], 'max_attempts': 2}))

    def test_failure_evidence_drives_repair_and_source_is_unchanged(self):
        feedback = []
        def worker(workspace, task, previous, attempt):
            feedback.append(previous)
            (workspace / 'app.py').write_text(f'value = {attempt}\n')
            return {'summary': 'changed'}
        def verifier(workspace, task, acceptance):
            passed = (workspace / 'app.py').read_text() == 'value = 2\n'
            return {'passed': passed, 'checks': [{'output': 'expected 2', 'exit_code': 0 if passed else 1}]}
        factory = Factory(self.root / 'state', worker, verifier)
        run_id = factory.create(self.task)
        result = factory.resume(run_id)
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(result['attempts'], 2)
        self.assertIn('expected 2', json.dumps(feedback[1]))
        self.assertEqual((self.repo / 'app.py').read_text(), 'value = 0\n')
        self.assertIn('+value = 2', Path(result['patch']).read_text())
        self.assertTrue((self.root / 'state' / run_id / 'attempts/1/verification.json').exists())
        self.assertEqual(factory.resume(run_id)['attempts'], 2)

    def test_interrupted_attempt_resumes_with_retained_work(self):
        calls = []
        def worker(workspace, task, previous, attempt):
            calls.append(attempt)
            if attempt == 1:
                (workspace / 'partial.txt').write_text('retained')
                raise KeyboardInterrupt()
            self.assertEqual((workspace / 'partial.txt').read_text(), 'retained')
            self.assertIn('interrupted', previous['error'])
            return {'summary': 'finished'}
        factory = Factory(self.root / 'state', worker, lambda *args: {'passed': True, 'checks': []})
        run_id = factory.create(self.task)
        with self.assertRaises(KeyboardInterrupt):
            factory.resume(run_id)
        self.assertEqual(factory.status(run_id)['status'], 'interrupted')
        reopened = Factory(self.root / 'state', worker, lambda *args: {'passed': True, 'checks': []})
        self.assertEqual(reopened.resume(run_id)['status'], 'accepted')
        self.assertEqual(calls, [1, 2])

    def test_exhaustion_never_becomes_success(self):
        factory = Factory(self.root / 'state', lambda *args: {}, lambda *args: {'passed': False})
        run_id = factory.create(self.task)
        self.assertEqual(factory.resume(run_id)['status'], 'exhausted')
        self.assertEqual(factory.resume(run_id)['attempts'], 2)

    def test_acceptance_is_snapshotted_and_tampering_is_rejected(self):
        factory = Factory(self.root / 'state', lambda *args: {}, lambda *args: {'passed': True})
        run_id = factory.create(self.task)
        (self.acceptance / 'check.py').write_text('changed original')
        frozen = self.root / 'state' / run_id / 'acceptance/check.py'
        self.assertEqual(frozen.read_text(), 'assert True\n')
        frozen.write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'acceptance'):
            factory.resume(run_id)

    def test_dirty_source_is_rejected(self):
        (self.repo / 'app.py').write_text('uncommitted')
        factory = Factory(self.root / 'state', lambda *args: {}, lambda *args: {})
        with self.assertRaisesRegex(ValueError, 'clean'):
            factory.create(self.task)

    def test_resume_published_verification_does_not_repeat_worker(self):
        factory = Factory(self.root / 'state', lambda *args: {}, lambda *args: {'passed': True})
        run_id = factory.create(self.task)
        original = factory._finish
        factory._finish = lambda *args: (_ for _ in ()).throw(RuntimeError('injected crash'))
        with self.assertRaisesRegex(RuntimeError, 'injected'):
            factory.resume(run_id)
        factory._finish = original
        factory.worker = lambda *args: self.fail('Worker repeated after saved verdict')
        self.assertEqual(factory.resume(run_id)['status'], 'accepted')
        self.assertEqual(factory.status(run_id)['attempts'], 1)

    def test_resume_after_attempt_directory_was_created_before_transaction(self):
        factory = Factory(self.root / 'state', lambda *args: {}, lambda *args: {'passed': True})
        run_id = factory.create(self.task)
        (self.root / 'state' / run_id / 'attempts/1').mkdir(parents=True)
        self.assertEqual(factory.resume(run_id)['status'], 'accepted')

    def test_changed_accepted_workspace_or_patch_is_not_reported_as_accepted(self):
        factory = Factory(self.root / 'state', lambda *args: {}, lambda *args: {'passed': True})
        run_id = factory.create(self.task)
        factory.resume(run_id)
        (self.root / 'state' / run_id / 'workspace/app.py').write_text('tampered')
        self.assertEqual(factory.status(run_id)['status'], 'invalidated')
        with self.assertRaisesRegex(ValueError, 'changed'):
            factory.resume(run_id)

    def test_cleanup_happens_before_recovery_observes_workspace(self):
        called = []
        def cleanup(workspace):
            called.append(True)
        def worker(*args):
            self.assertTrue(called)
            return {}
        factory = Factory(self.root / 'state', worker, lambda *args: {'passed': True}, cleanup=cleanup)
        factory.resume(factory.create(self.task))

    def test_contract_change_and_unknown_id_fail_closed(self):
        factory = Factory(self.root / 'state', lambda *args: {}, lambda *args: {'passed': True})
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            factory.resume('../elsewhere')
        run_id = factory.create(self.task)
        (self.root / 'state' / run_id / 'task.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'contract'):
            factory.resume(run_id)

    def test_task_validation_and_single_runner_lock(self):
        factory = Factory(self.root / 'state', lambda *args: {}, lambda *args: {'passed': True})
        original = json.loads(self.task.read_text())
        for key, value in [('objective', ''), ('checks', []), ('checks', ['echo']), ('max_attempts', 0), ('max_turns', True)]:
            invalid = dict(original, **{key: value})
            self.task.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                factory.create(self.task)
        self.task.write_text(json.dumps(original))
        with factory.locked():
            with self.assertRaisesRegex(RuntimeError, 'active'):
                Factory(self.root / 'state', None, None).create(self.task)

    def test_changed_patch_invalidates_acceptance(self):
        factory = Factory(self.root / 'state', lambda *args: {}, lambda *args: {'passed': True})
        run_id = factory.create(self.task)
        result = factory.resume(run_id)
        Path(result['patch']).write_text('changed patch')
        self.assertEqual(factory.status(run_id)['status'], 'invalidated')

    def test_cli_run_resume_and_status_without_source_mutation(self):
        from gflo.__main__ import main
        from unittest.mock import patch
        from contextlib import redirect_stdout
        import io
        config = self.root / 'config.json'
        config.write_text(json.dumps({'endpoint': 'http://127.0.0.1:18000', 'model': 'example'}))
        prefix = ['--state', str(self.root / 'cli-state'), '--config', str(config)]
        with patch('gflo.__main__.ModelWorker') as worker, patch('gflo.__main__.Sandbox') as sandbox, redirect_stdout(io.StringIO()) as output:
            worker.return_value.return_value = {'summary': 'done'}
            sandbox.return_value.verify.return_value = {'passed': True}
            self.assertEqual(main(prefix + ['run', str(self.task)]), 0)
            run_id = output.getvalue().splitlines()[0].split()[-1]
            self.assertEqual(main(prefix + ['resume', run_id]), 0)
            self.assertEqual(main(prefix + ['status', run_id]), 0)
            self.assertEqual(worker.return_value.call_count, 1)
