"""Controlled prototype gates. No model, service, prepared runtime or rig calls."""
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planning_pilot_prototype as p


class BuilderControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def source(self):
        source = self.root / 'input'; source.mkdir()
        (source / 'main.py').write_text('print("ordinary")\n')
        (source / 'main.py').chmod(0o755)
        (source / 'nested').mkdir(mode=0o750)
        (source / 'nested' / 'data.py').write_text('VALUE=1\n')
        (source / 'nested' / 'data.py').chmod(0o640)
        return source
    def factory(self, source):
        acceptance = self.root / 'acceptance'; acceptance.mkdir()
        (acceptance / 'check.py').write_text('pass\n')
        task = self.root / 'task.json'
        p.save(task, {'repo': str(source), 'acceptance': str(acceptance), 'objective': 'Preserve source',
                      'checks': [['python', '/acceptance/check.py']], 'review_required': False})
        factory = p.PilotFactory(self.root / 'state', None, None)
        # Factory.create inherits sanitized configuration in actual arm subprocess.
        with patch.dict(os.environ, p.git_environment(), clear=True):
            run_id = factory.create(task)
        return factory, run_id
    def test_exact_mode_restore_preserves_tree_and_prior_source(self):
        source = self.source(); before = p.fingerprint(source); modes = p.checked_tree(source)
        repo = self.root / 'repo'; p.initialize_repository(source, repo)
        factory, run = self.factory(repo)
        receipt = {'modes': modes, 'candidate': before}
        result = p.restore_checkpoint(factory, run, source, receipt)
        self.assertEqual(result['after'], before)
        self.assertEqual(p.checked_tree(source), modes)
        self.assertEqual(p.fingerprint(source), before)
        self.assertEqual(p.checked_tree(factory.status(run)['workspace']), modes)
        factory.db.close()
    def test_restore_changed_bytes_and_executable_refuses(self):
        source = self.source(); modes = p.checked_tree(source)
        repo = self.root / 'repo'; p.initialize_repository(source, repo)
        factory, run = self.factory(repo); target = Path(factory.status(run)['workspace'])
        (target / 'main.py').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'content'):
            p.restore_checkpoint(factory, run, source, {'modes': modes, 'candidate': p.fingerprint(source)})
        (target / 'main.py').write_bytes((source / 'main.py').read_bytes()); (target / 'main.py').chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'executable'):
            p.restore_checkpoint(factory, run, source, {'modes': modes, 'candidate': p.fingerprint(source)})
        factory.db.close()
    def test_git_controls_rejected_before_host_git(self):
        for name in ('.git', '.gitattributes', '.gitmodules', '.gitignore', 'nested/.git/config'):
            with self.subTest(name=name), tempfile.TemporaryDirectory(dir=self.root) as directory:
                source = Path(directory); path = source / name; path.parent.mkdir(exist_ok=True, parents=True)
                path.write_text('not trusted')
                with patch.object(p, 'git') as call, self.assertRaisesRegex(ValueError, 'Git control'):
                    p.initialize_repository(source, source.parent / ('copy-' + source.name))
                call.assert_not_called()
    def test_git_directory_link_and_special_modes_refused(self):
        source = self.source(); (source / '.git').mkdir()
        with self.assertRaisesRegex(ValueError, 'Git control'): p.checked_tree(source)
        (source / '.git').rmdir(); (source / 'link').symlink_to('/tmp')
        with self.assertRaises(ValueError): p.checked_tree(source)
        (source / 'link').unlink(); (source / 'main.py').chmod(0o4755)
        with self.assertRaisesRegex(ValueError, 'Special permission'): p.checked_tree(source)
    def test_global_hook_filter_and_template_cannot_execute(self):
        source = self.source(); marker = self.root / 'EXECUTED'
        template = self.root / 'template'; (template / 'hooks').mkdir(parents=True)
        hook = template / 'hooks' / 'pre-commit'; hook.write_text('#!/bin/sh\ntouch ' + str(marker)); hook.chmod(0o755)
        config = self.root / 'global'; config.write_text('[core]\n hooksPath = ' + str(template / 'hooks') + '\n[filter "evil"]\n clean = touch ' + str(marker) + '\n')
        with patch.dict(os.environ, {'GIT_CONFIG_GLOBAL': str(config), 'GIT_TEMPLATE_DIR': str(template)}):
            p.initialize_repository(source, self.root / 'repo')
        self.assertFalse(marker.exists())
    def test_slot_raw_shape_and_strict_types(self):
        identity = {'running': True}; health = {'status': 'ok'}
        slot = {'id': 0, 'n_ctx': 98304, 'is_processing': False}
        self.assertEqual(p.classify_idle(health, [slot], identity, identity, identity)['state'], 'idle')
        for slots in ([slot, None], [], {}, [dict(slot, id=False)], [dict(slot, is_processing=0)], [dict(slot, n_ctx='98304')]):
            with self.subTest(slots=slots), self.assertRaises(ValueError):
                p.classify_idle(health, slots, identity, identity, identity)
    def test_raw_malformed_body_captured_before_json_parser(self):
        class Response(io.BytesIO): status = 200
        class Opener:
            def open(self, request, timeout): return Response(b'{broken JSON')
        request = type('Request', (), {'data': b'{"model":"test"}'})()
        capture = p.CaptureOpener(Opener(), self.root)
        with self.assertRaises(json.JSONDecodeError): json.load(capture.open(request, 1))
        self.assertEqual((self.root / 'response.body').read_bytes(), b'{broken JSON')
        self.assertTrue(json.loads((self.root / 'transport.json').read_bytes())['complete'])
    def test_http_failure_body_and_overflow_preserved(self):
        class Opener:
            def open(self, request, timeout):
                raise urllib.error.HTTPError('http://127.0.0.1', 503, 'busy', {}, io.BytesIO(b'busy body'))
        request = type('Request', (), {'data': b'{}'})()
        with self.assertRaises(urllib.error.HTTPError): p.CaptureOpener(Opener(), self.root).open(request, 1)
        self.assertEqual((self.root / 'response.body').read_bytes(), b'busy body')
        class Response(io.BytesIO): status = 200
        class Large:
            def open(self, request, timeout): return Response(b'x' * 101)
        with patch.object(p, 'RESPONSE_BYTES', 100), self.assertRaisesRegex(ValueError, 'capacity'):
            p.CaptureOpener(Large(), self.root).open(request, 1)
        self.assertEqual((self.root / 'response.body').stat().st_size, 100)
        self.assertFalse(json.loads((self.root / 'transport.json').read_bytes())['complete'])
    def test_normal_exit_descendant_is_terminated(self):
        command = [sys.executable, '-c', 'import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]);']
        result = p.supervise(command, self.root / 'output', time.monotonic() + 5)
        self.assertTrue(result['client_group_absent'])
        self.assertEqual(result['exit_code'], 0)
    def test_sigterm_supervisor_returns_failed_cancellation(self):
        target = self.root / 'result'
        code = ('import sys,time,json; sys.path.insert(0,' + repr(str(Path(p.__file__).parent)) + '); '
                'import planning_pilot_prototype as p; from pathlib import Path; '
                'r=p.supervise([sys.executable,"-c","import time; time.sleep(30)"],Path(' + repr(str(self.root / 'child')) + '),time.monotonic()+30); '
                'Path(' + repr(str(target)) + ').write_text(json.dumps(r))')
        process = subprocess.Popen([sys.executable, '-c', code])
        try:
            time.sleep(0.2); process.send_signal(signal.SIGTERM); process.wait(timeout=5)
            result = json.loads(target.read_bytes())
            self.assertEqual(result['stop'], 'cancelled'); self.assertTrue(result['client_group_absent'])
        finally:
            if process.poll() is None: process.kill(); process.wait()


if __name__ == '__main__': unittest.main()
