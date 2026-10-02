import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

import test_runner


class ObservationTests(unittest.TestCase):
    setUp = test_runner.RunnerTests.setUp
    def test_event_and_live_detail_preserve_json_and_redact_nested_secrets(self):
        from gflo.runner import Factory
        from gflo.observe import Execution, Observer
        factory = Factory(self.root / 'state', None, None)
        run = factory.create(self.task)
        data = {'text': 'token="example-private-value"\nnext line',
                'nested': [{'access_token': 'hidden-value', 'count': 7}], 'flag': True}
        with Execution(factory.state, run) as execution:
            execution.emit('test_event', **data)
            view = Observer(factory.state)
            event = view.events(run)[-1]['data']
            detail = view.status(run)['detail']
            for record in (event, detail):
                self.assertNotIn('example-private-value', json.dumps(record))
                self.assertNotIn('hidden-value', json.dumps(record))
                self.assertEqual(record['nested'][0]['count'], 7)
                self.assertIs(record['flag'], True)
        self.assertEqual(data['nested'][0]['access_token'], 'hidden-value')

    def test_durable_events_and_budget_survive_reopen(self):
        from gflo.runner import Factory
        from gflo.observe import Observer
        factory = Factory(self.root / 'state', lambda *a: {}, lambda *a: {'passed': True})
        run = factory.create(self.task)
        factory.resume(run)
        view = Observer(factory.state)
        report = view.status(run)
        self.assertEqual(report['status'], 'accepted')
        self.assertEqual(report['budget']['max_attempts'], 2)
        events = view.events(run)
        self.assertEqual(sum(e['kind'] == 'accepted' for e in events), 1)
        factory.resume(run)
        self.assertEqual(view.events(run), events)
        self.assertTrue(all(e['version'] == 1 for e in events))
        self.assertIn('change.patch', report['artifacts'])

    def test_real_process_cancel_and_kill_have_honest_state(self):
        from gflo.runner import Factory
        from gflo.observe import Observer
        state = self.root / 'state'
        factory = Factory(state, None, None)
        run = factory.create(self.task)
        code = '''import sys,time
from gflo.runner import Factory
f=Factory(sys.argv[1],lambda *a: time.sleep(60),lambda *a: {'passed':True})
f.resume(sys.argv[2])
'''
        for kill in (False, True):
            process = subprocess.Popen([sys.executable, '-c', code, str(state), run], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                view = Observer(state)
                for _ in range(100):
                    report = view.status(run)
                    if report.get('owner_alive'): break
                    time.sleep(.05)
                self.assertTrue(report['owner_alive'])
                if kill:
                    process.kill()
                else:
                    factory.cancel(run)
                process.wait(timeout=10)
                report = view.status(run)
                self.assertFalse(report['owner_alive'])
                self.assertEqual(report['status'], 'interrupted' if kill else 'cancelled')
                self.assertNotEqual(report['phase'], 'accepted')
            finally:
                if process.poll() is None: process.kill(); process.wait()

    def test_dead_resume_owner_is_interrupted_even_before_old_cancelled_state_changes(self):
        from gflo.runner import Factory
        from gflo.observe import Execution, Observer
        factory = Factory(self.root / 'state', None, None)
        run = factory.create(self.task)
        factory.cancel(run)
        with Execution(factory.state, run):
            # A resumed owner can die between registering ownership and starting
            # its next attempt. The prior run status is still cancelled here.
            with factory.db:
                factory.db.execute('UPDATE execution SET identity=? WHERE run_id=?', ('dead-owner', run))
            report = Observer(factory.state).status(run)
            self.assertFalse(report['owner_alive'])
            self.assertEqual(report['status'], 'interrupted')

    def test_public_artifacts_reject_traversal_symlinks_and_secrets(self):
        from gflo.runner import Factory
        from gflo.observe import Observer
        f = Factory(self.root / 'state', lambda *a: {}, lambda *a: {'passed': True})
        run = f.create(self.task); f.resume(run)
        view = Observer(f.state)
        for name in ('../task.json', 'task.json', 'snapshot.git/config'):
            with self.assertRaises(ValueError): view.artifact(run, name)
        target = f.state / run / 'attempts/1/worker.json'
        target.unlink(); target.symlink_to(self.task)
        with self.assertRaises(ValueError): view.artifact(run, 'attempts/1/worker.json')

    def test_public_json_artifact_redaction_is_valid_json(self):
        from gflo.runner import Factory
        from gflo.observe import Observer
        factory = Factory(self.root / 'state', lambda *a: {}, lambda *a: {'passed': True})
        run = factory.create(self.task)
        factory.resume(run)
        artifact = factory.state / run / 'attempts/1/worker.json'
        artifact.write_text(json.dumps({'summary': 'password="example-private-value"',
                                        'nested': {'token': ['private-list-value']}, 'turns': 3}))
        public = Observer(factory.state).artifact(run, 'attempts/1/worker.json')
        self.assertEqual(json.loads(public)['turns'], 3)
        self.assertNotIn('example-private-value', public)
        self.assertNotIn('private-list-value', public)
        artifact.write_text('{"password":"unterminated')
        with self.assertRaisesRegex(ValueError, 'malformed'):
            Observer(factory.state).artifact(run, 'attempts/1/worker.json')
        artifact.write_text(json.dumps({'summary': 'x' * (1024 * 1024)}))
        with self.assertRaisesRegex(ValueError, 'display limit'):
            Observer(factory.state).artifact(run, 'attempts/1/worker.json')

    def test_redaction_consumes_whole_quoted_and_unterminated_values(self):
        from gflo.observe import redact_json
        for value in ('password="alpha beta"', 'token="alpha\\"beta"',
                      "secret='alpha beta'", 'api_key="alpha\nbeta"',
                      'token="alpha beta', 'token="alpha beta\\'):
            with self.subTest(value=value):
                public = redact_json({'summary': value, 'ordinary': 'retained'})
                self.assertNotIn('alpha', public)
                self.assertNotIn('beta', public)
                self.assertEqual(json.loads(public)['ordinary'], 'retained')

    def test_nested_encoded_credentials_are_hidden_in_public_artifacts(self):
        from gflo.runner import Factory
        from gflo.observe import Observer
        factory = Factory(self.root / 'state', lambda *a: {}, lambda *a: {'passed': True})
        run = factory.create(self.task)
        factory.resume(run)
        artifact = factory.state / run / 'attempts/1/worker.json'
        for value in ('token="ALPHA BETA"', 'secret="ALPHA\\"BETA"',
                      "password='ALPHA BETA'", 'token="ALPHA BETA'):
            for depth in range(5):
                value = json.dumps({'evidence': value})
                with self.subTest(depth=depth, value=value):
                    original = {'summary': 'Previous evidence:\n' + value, 'turns': 2}
                    artifact.write_text(json.dumps(original))
                    public = Observer(factory.state).artifact(run, 'attempts/1/worker.json')
                    self.assertNotIn('ALPHA', public)
                    self.assertNotIn('BETA', public)
                    self.assertEqual(json.loads(public)['turns'], 2)
                    self.assertEqual(json.loads(artifact.read_text()), original)

    def test_escaped_backslash_at_secret_end_preserves_following_evidence(self):
        from gflo.observe import redact_json
        for trailing in (0, 2, 4):
            value = 'token="ALPHA' + '\\' * trailing + '" ordinary=KEEP'
            for depth in range(5):
                with self.subTest(trailing=trailing, depth=depth):
                    public = redact_json({'summary': value})
                    self.assertNotIn('ALPHA', public)
                    self.assertIn('ordinary=KEEP', public)
                value = json.dumps({'evidence': value})

    def test_http_view_is_readonly_and_reconnects_with_durable_cursor(self):
        import threading
        import urllib.request
        import urllib.error
        from gflo.runner import Factory
        from gflo.web import server
        f = Factory(self.root / 'state', lambda *a: {}, lambda *a: {'passed': True})
        run = f.create(self.task); f.resume(run)
        for _ in range(2):
            http = server(f.state, 0)
            thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
            base = f'http://127.0.0.1:{http.server_port}'
            try:
                with urllib.request.urlopen(base) as r:
                    self.assertIn('GFLO runs', r.read().decode())
                with urllib.request.urlopen(base + '/api/runs') as r:
                    self.assertEqual(json.load(r)[0]['status'], 'accepted')
                with urllib.request.urlopen(base + '/api/runs/' + run + '/events') as r:
                    events = json.load(r)
                with urllib.request.urlopen(base + '/api/runs/' + run + '/events?after=' + str(events[-1]['seq'])) as r:
                    self.assertEqual(json.load(r), [])
                with urllib.request.urlopen(base + '/api/runs/' + run + '/artifact?name=change.patch') as r:
                    self.assertEqual(r.status, 200)
                for request in (urllib.request.Request(base, method='POST'), urllib.request.Request(base, headers={'Host': 'evil.example'})):
                    with self.assertRaises(urllib.error.HTTPError): urllib.request.urlopen(request)
            finally:
                http.shutdown(); http.server_close(); thread.join()

    def test_stalled_model_has_live_heartbeat_without_fake_progress(self):
        from gflo.observe import Execution, Observer, redact
        from gflo.runner import Factory
        f = Factory(self.root / 'state', None, None); run = f.create(self.task)
        with Execution(f.state, run) as execution:
            execution.emit('model_wait', turn=2, timeout_s=300)
            with f.db:
                f.db.execute('UPDATE execution SET action_at=action_at-40 WHERE run_id=?', (run,))
            time.sleep(1.1)
            status = Observer(f.state).status(run)
            self.assertTrue(status['owner_alive'])
            self.assertTrue(status['model_slow'])
            self.assertLess(status['heartbeat_age_s'], 2)
            self.assertGreater(status['action_age_s'], 40)
        self.assertNotIn('sensitive', redact('Authorization: Bearer sensitive password=sensitive api_key="sensitive"'))

    def test_observer_can_start_before_first_task(self):
        from gflo.observe import Observer
        self.assertEqual(Observer(self.root / 'not-created').status(), [])

    def test_cancel_during_startup_is_terminal_and_resumable(self):
        from gflo.runner import Factory
        from gflo.observe import Observer
        state = self.root / 'state'
        factory = Factory(state, None, None); run = factory.create(self.task)
        code = '''import sys,time
from gflo.runner import Factory
Factory(sys.argv[1],lambda *a:{},lambda *a:{'passed':True},cleanup=lambda *a:time.sleep(60)).resume(sys.argv[2])
'''
        process = subprocess.Popen([sys.executable, '-c', code, str(state), run], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                if Observer(state).status(run).get('owner_alive'): break
                time.sleep(.05)
            factory.cancel(run); process.wait(timeout=10)
            self.assertEqual(Observer(state).status(run)['status'], 'cancelled')
            self.assertEqual(Factory(state, lambda *a: {}, lambda *a: {'passed': True}).resume(run)['status'], 'accepted')
        finally:
            if process.poll() is None: process.kill(); process.wait()
