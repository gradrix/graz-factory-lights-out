import json
import copy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import test_documents
from gflo import documents
from gflo import document_references as refs


class DocumentReferenceTests(unittest.TestCase):
    executor = test_documents.DocumentsTests.executor
    setUp = test_documents.DocumentsTests.setUp

    @staticmethod
    def selected(numbers=None, text='Supported claim'):
        return {'status': 'supported', 'claims': [{'text': text, 'spans': [1] if numbers is None else numbers}], 'reason': ''}

    @staticmethod
    def evidence(spans=None):
        return {'id': 'a' * 64, 'spans': ['Original source.'] if spans is None else spans,
                'receipt': {'approval': {'source_version': 'Historical test version'}, 'retrieved_utc': '2026-01-01T00:00:00+00:00'}}

    def test_selected_span_preserves_exact_unicode_without_model_quote(self):
        self.body = '<p>The writer won’t preserve it.</p>'.encode()
        evidence = self.store.acquire(test_documents.APPROVAL)
        client = type('Client', (), {'config': {'model': 'local'}, 'endpoint': 'http://127.0.0.1:18000'})()
        response = {'choices': [{'message': {'content': json.dumps({
            'status': 'supported', 'claims': [{'text': 'The distinction is lost.', 'spans': [1]}], 'reason': ''})}}]}
        with patch('gflo.documents.bounded_answer', return_value=response) as infer:
            saved = self.store.answer(evidence['id'], client)
        self.assertEqual(infer.call_count, 1)
        self.assertEqual(self.store.resolve(saved['id'])['receipt']['format'], 3)
        self.assertEqual(saved['answer']['claims'][0]['citations'], [
            {'evidence_id': evidence['id'], 'span': 1, 'excerpt': 'The writer won’t preserve it.'}])
        self.assertEqual(self.store.replay(saved['id'])['answer'], saved['answer'])

    def test_format2_request_and_repair_protocol_remain_frozen(self):
        request = documents.answer_request(self.evidence(), 'local', 'Question?')
        self.assertEqual(documents.digest(documents.encoded(request)),
                         '0b03fac89ebdd2cd5eac559d8ee6f56766f6901e998c07965708e75c2472316f')
        response = {'choices': [{'message': {'content': '{bad'}}]}
        repaired = documents.repair_request(request, response, 'bad JSON')
        self.assertEqual(documents.digest(documents.encoded(repaired)),
                         '51d7b46b1bbe32ad5188a84c31e97ee678e3fabfd85ef2f475e8cb332edc3c31')
        response['choices'][0]['message']['content'] = json.dumps(self.selected())
        self.assertEqual(documents.response_answer(response, self.evidence()),
                         ('invalid', 'Invalid supported claim', None))

    def test_ids_counts_and_extra_fields_fail_before_expansion(self):
        class WatchedSpans(list):
            def __getitem__(self, key):
                raise AssertionError('Expanded source before all bounds passed')
        evidence = self.evidence(WatchedSpans(['source']))
        bad = [self.selected([x]) for x in [True, False, 0, -1, 2, 1.0, '1', None]]
        bad += [self.selected([]), self.selected([1] * 5), dict(self.selected(), extra=True),
                dict(self.selected(), claims=[]), dict(self.selected(), claims=[self.selected()['claims'][0]] * 9)]
        occurrence = dict(self.selected(), claims=[self.selected([1] * 4)['claims'][0]] * 4 + [self.selected()['claims'][0]])
        bad.append(occurrence)
        old_schema = self.selected(); old_schema['claims'][0]['excerpt'] = 'invented'
        bad.append(old_schema)
        for value in bad:
            with self.subTest(value=str(value)[:70]), self.assertRaises(ValueError):
                refs.materialize(value, evidence)
        eligible = self.evidence()
        sixteen = dict(self.selected(), claims=[self.selected([1] * 4)['claims'][0]] * 4)
        result = refs.materialize(sixteen, eligible)
        self.assertEqual(sum(len(c['citations']) for c in result['claims']), 16)
        eight = dict(self.selected(), claims=[self.selected()['claims'][0]] * 8)
        self.assertEqual(len(refs.materialize(eight, eligible)['claims']), 8)

    def test_encoded_text_reason_and_selected_span_boundaries(self):
        evidence = self.evidence()
        for text in ['a' * 1022, '€' * 170 + 'aa', '\x01' * 170 + 'aa', '😀' * 85 + 'aa']:
            self.assertEqual(len(documents.encoded(text)), 1024)
            self.assertEqual(refs.materialize(self.selected(text=text), evidence)['claims'][0]['text'], text)
            with self.assertRaises(ValueError):
                refs.materialize(self.selected(text=text + 'a'), evidence)
        for reason in ['a' * 2046, '€' * 341, '\x01' * 341]:
            value = {'status': 'insufficient_evidence', 'claims': [], 'reason': reason}
            self.assertEqual(len(documents.encoded(reason)), 2048)
            self.assertEqual(refs.materialize(value, evidence), value)
            with self.assertRaises(ValueError):
                refs.materialize(dict(value, reason=reason + 'a'), evidence)
        for text in ['a' * 2046, '€' * 341, '\x01' * 341]:
            original = self.evidence([text])
            self.assertEqual(refs.materialize(self.selected(), original)['claims'][0]['citations'][0]['excerpt'], text)
            with self.assertRaisesRegex(ValueError, 'capacity'):
                refs.materialize(self.selected(), self.evidence([text + 'a']))
        for size in [4096, 4097]:
            entry = refs.catalog(self.evidence(['a' * size]))[0]
            self.assertEqual(entry['utf8_bytes'], size)
            self.assertFalse(entry['selectable'])  # Encoded2048 ceiling is already stricter for these strings.

    def test_long_span_repair_to_abstention_is_capacity_failure(self):
        self.body = ('<p>' + 'x' * 2047 + '</p><p>small fact</p>').encode()
        evidence = self.store.acquire(test_documents.APPROVAL)
        client = type('Client', (), {'config': {'model': 'local'}, 'endpoint': 'http://127.0.0.1:18000'})()
        insufficient = {'status': 'insufficient_evidence', 'claims': [], 'reason': 'Cannot establish the answer.'}
        def response(value):
            return {'choices': [{'message': {'content': json.dumps(value)}}]}
        with patch('gflo.documents.bounded_answer', side_effect=[response(self.selected()), response(insufficient)]) as infer:
            with self.assertRaises(documents.AnswerFailure) as caught:
                self.store.answer(evidence['id'], client)
        receipt = self.store.resolve(caught.exception.identifier)['receipt']
        self.assertEqual(infer.call_count, 2)
        self.assertIn('capacity unresolved', receipt['attempts'][1]['error'])
        self.assertEqual([a['validation'] for a in receipt['attempts']], ['invalid', 'invalid'])
        self.assertEqual(self.store.resolve(evidence['id'])['spans'], ['x' * 2047, 'small fact'])
        with patch('gflo.documents.bounded_answer', return_value=response(self.selected([2]))):
            saved = self.store.answer(evidence['id'], client)
        self.assertEqual(saved['answer']['claims'][0]['citations'][0]['excerpt'], 'small fact')

    def test_aggregate_capacity_checks_and_operator_preflight(self):
        maximum = dict(self.selected(), claims=[self.selected([2048, 2048], 'x' * 1022)['claims'][0]] * 8)
        expanded = refs.materialize(maximum, self.evidence(['s'] * 2047 + ['x' * 2046]))
        self.assertLess(len(documents.encoded(expanded)), 48 * 1024)
        # Pure serializer boundary; publication separately validates ledger fields.
        metadata = {'padding': ''}
        metadata['padding'] = 'x' * (12 * 1024 - len(documents.encoded(metadata)))
        refs.check_receipt_bounds(metadata)
        metadata['padding'] += 'x'
        with self.assertRaises(ValueError):
            refs.check_receipt_bounds(metadata)
        evidence = self.store.acquire(test_documents.APPROVAL)
        client = type('Client', (), {'config': {'model': 'local'}, 'endpoint': 'http://127.0.0.1:18000'})()
        before = set(self.store.root.iterdir())
        with patch('gflo.documents.bounded_answer', side_effect=AssertionError('Capacity failure inferred')):
            with self.assertRaisesRegex(ValueError, 'metadata capacity'):
                self.store.answer(evidence['id'], client, question='\x01' * 2048)
        self.assertEqual(set(self.store.root.iterdir()), before)

    def test_rehashed_catalog_canonical_and_protocol_version_tampering_refuse(self):
        evidence = self.store.acquire(test_documents.APPROVAL)
        client = type('Client', (), {'config': {'model': 'local'}, 'endpoint': 'http://127.0.0.1:18000'})()
        response = {'choices': [{'message': {'content': json.dumps(self.selected())}}]}
        with patch('gflo.documents.bounded_answer', return_value=response):
            saved = self.store.answer(evidence['id'], client)
        receipt = self.store.resolve(saved['id'])['receipt']
        changes = [lambda r: r['protocol'].update(catalog_sha256='0' * 64),
                   lambda r: r['protocol']['limits'].update(reference_occurrences=128),
                   lambda r: r['answer']['claims'][0]['citations'][0].update(excerpt='separators'),
                   lambda r: r.update(format=4), lambda r: r.update(format=True)]
        for change in changes:
            bad = copy.deepcopy(receipt); change(bad)
            stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=self.store.root))
            shutil.copy2(self.store.root / saved['id'] / 'response-1.json', stage / 'response-1.json')
            with self.assertRaises(ValueError):
                self.store._publish(stage, bad, lambda: False)
            shutil.rmtree(stage)
        self.assertEqual(self.store.replay(saved['id'])['answer'], saved['answer'])
