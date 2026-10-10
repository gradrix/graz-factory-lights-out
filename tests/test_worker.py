import tempfile
from pathlib import Path
import unittest

from gflo.worker import ModelWorker


class FakeSandbox:
    def cleanup(self, workspace):
        pass
    def execute(self, workspace, command, **kwargs):
        return {'exit_code': 0, 'output': 'app.py'}
    def verify(self, *args):
        return {'passed': False, 'checks': [{'output': 'expected value 2'}]}


class WorkerTests(unittest.TestCase):
    def test_enabled_reasoning_has_a_separate_budget_on_the_http_wire(self):
        import http.server
        import json
        import threading
        requests = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({'choices': [{'message': {
                    'role': 'assistant', 'content': 'Done'}, 'finish_reason': 'stop'}]}).encode())
            def log_message(self, *args):
                pass
        with http.server.HTTPServer(('127.0.0.1', 0), Handler) as server, tempfile.TemporaryDirectory() as directory:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for reasoning in ('none', 'medium'):
                    workspace = Path(directory) / reasoning / 'workspace'
                    workspace.mkdir(parents=True)
                    worker = ModelWorker({'endpoint': f'http://127.0.0.1:{server.server_port}',
                                          'model': 'test', 'reasoning': reasoning}, FakeSandbox())
                    worker(workspace, {'objective': 'Fix', 'max_turns': 1, 'checks': []}, None, 1)
                    wire = requests[-1]
                    self.assertEqual(wire['max_tokens'], 4096)
                    self.assertEqual(wire['chat_template_kwargs'], {'enable_thinking': reasoning != 'none'})
                    if reasoning == 'medium':
                        self.assertEqual(wire['thinking_budget_tokens'], 1024)
                    else:
                        self.assertNotIn('thinking_budget_tokens', wire)
                    trace = [json.loads(line) for line in
                             (workspace.parent / 'attempts/1/trajectory.jsonl').read_text().splitlines()]
                    self.assertEqual(next(r['body'] for r in trace if r['event'] == 'request'), wire)
            finally:
                server.shutdown()
                thread.join()

    def test_redacted_trajectory_remains_json_without_mutating_model_content(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / 'workspace'
            workspace.mkdir()
            worker = ModelWorker({'endpoint': 'http://127.0.0.1:18000', 'model': 'test',
                                  'password': 123456789}, FakeSandbox())
            content = 'token = "example-private-value"\nordinary text: \\"quoted\\"'
            message = {'role': 'assistant', 'content': content}
            worker.request = lambda *a, **kw: {'choices': [{'message': message, 'finish_reason': 'stop'}]}
            result = worker(workspace, {'objective': 'Fix', 'max_turns': 1, 'checks': []}, None, 1)
            trace = (workspace.parent / 'attempts/1/trajectory.jsonl').read_text()
            records = [json.loads(line) for line in trace.splitlines()]
            self.assertNotIn('example-private-value', trace)
            self.assertNotIn('123456789', trace)
            self.assertEqual(records[0]['config']['password'], '[redacted]')
            self.assertEqual(result['summary'], content)
            self.assertEqual(message['content'], content)

    def test_previous_review_is_private_in_trace_but_unchanged_for_model(self):
        import copy
        import json
        previous = {'passed': False, 'review': {'evidence': 'token="ALPHA BETA"'}}
        original = copy.deepcopy(previous)
        requests = []
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / 'workspace'
            workspace.mkdir()
            worker = ModelWorker({'endpoint': 'http://127.0.0.1:1', 'model': 'test'}, FakeSandbox())
            def response(path, body, **kwargs):
                requests.append(copy.deepcopy(body))
                return {'choices': [{'message': {'role': 'assistant', 'content': 'Done'}}]}
            worker.request = response
            worker(workspace, {'objective': 'Fix', 'max_turns': 1, 'checks': []}, previous, 2)
            sent = requests[0]['messages'][-1]['content'].split('\n', 1)[1]
            self.assertEqual(json.loads(sent), original)
            self.assertEqual(previous, original)
            trace = (workspace.parent / 'attempts/2/trajectory.jsonl').read_text()
            self.assertTrue(all(isinstance(json.loads(line), dict) for line in trace.splitlines()))
            self.assertNotIn('ALPHA', trace)
            self.assertNotIn('BETA', trace)

    def test_tools_and_completion_leave_a_replayable_trace(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / 'workspace'
            workspace.mkdir()
            worker = ModelWorker({'endpoint': 'http://127.0.0.1:18000', 'model': 'test'}, FakeSandbox())
            messages = iter([
                {'role': 'assistant', 'content': None, 'tool_calls': [{'id': '1', 'type': 'function', 'function': {'name': 'run', 'arguments': '{"command":"ls"}'}}]},
                {'role': 'assistant', 'content': None, 'tool_calls': [{'id': '2', 'type': 'function', 'function': {'name': 'check', 'arguments': '{}'}}]},
                {'role': 'assistant', 'content': 'Done'}])
            worker.request = lambda *args, **kwargs: {'choices': [{'message': next(messages), 'finish_reason': 'stop'}]}
            result = worker(workspace, {'objective': 'Fix value', 'max_turns': 4, 'checks': []}, None, 1)
            self.assertEqual(result['turns'], 3)
            trace = workspace.parent / 'attempts/1/trajectory.jsonl'
            self.assertIn('expected value 2', trace.read_text())

    def test_remote_inference_and_redirects_are_not_implicitly_allowed(self):
        with self.assertRaisesRegex(ValueError, 'loopback'):
            ModelWorker({'endpoint': 'https://example.com', 'model': 'test'}, FakeSandbox())

    def test_malformed_tools_and_repeated_calls_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / 'workspace'
            workspace.mkdir()
            worker = ModelWorker({'endpoint': 'http://127.0.0.1:18000', 'model': 'test'}, FakeSandbox())
            message = {'role': 'assistant', 'tool_calls': [{'id': '1', 'function': {'name': 'unknown', 'arguments': '{bad'}}]}
            worker.request = lambda *args, **kwargs: {'choices': [{'message': message}]}
            result = worker(workspace, {'objective': 'Fix', 'max_turns': 8, 'checks': []}, {'error': 'old failure'}, 1)
            self.assertTrue(result['limited'])
            self.assertEqual(result['turns'], 5)
            self.assertIn('old failure', (workspace.parent / 'attempts/1/trajectory.jsonl').read_text())

    def test_unparseable_model_tool_calls_are_retried_then_end_the_attempt(self):
        from gflo.worker import ModelHTTPError
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / 'workspace'
            workspace.mkdir()
            worker = ModelWorker({'endpoint': 'http://127.0.0.1:18000', 'model': 'test'}, FakeSandbox())
            seen = []
            def malformed(path, body, **kwargs):
                seen.append(body['messages'][-1]['content'])
                raise ModelHTTPError(500, 'Failed to parse tool call arguments as JSON: missing closing quote')
            worker.request = malformed
            result = worker(workspace, {'objective': 'Fix', 'max_turns': 8, 'checks': []}, None, 1)
            self.assertTrue(result['limited'])
            self.assertIn('malformed', result['summary'])
            self.assertEqual(len(seen), 3)
            self.assertIn('shorter', seen[1])
            replies = iter([ModelHTTPError(500, 'Failed to parse tool call arguments as JSON'), {'choices': [{'message': {'role': 'assistant', 'content': 'Done'}}]}])
            def recovers(*args, **kwargs):
                reply = next(replies)
                if isinstance(reply, Exception):
                    raise reply
                return reply
            worker.request = recovers
            self.assertEqual(worker(workspace, {'objective': 'Fix', 'max_turns': 8, 'checks': []}, None, 2)['summary'], 'Done')
            worker.request = lambda *a, **k: (_ for _ in ()).throw(ModelHTTPError(500, 'out of memory'))
            with self.assertRaisesRegex(RuntimeError, 'HTTP 500: out of memory'):  # other server errors still stop the run
                worker(workspace, {'objective': 'Fix', 'max_turns': 8, 'checks': []}, None, 3)

    def test_turn_budget_and_redirect_rejection(self):
        from gflo.worker import NoRedirect
        with self.assertRaisesRegex(ValueError, 'redirects'):
            NoRedirect().redirect_request(None, None, 302, '', {}, 'http://example.com')
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / 'workspace'
            workspace.mkdir()
            worker = ModelWorker({'endpoint': 'http://127.0.0.1:18000', 'model': 'test'}, FakeSandbox())
            worker.request = lambda *args, **kwargs: {'choices': [{'message': {'role': 'assistant', 'tool_calls': [{'id': '1', 'function': {'name': 'run', 'arguments': '{"command":"ls"}'}}]}}]}
            result = worker(workspace, {'objective': 'Fix', 'max_turns': 1, 'checks': []}, None, 1)
            self.assertTrue(result['limited'])

    def test_http_requests_use_key_file_and_report_errors(self):
        import http.server
        import json
        import threading
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200 if self.path == '/ok' else 400)
                self.end_headers()
                self.wfile.write(json.dumps({'auth': self.headers.get('Authorization')}).encode())
            def log_message(self, *args):
                pass
        with http.server.HTTPServer(('127.0.0.1', 0), Handler) as server, tempfile.TemporaryDirectory() as directory:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                key = Path(directory) / 'key'
                key.write_text('test-key')
                worker = ModelWorker({'endpoint': f'http://127.0.0.1:{server.server_port}', 'model': 'test', 'api_key_file': str(key)}, FakeSandbox())
                self.assertEqual(worker.request('/ok')['auth'], 'Bearer test-key')
                with self.assertRaisesRegex(RuntimeError, 'HTTP 400'):
                    worker.request('/bad')
            finally:
                server.shutdown()
                thread.join()
