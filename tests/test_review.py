import json
from pathlib import Path
import unittest

import test_runner
from gflo.runner import Factory


class ReviewTests(unittest.TestCase):
    setUp = test_runner.RunnerTests.setUp

    def test_checks_alone_cannot_accept_and_review_findings_drive_repair(self):
        seen = []
        def worker(workspace, task, previous, attempt):
            seen.append(previous)
            (workspace / 'app.py').write_text('value = 2\n')
            return {}
        def reviewer(workspace, task):
            return {'decision': 'repair' if len(seen) == 1 else 'pass', 'findings': [{'severity': 'major', 'path': 'app.py', 'line': 1, 'evidence': 'missing regression', 'repair': 'add regression'}] if len(seen) == 1 else [], 'question': ''}
        f = Factory(self.root / 'state', worker, lambda *a: {'passed': True}, reviewer=reviewer)
        run = f.create(self.task)
        result = f.resume(run)
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(result['attempts'], 2)
        self.assertEqual(seen[1]['review']['decision'], 'repair')
        self.assertTrue((f.state / run / 'attempts/1/review.json').exists())
        self.assertTrue(json.loads((f.state / run / 'task.json').read_text())['review_required'])

    def test_question_stops_without_verification_or_invented_policy(self):
        f = Factory(self.root / 'state', lambda *a: {'question': 'Flat fee or percentage, and what rate?'}, lambda *a: self.fail('Ambiguity must not be verified'))
        run = f.create(self.task)
        self.assertEqual(f.resume(run)['status'], 'needs_input')
        self.assertEqual(f.resume(run)['attempts'], 1)

    def test_required_review_unavailable_never_accepts(self):
        f = Factory(self.root / 'state', lambda *a: {}, lambda *a: {'passed': True}, reviewer=lambda *a: {})
        run = f.create(self.task)
        with self.assertRaisesRegex(ValueError, 'review'):
            Factory(f.state, lambda *a: {}, lambda *a: {'passed': True}).resume(run)
        self.assertNotEqual(f.status(run)['status'], 'accepted')

    def test_reviewer_has_fresh_context_and_rejects_ungrounded_findings(self):
        from gflo.review import Reviewer
        class Client:
            observe = staticmethod(lambda *a, **kw: None)
            config = {'model': 'local'}
            bodies = []
            def request(self, path, body, timeout):
                self.bodies.append(body)
                return {'choices': [{'message': {'content': json.dumps({'decision':'repair','findings':[{'severity':'major','path':'missing.py','line':99,'evidence':'bad','repair':'fix'}], 'question':''})}}]}
        client = Client()
        with self.assertRaisesRegex(ValueError, 'source'):
            Reviewer(client).review_files('Fix value', {'app.py': 'value=1\n'})
        self.assertEqual(len(client.bodies[-1]['messages']), 2)
        self.assertNotIn('tools', client.bodies[-1])

    def test_incomplete_or_contradictory_review_never_accepts(self):
        for index, review in enumerate([{'decision': 'pass'}, {'decision':'pass','findings':[],'question':'Which policy?'}]):
            f = Factory(self.root / f'state-{index}', lambda *a: {}, lambda *a: {'passed': True}, reviewer=lambda *a: review)
            run = f.create(self.task)
            with self.assertRaises(ValueError): f.resume(run)
            self.assertNotEqual(f.status(run)['status'], 'accepted')

    def test_deleted_review_evidence_invalidates_acceptance(self):
        from gflo.observe import Observer
        f = Factory(self.root / 'state', lambda *a: {}, lambda *a: {'passed':True}, reviewer=lambda *a: {'decision':'pass','findings':[],'question':''})
        run = f.create(self.task); f.resume(run)
        (f.state / run / 'attempts/1/review.json').unlink()
        self.assertEqual(f.status(run)['status'], 'invalidated')
        self.assertEqual(Observer(f.state).status(run)['status'], 'invalidated')

    def test_review_needs_input_is_not_repaired_without_a_new_contract(self):
        f = Factory(self.root / 'state', lambda *a: {}, lambda *a: {'passed': True}, reviewer=lambda *a: {'decision':'needs_input','findings':[],'question':'Which rate?'})
        run = f.create(self.task)
        self.assertEqual(f.resume(run)['status'], 'needs_input')
        self.assertEqual(f.resume(run)['attempts'], 1)

    def test_worker_question_tool_produces_a_bounded_question(self):
        from gflo.worker import ModelWorker
        from test_worker import FakeSandbox
        workspace = self.root / 'workspace'; workspace.mkdir()
        worker = ModelWorker({'endpoint':'http://127.0.0.1:18000','model':'test'}, FakeSandbox())
        responses = iter([{'choices':[{'message':{'role':'assistant','tool_calls':[{'id':'q','function':{'name':'question','arguments':'{"question":"Flat fee or percentage?"}'}}]}}]}, {'choices':[{'message':{'content':'{"needed":true,"basis":"Undecided policy","guidance":"Ask which fee model."}'}}]}])
        worker.request = lambda *a, **kw: next(responses)
        result = worker(workspace, {'objective':'Undecided policy','checks':[],'max_turns':1}, None, 1)
        self.assertEqual(result['question'], 'Flat fee or percentage?')

    def test_review_profile_reserves_output_after_bounded_thinking(self):
        from gflo.review import Reviewer
        class Client:
            observe = staticmethod(lambda *a, **kw: None)
            config = {'model':'local'}
            def request(inner, path, body, timeout):
                self.assertEqual(body['thinking_budget_tokens'], 1024)
                self.assertEqual(body['max_tokens'], 4096)
                self.assertTrue(body['chat_template_kwargs']['enable_thinking'])
                self.assertEqual(timeout, 120)
                self.assertNotIn('tools', body)
                return {'choices':[{'message':{'content':'{"decision":"pass","findings":[],"question":""}'}}]}
        self.assertEqual(Reviewer(Client()).review_files('Keep value', {'app.py':'value=1\n'})['decision'], 'pass')

    def test_question_assessment_requires_grounding_and_preserves_product_choice(self):
        from gflo.review import assess_question
        class Client:
            config = {'model':'local'}
            observe = staticmethod(lambda *a, **kw: None)
            result = {'needed':True,'basis':'rate is undecided','guidance':'Ask which rate.'}
            def request(inner, *args, **kwargs):
                return {'choices':[{'message':{'content':json.dumps(inner.result)}}]}
        client = Client()
        self.assertTrue(assess_question(client,'The rate is undecided.','Which rate?')['needed'])
        client.result = {'needed':False,'basis':'only valid integers','guidance':'Invalid strings are outside scope; implement valid integers.'}
        self.assertFalse(assess_question(client,'Inputs are only valid integers.','What about invalid strings?')['needed'])
        client.result['basis'] = 'invented requirement'
        with self.assertRaises(RuntimeError): assess_question(client,'Inputs are only valid integers.','What about strings?')

    def test_unnecessary_question_returns_guidance_and_worker_continues(self):
        from gflo.worker import ModelWorker
        from test_worker import FakeSandbox
        workspace = self.root / 'workspace'; workspace.mkdir()
        worker = ModelWorker({'endpoint':'http://127.0.0.1:18000','model':'test'}, FakeSandbox())
        responses = iter([
            {'choices':[{'message':{'role':'assistant','tool_calls':[{'id':'q','function':{'name':'question','arguments':'{"question":"What about strings?"}'}}]}}]},
            {'choices':[{'message':{'content':'{"needed":false,"basis":"valid integers only","guidance":"Strings are outside the input contract."}'}}]},
            {'choices':[{'message':{'role':'assistant','content':'Implemented integer behavior'},'finish_reason':'stop'}]}])
        worker.request = lambda *a, **kw: next(responses)
        result = worker(workspace, {'objective':'Inputs are valid integers only.','checks':[],'max_turns':2}, None, 1)
        self.assertNotIn('question', result)
        self.assertEqual(result['turns'], 2)
        self.assertIn('Strings are outside', (workspace.parent / 'attempts/1/trajectory.jsonl').read_text())

    def test_invalid_question_assessment_stops_instead_of_inventing_policy(self):
        from gflo.worker import ModelWorker
        from test_worker import FakeSandbox
        workspace = self.root / 'workspace'; workspace.mkdir()
        worker = ModelWorker({'endpoint':'http://127.0.0.1:18000','model':'test'}, FakeSandbox())
        responses = iter([
            {'choices':[{'message':{'role':'assistant','tool_calls':[{'id':'q','function':{'name':'question','arguments':'{"question":"Which policy?"}'}}]}}]},
            {'choices':[{'message':{'content':'not json'}}]}])
        worker.request = lambda *a, **kw: next(responses)
        with self.assertRaisesRegex(RuntimeError, 'assessment'):
            worker(workspace, {'objective':'Undecided policy','checks':[],'max_turns':2}, None, 1)

    def test_empty_assessment_response_has_a_useful_failure(self):
        from gflo.review import assess_question
        class Client:
            config = {'model':'local'}
            observe = staticmethod(lambda *a, **kw: None)
            def request(self, *a, **kw): return {'choices': []}
        with self.assertRaisesRegex(RuntimeError, 'malformed JSON verdict'):
            assess_question(Client(), 'The product policy is undecided.', 'Which policy?')

    def test_generated_binary_gets_actionable_repair_instead_of_crashing_review(self):
        seen=[]
        def worker(workspace, task, previous, attempt):
            seen.append(previous)
            cache=workspace/'app.pyc'
            if attempt==1: cache.write_bytes(b'\xa7\r\r\n\x00')
            else:
                self.assertIn('app.pyc', json.dumps(previous))
                cache.unlink()
            return {}
        f=Factory(self.root/'state', worker, lambda *a:{'passed':True}, reviewer=lambda *a:{'decision':'pass','findings':[],'question':''})
        run=f.create(self.task)
        self.assertEqual(f.resume(run)['status'],'accepted')
        self.assertEqual(len(seen),2)
