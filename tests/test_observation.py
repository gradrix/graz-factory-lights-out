import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

import test_runner


class ObservationTests(unittest.TestCase):
    setUp = test_runner.RunnerTests.setUp
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
