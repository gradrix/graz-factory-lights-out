import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from gflo import ensemble as e
from gflo.review import validate

OBJECTIVE = 'A1: Tests pass. README example works.\n'


def wire(decision='pass', ids=(2,), observations=(2,), line=1, path='README.md'):
    findings = [] if decision == 'pass' else [{'severity': 'major', 'source': {'path': path, 'line': line},
                                               'requirements': list(ids), 'observations': list(observations),
                                               'inference': 'documented example exits 2'}]
    return {'version': 1, 'decision': decision, 'findings': findings, 'question': ''}


def audit_answer(assignment, bearing='unrelated'):
    ids = json.loads(assignment.split('Classify ONLY these command IDs (other commands are audited separately): ', 1)[1].split(']', 1)[0] + ']')
    return {'version': 1, 'commands': [{'id': i, 'bearing': bearing if i == 2 else 'unrelated',
                                        'segments': [] if bearing == 'unrelated' or i != 2 else [2]} for i in ids]}


class Sandbox:
    environment = None

    def __init__(self, change=None):
        self.calls = []; self.change = change

    def execute(self, workspace, command, *, readonly=False, timeout=60, acceptance=None):
        self.calls.append((command, readonly))
        if self.change and len(self.calls) == 2: self.change()
        output = 'ACTUAL EXIT: 2\nunknown action' if len(self.calls) == 2 else f'out{len(self.calls)}'
        return {'command': command, 'image': 'img', 'exit_code': 0, 'timed_out': False, 'output': output, 'elapsed_s': 0.1}


class Client:
    """Fake local model: explorers propose no commands; units answer per role from a table."""
    config = {'model': 'local'}

    def __init__(self, answers, reasoning=100):
        self.answers = answers; self.reasoning = reasoning; self.roles = []; self.bodies = []; self.events = []

    def observe(self, event, **facts):
        self.events.append(event)

    def request(self, path, body, timeout=300, max_response_bytes=None):
        if path == '/tokenize':
            value = self.reasoning.get(self.roles[-1], 100) if isinstance(self.reasoning, dict) else self.reasoning
            if isinstance(value, list): value = value.pop(0)
            return {'tokens': [0] * value}
        self.bodies.append(body)
        if 'tools' in body:
            self.roles.append('explore')
            return {'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': 'done'}}]}
        text = body['messages'][1]['content'].split('ASSIGNMENT: ', 1)[1]
        role = 'audit' if text.startswith('Role: evidence auditor') else 'prosecutor' if text.startswith('Role: prosecutor') else 'judge'
        if role == 'judge':
            role = next((f'judge-{f}' for f in ('strict', 'charitable') if e.PANEL[f] in text), 'judge-neutral')
        self.roles.append(role)
        answer = self.answers.get(role, self.answers.get(role.split('-')[0]))
        if isinstance(answer, list): answer = answer.pop(0) if len(answer) > 1 else answer[0]
        if callable(answer): answer = answer(text)
        return {'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(answer),
                                                                   'reasoning_content': 'r'}}], 'usage': {}}


class EnsembleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name) / 'workspace'; self.workspace.mkdir()
        (self.workspace / 'README.md').write_text('example\n')

    def review(self, answers, sandbox=None, reasoning=100):
        client = Client(answers, reasoning)
        reviewer = e.EnsembleReviewer(client, sandbox or Sandbox(), Path(self.tmp.name) / 'evidence')
        return reviewer, client

    def test_statements_units_and_catalog_bounds(self):
        found = e.statements('A1: Tests pass. README example works; it must run.\n\nA2: (Optional) docs.\n')
        self.assertEqual([s['text'] for s in found], ['A1: Tests pass.', 'README example works; it must run.', 'A2: (Optional) docs.'])
        self.assertEqual(sum(len(u['ids']) for u in e.units(found)), 3)
        big = e.catalog([{'role': 'battery', 'command': 'c', 'exit_code': 0, 'timed_out': False, 'output': 'x' * 20000}])
        self.assertTrue(big['commands'][0]['output_limited'])
        self.assertEqual(big['commands'][0]['elided_bytes'], e.OUTPUT_BYTES - 2 * e.HEAD)
        self.assertTrue(all(len(e.encoded(s['text'])) <= e.SEGMENT_BYTES for s in big['segments']))

    def test_audit_validation_and_foreign_citation_pruning(self):
        value = e.catalog([{'role': 'b', 'command': 'c1', 'exit_code': 0, 'timed_out': False, 'output': 'one'},
                           {'role': 'b', 'command': 'c2', 'exit_code': 2, 'timed_out': False, 'output': 'two'}])
        mixed = {'version': 1, 'commands': [{'id': 1, 'bearing': 'supports', 'segments': [1, 2]}, {'id': 2, 'bearing': 'unrelated', 'segments': []}]}
        self.assertEqual(e.prune_audit(mixed, value), 1); e.validate_audit(mixed, value)
        foreign = {'version': 1, 'commands': [{'id': 1, 'bearing': 'supports', 'segments': [2]}, {'id': 2, 'bearing': 'unrelated', 'segments': []}]}
        self.assertEqual(e.prune_audit(foreign, value), 0)
        with self.assertRaisesRegex(ValueError, 'does not belong'): e.validate_audit(foreign, value)
        with self.assertRaisesRegex(ValueError, 'exactly the assigned'): e.validate_audit({'version': 1, 'commands': mixed['commands'][:1]}, value)

    def test_panel_needs_two_judges_on_common_statement(self):
        one, other = wire('repair'), wire('repair', ids=(1,), observations=(1,))
        self.assertEqual(e.panel_decision([one, wire(), other], [1, 2])[0], 'pass')
        decision, statement, findings = e.panel_decision([one, wire(), one], [1, 2])
        self.assertEqual((decision, statement, len(findings)), ('repair', 2, 2))

    def test_clean_review_passes_with_readonly_commands_and_no_judge(self):
        reviewer, client = self.review({'audit': audit_answer, 'prosecutor': wire()})
        result = reviewer.review(self.workspace, OBJECTIVE)
        self.assertEqual(result, {'decision': 'pass', 'findings': [], 'question': ''})
        self.assertTrue(all(readonly for _, readonly in reviewer.sandbox.calls))
        self.assertEqual(len(reviewer.sandbox.calls), 2)
        self.assertNotIn('judge-neutral', client.roles)
        self.assertEqual(client.roles.count('explore'), 3)
        unit_bodies = [b for b in client.bodies if 'tools' not in b]
        self.assertTrue(all(b['messages'][0]['content'] == e.POLICY and b['response_format'] == {'type': 'json_object'} for b in unit_bodies))
        self.assertTrue(list((Path(self.tmp.name) / 'evidence').glob('*/catalog.json')))

    def test_panel_backed_repair_maps_to_runner_schema(self):
        reviewer, client = self.review({'audit': lambda t: audit_answer(t, 'contradicts'), 'prosecutor': wire(),
                                        'judge-strict': wire('repair'), 'judge-charitable': wire(), 'judge-neutral': wire('repair')})
        result = reviewer.review(self.workspace, OBJECTIVE)
        self.assertEqual(result['decision'], 'repair')
        self.assertEqual(len(result['findings']), 1)  # two judges on the same line and statement collapse to one
        finding = result['findings'][0]
        self.assertEqual((finding['path'], finding['line']), ('README.md', 1))
        self.assertIn('ACTUAL EXIT: 2', finding['evidence'])
        self.assertIn('README example works.', finding['repair'])
        validate(result, {'README.md': 'example\n'})

    def test_exhausted_role_climbs_the_ladder_then_fails_closed(self):
        reviewer, client = self.review({'audit': audit_answer, 'prosecutor': wire()},
                                       reasoning={'audit': 100, 'prosecutor': [8192, 24576, 65536]})
        with self.assertRaises(e.EnsembleIncomplete):
            reviewer.review(self.workspace, OBJECTIVE)
        budgets = [b['thinking_budget_tokens'] for b in client.bodies if 'tools' not in b][-3:]
        self.assertEqual(budgets, [8192, 24576, 65536])
        self.assertEqual(client.bodies[-1]['max_tokens'], 69632)

    def test_rejected_answer_gets_quoted_correction(self):
        wrong = {'version': 1, 'commands': [{'id': 1, 'bearing': 'supports', 'segments': [2]}, {'id': 2, 'bearing': 'unrelated', 'segments': []}]}
        reviewer, client = self.review({'audit': [wrong, audit_answer], 'prosecutor': wire()})
        self.assertEqual(reviewer.review(self.workspace, OBJECTIVE)['decision'], 'pass')
        corrected = [b for b in client.bodies if 'Controller rejection of a previous answer' in b['messages'][1]['content']]
        self.assertEqual(len(corrected), 1)
        self.assertIn('does not belong to that command', corrected[0]['messages'][1]['content'])

    def test_candidate_change_during_review_fails(self):
        sandbox = Sandbox(change=lambda: (self.workspace / 'README.md').write_text('changed\n'))
        reviewer, _ = self.review({'audit': audit_answer, 'prosecutor': wire()}, sandbox)
        with self.assertRaisesRegex(e.EnsembleIncomplete, 'Candidate changed'):
            reviewer.review(self.workspace, OBJECTIVE)

    def test_explorer_commands_join_the_catalog(self):
        calls = iter([[{'id': 'a', 'type': 'function', 'function': {'name': 'run', 'arguments': json.dumps({'command': 'python -c 1'})}}], []])
        reviewer, client = self.review({'audit': audit_answer, 'prosecutor': wire()})
        original = client.request
        def request(path, body, timeout=300, max_response_bytes=None):
            if 'tools' in body and body['messages'][0]['content'].endswith(e.ROLE_TEXT['tester']):
                planned = next(calls, [])
                if planned:
                    return {'choices': [{'finish_reason': 'tool_calls', 'message': {'role': 'assistant', 'content': None, 'tool_calls': planned}}]}
            return original(path, body, timeout, max_response_bytes)
        client.request = request
        reviewer.review(self.workspace, OBJECTIVE)
        catalog = json.loads(next((Path(self.tmp.name) / 'evidence').glob('*/catalog.json')).read_text())
        self.assertEqual([c['role'] for c in catalog['commands']], ['battery', 'battery', 'tester'])
        self.assertEqual(reviewer.sandbox.calls[2], (['sh', '-c', 'python -c 1'], True))

    def test_node_profile_is_refused(self):
        sandbox = Sandbox(); sandbox.environment = mock.Mock(profile='node-ts')
        reviewer, _ = self.review({}, sandbox)
        with self.assertRaisesRegex(ValueError, 'qualified only for Python'):
            reviewer(self.workspace, {'objective': OBJECTIVE})

    def test_runner_repair_loop_receives_ensemble_findings(self):
        import test_runner
        from gflo.runner import Factory
        fixture = test_runner.RunnerTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        seen = []
        def worker(workspace, task, previous, attempt):
            seen.append(previous); (workspace / 'app.py').write_text(f'value = {attempt}\n'); return {}
        answers = [{'decision': 'repair', 'findings': [{'severity': 'major', 'path': 'app.py', 'line': 1,
                    'evidence': 'e', 'repair': 'Satisfy objective statement 1'}], 'question': ''},
                   {'decision': 'pass', 'findings': [], 'question': ''}]
        reviewer = mock.Mock(side_effect=lambda workspace, task: answers.pop(0))
        factory = Factory(fixture.root / 'state', worker, lambda *a: {'passed': True}, reviewer=reviewer)
        run = factory.create(fixture.task)
        self.assertEqual(factory.resume(run)['status'], 'accepted')
        self.assertEqual(seen[1]['review']['findings'][0]['repair'], 'Satisfy objective statement 1')


class ConfigTests(unittest.TestCase):
    def test_review_mode_is_validated_and_ensemble_is_opt_in(self):
        from gflo.__main__ import main
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.json'
            config.write_text(json.dumps({'endpoint': 'http://127.0.0.1:1', 'model': 'm', 'review': 'bogus'}))
            with mock.patch('sys.stderr') as stderr:
                self.assertEqual(main(['--config', str(config), '--state', directory, 'resume', 'missing']), 1)
            self.assertIn('review must be', ''.join(c.args[0] for c in stderr.write.call_args_list))


if __name__ == '__main__':
    unittest.main()
