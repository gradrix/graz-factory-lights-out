"""Focused tests for the loopback read-only observer server in gflo/web.py.

The state fixture is written directly (sqlite plus run directory) so these
tests exercise the HTTP surface without needing the git-backed runner.
"""
import inspect
import json
import sqlite3
import tempfile
import threading
import time
import urllib.error
import urllib.request
import unittest
from contextlib import contextmanager
from pathlib import Path

from gflo.observe import schema
from gflo.web import server

RUN = 'run00000000001'


class WebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state'
        self._write_fixture()

    def _write_fixture(self):
        root = self.state / RUN
        (root / 'attempts' / '1').mkdir(parents=True)
        (root / 'task.json').write_text(json.dumps(
            {'objective': 'Set value to 2', 'max_attempts': 3, 'max_turns': 7}))
        (root / 'change.patch').write_text('--- a/app.py\n+++ b/app.py\n+value = 2\n')
        (root / 'attempts' / '1' / 'worker.json').write_text(
            json.dumps({'summary': 'plain evidence', 'turns': 2}))
        db = sqlite3.connect(self.state / 'state.sqlite')
        db.executescript('''
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, status TEXT NOT NULL, attempts INTEGER NOT NULL,
                contract_hash TEXT NOT NULL, message TEXT NOT NULL DEFAULT '');
        ''')
        schema(db)
        now = time.time()
        db.execute('INSERT INTO runs VALUES (?,?,0,?,?)', (RUN, 'exhausted', 'c0ffee', ''))
        db.execute('INSERT INTO execution VALUES (?,?,?,?,?,?,?,0)',
                   (RUN, None, None, now, 'finishing', now, '{}'))
        for kind in ('created', 'resumed', 'accepted'):
            db.execute('INSERT INTO events(run_id,time,version,kind,data) VALUES (?,?,1,?,?)',
                       (RUN, now, kind, '{"turns": 1}'))
        db.commit()
        db.close()

    def _make_state(self, state):
        """Create a state directory holding the schema but no runs."""
        db = sqlite3.connect(state / 'state.sqlite')
        db.executescript('''
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, status TEXT NOT NULL, attempts INTEGER NOT NULL,
                contract_hash TEXT NOT NULL, message TEXT NOT NULL DEFAULT '');
        ''')
        schema(db)
        db.commit()
        db.close()

    @contextmanager
    def _serve(self, port, state=None):
        """Serve the observer on `port` and yield a (status, headers, body) helper."""
        http = server(state if state is not None else self.state, port)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{http.server_port}'
        try:
            def fetch(path, headers=None, method='GET', data=None):
                request = urllib.request.Request(base + path, headers=headers or {},
                                                 method=method, data=data)
                try:
                    response = urllib.request.urlopen(request, timeout=10)
                except urllib.error.HTTPError as error:
                    return error.code, error.headers, error.read()
                return response.status, response.headers, response.read()
            yield http, fetch
        finally:
            http.shutdown()
            http.server_close()
            thread.join()

    def test_default_port_and_loopback_bind(self):
        # Edited on merge: binding the real default port fails while an observer runs on this machine.
        self.assertEqual(inspect.signature(server).parameters['port'].default, 8787)
        http = server(self.state, 0)
        try:
            self.assertEqual(http.server_address[0], '127.0.0.1')
        finally:
            http.server_close()

    def test_root_serves_the_progress_page_as_html(self):
        with self._serve(0) as (http, fetch):
            status, headers, body = fetch('/')
            self.assertEqual(status, 200)
            self.assertEqual(headers['Content-Type'], 'text/html; charset=utf-8')
            page = body.decode()
            # Stable, user-visible markers of the observer page: title, heading,
            # the run-listing container, the connection status element, the
            # empty-state sentence and the detail-section labels.
            self.assertIn('<title>GFLO runs</title>', page)
            self.assertIn('<h1>GFLO runs</h1>', page)
            self.assertIn('<main id="runs">', page)
            self.assertIn('id="connection"', page)
            self.assertIn('No runs yet. Start a task', page)
            self.assertIn('Execution details and evidence', page)
            self.assertIn('Durable event log (JSON)', page)
            # The page must target the documented loopback API route; the route
            # itself is exercised through the endpoints below, not source text.
            self.assertIn('/api/runs', page)

    def test_runs_list_reports_the_fixture_run_as_json(self):
        with self._serve(0) as (http, fetch):
            status, headers, body = fetch('/api/runs')
            self.assertEqual(status, 200)
            self.assertEqual(headers['Content-Type'], 'application/json; charset=utf-8')
            runs = json.loads(body)
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]['id'], RUN)
            self.assertEqual(runs[0]['status'], 'exhausted')
            self.assertEqual(runs[0]['budget']['max_attempts'], 3)
            self.assertEqual(runs[0]['budget']['max_turns'], 7)

    def test_empty_state_lists_no_runs_and_keeps_detail_routes_closed(self):
        """An empty fixture drives the page's 'no runs' state via the API."""
        empty = self.root / 'empty-state'
        empty.mkdir()
        self._make_state(empty)
        with self._serve(0, empty) as (http, fetch):
            status, headers, body = fetch('/api/runs')
            self.assertEqual(status, 200)
            self.assertEqual(headers['Content-Type'], 'application/json; charset=utf-8')
            self.assertEqual(json.loads(body), [])
            # The page is still served, and unknown runs stay hidden.
            status, headers, body = fetch('/')
            self.assertEqual(status, 200)
            self.assertEqual(headers['Content-Type'], 'text/html; charset=utf-8')
            self.assertIn('No runs yet. Start a task', body.decode())
            for path in ('/api/runs/' + RUN, '/api/runs/' + RUN + '/events',
                         '/api/runs/' + RUN + '/artifact?name=change.patch'):
                status, _, body = fetch(path)
                self.assertEqual(status, 404)
                self.assertIn(b'Run or artifact unavailable', body)

    def test_single_run_detail_is_the_status_object_not_a_list(self):
        with self._serve(0) as (http, fetch):
            status, headers, body = fetch('/api/runs/' + RUN)
            self.assertEqual(status, 200)
            self.assertEqual(headers['Content-Type'], 'application/json; charset=utf-8')
            self.assertEqual(body.decode()[:1], '{')
            report = json.loads(body)
            self.assertEqual(report['id'], RUN)
            self.assertEqual(report['phase'], 'exhausted')
            self.assertFalse(report['owner_alive'])
            self.assertIn('change.patch', report['artifacts'])
            self.assertIn('attempts/1/worker.json', report['artifacts'])

    def test_events_endpoint_returns_every_durable_event_in_order(self):
        with self._serve(0) as (http, fetch):
            status, _, body = fetch('/api/runs/' + RUN + '/events')
            self.assertEqual(status, 200)
            events = json.loads(body)
            self.assertEqual(len(events), 3)
            self.assertEqual([e['seq'] for e in events], [1, 2, 3])
            self.assertEqual([e['kind'] for e in events], ['created', 'resumed', 'accepted'])
            self.assertEqual(events[0]['run_id'], RUN)
            self.assertEqual(events[0]['data'], {'turns': 1})

    def test_events_after_cursor_is_a_strict_exclusive_window(self):
        with self._serve(0) as (http, fetch):
            _, _, body = fetch('/api/runs/' + RUN + '/events')
            last = json.loads(body)[-1]['seq']
            status, _, tail = fetch('/api/runs/' + RUN + f'/events?after={last}')
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(tail), [])
            status, _, middle = fetch('/api/runs/' + RUN + '/events?after=1')
            self.assertEqual(status, 200)
            self.assertEqual([e['seq'] for e in json.loads(middle)], [2, 3])
            status, _, whole = fetch('/api/runs/' + RUN + '/events?after=0')
            self.assertEqual(status, 200)
            self.assertEqual(len(json.loads(whole)), 3)
            # A non-integer cursor is rejected through the error path.
            status, _, broken = fetch('/api/runs/' + RUN + '/events?after=oops')
            self.assertEqual(status, 404)
            self.assertIn(b'Run or artifact unavailable', broken)

    def test_artifact_endpoint_serves_allowed_files_as_text(self):
        with self._serve(0) as (http, fetch):
            status, headers, body = fetch('/api/runs/' + RUN + '/artifact?name=change.patch')
            self.assertEqual(status, 200)
            self.assertEqual(headers['Content-Type'], 'text/plain; charset=utf-8')
            self.assertIn('--- a/app.py', body.decode())
            status, headers, body = fetch('/api/runs/' + RUN + '/artifact?name=attempts/1/worker.json')
            self.assertEqual(status, 200)
            self.assertEqual(headers['Content-Type'], 'text/plain; charset=utf-8')
            self.assertEqual(json.loads(body)['turns'], 2)

    def test_disallowed_names_unknown_runs_and_unknown_routes_are_404(self):
        with self._serve(0) as (http, fetch):
            for path in ('/api/runs/' + RUN + '/artifact?name=task.json',
                         '/api/runs/' + RUN + '/artifact',
                         '/api/runs/' + RUN + '/artifact?name=attempts/1/review.json',
                         '/api/other', '/api/runs/' + RUN + '/bogus',
                         # Look-alike paths must not be rescued by the route guard.
                         '/api/other/' + RUN, '/api/other/' + RUN + '/events',
                         '/x/y/' + RUN,
                         '/api/runs/missing-run', '/api/runs/missing-run/events',
                         '/api/runs/missing-run/artifact?name=change.patch',
                         '/api/runs/' + RUN + '/extra/still', '/elsewhere'):
                status, _, body = fetch(path)
                self.assertEqual(status, 404)
                self.assertIn(b'Run or artifact unavailable', body)

    def test_responses_carry_read_only_headers_and_exact_length(self):
        with self._serve(0) as (http, fetch):
            for path in ('/', '/api/runs', '/api/runs/' + RUN):
                status, headers, body = fetch(path)
                self.assertEqual(status, 200)
                self.assertEqual(int(headers['Content-Length']), len(body))
                self.assertEqual(headers['Cache-Control'], 'no-store')
                self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
                policy = headers['Content-Security-Policy']
                for directive in ("default-src 'none'", "connect-src 'self'",
                                  "frame-ancestors 'none'", "base-uri 'none'"):
                    self.assertIn(directive, policy)

    def test_non_loopback_host_is_rejected_before_any_lookup(self):
        with self._serve(0) as (http, fetch):
            status, _, body = fetch('/api/runs', headers={'Host': 'evil.example'})
            self.assertEqual(status, 403)
            self.assertIn(b'Use a loopback URL or SSH tunnel', body)
            # The port suffix and the localhost alias must still be accepted.
            status, _, body = fetch('/api/runs', headers={'Host': f'127.0.0.1:{http.server_port}'})
            self.assertEqual(status, 200)
            self.assertEqual(len(json.loads(body)), 1)
            status, _, body = fetch('/api/runs', headers={'Host': 'localhost'})
            self.assertEqual(status, 200)
            self.assertEqual(len(json.loads(body)), 1)

    def test_server_offers_no_write_methods(self):
        with self._serve(0) as (http, fetch):
            try:
                response = urllib.request.urlopen(
                    urllib.request.Request(f'http://127.0.0.1:{http.server_port}/api/runs',
                                           method='POST', data=b'{}'), timeout=10)
                self.fail('POST unexpectedly returned %d' % response.status)
            except urllib.error.HTTPError as error:
                self.assertEqual(error.code, 501)


if __name__ == '__main__':
    unittest.main()
