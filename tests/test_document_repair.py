import io
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import test_documents
from gflo import documents
from gflo.recipes import document_extract


class DocumentRepairTests(unittest.TestCase):
    executor = test_documents.DocumentsTests.executor
    setUp = test_documents.DocumentsTests.setUp

    def prepared(self):
        evidence = self.store.acquire(test_documents.APPROVAL)
        client = type('Client', (), {'config': {'model': 'local'}, 'endpoint': 'http://127.0.0.1:18000'})()
        answer = {'status': 'supported', 'claims': [{'text': 'Use compact separators.', 'citations': [
            {'evidence_id': evidence['id'], 'span': 1, 'excerpt': evidence['spans'][0]}]}], 'reason': ''}
        return evidence, client, answer

    @staticmethod
    def response(value):
        if isinstance(value, dict) and value.get('status') == 'supported':
            value = dict(value, claims=[{'text': c['text'], 'spans': [x['span'] for x in c['citations']]} for c in value['claims']])
        return {'choices': [{'message': {'content': value if isinstance(value, str) else json.dumps(value)}}]}

    def test_40000_events_are_complete_and_plus_one_refuses(self):
        self.assertEqual(document_extract.VERSION, 'document-text-v2')
        self.assertEqual(document_extract.extract(b'<!--x-->' * 39997 + b'<p>visible</p>', 'text/html'), ['visible'])
        with self.assertRaisesRegex(ValueError, 'event'):
            document_extract.extract(b'<!--x-->' * 39998 + b'<p>visible</p>', 'text/html')

    def test_repair_retains_rejected_response_and_replays_offline(self):
        evidence, client, answer = self.prepared()
        rejected = self.response('{broken')
        corrected = self.response(answer)
        with patch('gflo.documents.bounded_answer', side_effect=[rejected, corrected]) as infer:
            saved = self.store.answer(evidence['id'], client)
        self.assertEqual(infer.call_count, 2)
        receipt = self.store.resolve(saved['id'])['receipt']
        self.assertEqual(receipt['format'], 3)
        self.assertEqual([a['validation'] for a in receipt['attempts']], ['invalid', 'valid'])
        self.assertEqual(json.loads((self.store.root / saved['id'] / 'response-1.json').read_bytes()), rejected)
        self.assertEqual(json.loads((self.store.root / saved['id'] / 'response-2.json').read_bytes()), corrected)
        with patch('gflo.documents.bounded_answer', side_effect=AssertionError('Offline inference')):
            self.assertEqual(self.store.replay(saved['id'])['answer'], answer)
        repair_request = infer.call_args.args[1]
        self.assertIn('{broken', repair_request['messages'][-1]['content'])

    def test_exhaustion_is_inspectable_failure_never_replayable(self):
        evidence, client, answer = self.prepared()
        with patch('gflo.documents.bounded_answer', return_value=self.response('{bad')) as infer:
            with self.assertRaises(ValueError) as caught:
                self.store.answer(evidence['id'], client)
        self.assertEqual(infer.call_count, 2)
        failed = self.store.resolve(caught.exception.identifier)
        self.assertEqual(failed['receipt']['kind'], 'answer_failure')
        self.assertNotIn('answer', failed['receipt'])
        self.assertEqual(len(failed['receipt']['attempts']), 2)
        with self.assertRaises(ValueError):
            self.store.replay(failed['id'])

    def test_first_valid_call_and_legacy_receipt_remain_offline(self):
        evidence, client, answer = self.prepared()
        response = self.response(answer)
        with patch('gflo.documents.bounded_answer', return_value=response) as infer:
            saved = self.store.answer(evidence['id'], client)
        self.assertEqual(infer.call_count, 1)
        self.assertEqual({p.name for p in (self.store.root / saved['id']).iterdir()}, {'receipt.json', 'response-1.json'})
        old_receipt = {'format': 1, 'kind': 'answer', 'evidence_id': evidence['id'],
                       'answer': answer, 'response': {'choices': [{'message': {'content': json.dumps(answer)}}]},
                       'verdict': 'citation_provenance_valid_not_semantic_entailment'}
        stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=self.store.root))
        old = self.store._publish(stage, old_receipt, lambda: False)
        old_bytes = (self.store.root / old['id'] / 'receipt.json').read_bytes()
        with patch('gflo.documents.bounded_answer', side_effect=AssertionError('Offline inference')):
            self.assertEqual(self.store.replay(old['id'])['answer'], answer)
        self.assertEqual((self.store.root / old['id'] / 'receipt.json').read_bytes(), old_bytes)

    def test_transport_overflow_envelope_and_authority_never_repair(self):
        evidence, client, answer = self.prepared()
        cases = [TimeoutError('timed out'), RuntimeError('transport failed'), ValueError('byte limit'),
                 self.response('x' * 65536), {}, {'choices': [{'message': {}}]},
                 {'choices': [{'message': {'content': json.dumps(answer), 'tool_calls': [{}]}}]},
                 {'choices': [{'message': {'content': json.dumps(answer), 'function_call': {}}}]}]
        for result in cases:
            with self.subTest(result=str(result)[:40]):
                with patch('gflo.documents.bounded_answer', side_effect=result if isinstance(result, Exception) else None,
                           return_value=result) as infer, self.assertRaises(documents.AnswerFailure) as caught:
                    self.store.answer(evidence['id'], client)
                self.assertEqual(infer.call_count, 1)
                failed = self.store.resolve(caught.exception.identifier)
                self.assertEqual(failed['receipt']['kind'], 'answer_failure')
                self.assertNotIn('answer', failed['receipt'])

    def test_invalid_reference_and_second_transport_keeps_first(self):
        evidence, client, answer = self.prepared()
        bad = copy.deepcopy(answer)
        bad['claims'][0]['citations'][0]['span'] = 1000
        with patch('gflo.documents.bounded_answer', side_effect=[self.response(bad), TimeoutError('second failed')]) as infer:
            with self.assertRaises(documents.AnswerFailure) as caught:
                self.store.answer(evidence['id'], client)
        receipt = self.store.resolve(caught.exception.identifier)['receipt']
        self.assertEqual([a['validation'] for a in receipt['attempts']], ['invalid', 'inference_error'])
        self.assertEqual({p.name for p in (self.store.root / caught.exception.identifier).iterdir()}, {'receipt.json', 'response-1.json'})
        self.assertEqual(infer.call_count, 2)
        self.assertEqual(json.loads((self.store.root / caught.exception.identifier / 'response-1.json').read_bytes()), self.response(bad))

    def test_cancel_after_first_response_and_during_final_sync_publish_nothing(self):
        evidence, client, answer = self.prepared()
        initial = {p.name for p in self.store.root.iterdir()}
        cancel = [False]
        def cancelled_response(*args, **kwargs):
            cancel[0] = True
            return self.response('{bad')
        with patch('gflo.documents.bounded_answer', side_effect=cancelled_response) as infer, self.assertRaises(ValueError):
            self.store.answer(evidence['id'], client, cancelled=lambda: cancel[0])
        self.assertEqual(infer.call_count, 1)
        self.assertEqual({p.name for p in self.store.root.iterdir()}, initial)
        cancel[0] = False
        original_sync = documents.sync_directory
        def late_cancel(path):
            original_sync(path)
            if not (path / 'pending').exists():
                cancel[0] = True
        with patch('gflo.documents.bounded_answer', return_value=self.response(answer)), patch('gflo.documents.sync_directory', side_effect=late_cancel), self.assertRaises(ValueError):
            self.store.answer(evidence['id'], client, cancelled=lambda: cancel[0])
        self.assertEqual({p.name for p in self.store.root.iterdir()}, initial)

    def test_ledger_and_response_tampering_refuse_even_with_new_receipt_identity(self):
        evidence, client, answer = self.prepared()
        with patch('gflo.documents.bounded_answer', return_value=self.response(answer)):
            saved = self.store.answer(evidence['id'], client)
        good = self.store.resolve(saved['id'])['receipt']
        changes = [lambda r: r['answer']['claims'][0].update(text='different claim'),
                   lambda r: r['attempts'][0].update(number=True),
                   lambda r: r['attempts'][0].update(response_size=True),
                   lambda r: r['attempts'][0].update(request_sha256='0' * 64),
                   lambda r: r['attempts'][0].update(validation='invalid'),
                   lambda r: r['attempts'][0].update(response_sha256=None),
                   lambda r: r.update(question='different question'),
                   lambda r: r['profile'].update(max_tokens=4096),
                   lambda r: r['attempts'].append(copy.deepcopy(r['attempts'][0]))]
        for change in changes:
            receipt = copy.deepcopy(good); change(receipt)
            stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=self.store.root))
            shutil.copy2(self.store.root / saved['id'] / 'response-1.json', stage / 'response-1.json')
            with self.assertRaises(ValueError):
                self.store._publish(stage, receipt, lambda: False)
            shutil.rmtree(stage)
        response = self.store.root / saved['id'] / 'response-1.json'
        original = response.read_bytes()
        response.chmod(0o600); response.write_bytes(b'{}'); response.chmod(0o444)
        with self.assertRaisesRegex(ValueError, 'tampered'):
            self.store.resolve(saved['id'])
        response.chmod(0o600); response.write_bytes(original); response.chmod(0o444)
        os.link(response, Path(self.temp.name) / 'response-link')
        with self.assertRaises(ValueError):
            self.store.resolve(saved['id'])

    def test_failure_cli_has_nonzero_exit_and_diagnostic_identifier(self):
        from gflo.__main__ import main
        evidence, client, answer = self.prepared()
        config = Path(self.temp.name) / 'config.json'
        config.write_text(json.dumps({'model': 'local', 'endpoint': 'http://127.0.0.1:18000'}))
        with patch('gflo.documents.bounded_answer', return_value=self.response('{bad')), patch('sys.stderr', new_callable=io.StringIO) as output:
            code = main(['--config', str(config), 'documents', '--store', str(self.store.root), 'answer', evidence['id']])
        self.assertEqual(code, 1)
        failed = [p.name for p in self.store.root.iterdir() if p.is_dir() and p.name != evidence['id']]
        self.assertEqual(len(failed), 1)
        self.assertIn(failed[0], output.getvalue())

    def test_oversized_claim_response_is_retained_as_failure(self):
        evidence, client, answer = self.prepared()
        # A bounded transport body can still violate new claim/count capacity;
        # preserve both rejected responses instead of clipping them.
        answer['claims'] = [copy.deepcopy(answer['claims'][0]) for _ in range(16)]
        answer['claims'][0]['text'] = 'x' * 4000
        for claim in answer['claims'][1:]:
            claim['text'] = 'x' * 3950
        response = self.response(answer)
        while len(documents.encoded(response)) > 65536:
            answer['claims'][-1]['text'] = answer['claims'][-1]['text'][:-10]
            response = self.response(answer)
        with patch('gflo.documents.bounded_answer', return_value=response):
            with self.assertRaises(documents.AnswerFailure) as caught:
                self.store.answer(evidence['id'], client)
        receipt = self.store.resolve(caught.exception.identifier)['receipt']
        self.assertEqual(receipt['failure'], 'Returned response failed: invalid')
        self.assertEqual([a['validation'] for a in receipt['attempts']], ['invalid', 'invalid'])
        self.assertLessEqual((self.store.root / caught.exception.identifier / 'receipt.json').stat().st_size, 65536)

    def test_extra_and_symlink_response_files_refuse(self):
        evidence, client, answer = self.prepared()
        with patch('gflo.documents.bounded_answer', return_value=self.response(answer)):
            saved = self.store.answer(evidence['id'], client)
        root = self.store.root / saved['id']
        (root / 'response-2.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            self.store.resolve(saved['id'])
        (root / 'response-2.json').unlink()
        response = root / 'response-1.json'
        backup = Path(self.temp.name) / 'saved-response'
        response.rename(backup); response.symlink_to(backup)
        with self.assertRaises(ValueError):
            self.store.resolve(saved['id'])
