"""Receipt capacity checks and the format3 response envelope policy."""
import json
import unittest

from gflo import documents
from gflo import document_references as refs


class ReferenceReceiptAndResponseTests(unittest.TestCase):
    @staticmethod
    def evidence(spans=None):
        return {'id': 'c' * 64,
                'spans': ['First span.', 'Second span.'] if spans is None else spans,
                'receipt': {'approval': {'source_version': 'Historical test version'},
                            'retrieved_utc': '2026-01-01T00:00:00+00:00'}}

    def test_receipt_metadata_bound_is_measured_without_the_answer(self):
        padding = 'x' * (refs.LIMITS['metadata_bytes'] - 14)
        self.assertEqual(len(documents.encoded({'padding': padding})),
                         refs.LIMITS['metadata_bytes'])
        refs.check_receipt_bounds({'padding': padding})
        with self.assertRaisesRegex(ValueError, 'metadata capacity exceeded'):
            refs.check_receipt_bounds({'padding': padding + 'x'})
        # The canonical answer is bounded separately, so an oversized answer must not
        # be counted as metadata and an oversized metadata must not hide behind it.
        refs.check_receipt_bounds({'padding': padding, 'answer': {'status': 'supported'}})
        with self.assertRaisesRegex(ValueError, 'metadata capacity exceeded'):
            refs.check_receipt_bounds({'padding': padding + 'x', 'answer': {'status': 'supported'}})

    def test_receipt_answer_bound_is_measured_in_canonical_bytes(self):
        for size, expected in [(refs.LIMITS['answer_bytes'], 'pass'),
                               (refs.LIMITS['answer_bytes'] + 1, 'raise')]:
            answer = 'a' * (size - 2)
            self.assertEqual(len(documents.encoded(answer)), size)
            if expected == 'pass':
                refs.check_receipt_bounds({'answer': answer})
            else:
                with self.assertRaisesRegex(ValueError, 'answer exceeds bound'):
                    refs.check_receipt_bounds({'answer': answer})

    def test_operator_preflight_reserves_ledger_and_error_headroom(self):
        # A receipt that fits alone must fail once the two fixed ledger slots and the
        # maximal bounded errors are reserved for.
        fits = {'padding': 'x' * 2540}
        refs.check_receipt_bounds(fits)
        refs.check_receipt_bounds(fits, reserve=True)
        over = {'padding': 'x' * 2541}
        refs.check_receipt_bounds(over)
        with self.assertRaisesRegex(ValueError, 'metadata capacity exceeded'):
            refs.check_receipt_bounds(over, reserve=True)
        # Reservation must not mutate the caller's receipt.
        receipt = {'padding': 'x' * 10}
        refs.check_receipt_bounds(receipt, reserve=True)
        self.assertEqual(receipt, {'padding': 'x' * 10})

    def test_reservation_still_rejects_an_oversized_canonical_answer(self):
        over = {'answer': 'a' * (refs.LIMITS['answer_bytes'] - 1)}
        refs.check_receipt_bounds({'answer': 'a' * (refs.LIMITS['answer_bytes'] - 2)})
        with self.assertRaisesRegex(ValueError, 'answer exceeds bound'):
            refs.check_receipt_bounds(over, reserve=True)

    def test_reference_response_materializes_one_assistant_choice(self):
        evidence = self.evidence()
        answer = {'status': 'supported',
                  'claims': [{'text': 'Claim text', 'spans': [2, 1]}], 'reason': ''}
        expanded = refs.materialize(answer, evidence)
        for message in [{'content': json.dumps(answer)},
                        {'content': json.dumps(answer), 'role': 'assistant'},
                        {'content': json.dumps(answer), 'tool_calls': None,
                         'function_call': None},
                        {'content': json.dumps(answer), 'tool_calls': [],
                         'function_call': None}]:
            self.assertEqual(refs.reference_response({'choices': [{'message': message}]},
                                                     evidence),
                             ('valid', '', expanded))

    def test_reference_response_refuses_malformed_choice_envelopes(self):
        evidence = self.evidence()
        for response in [{}, {'choices': None}, {'choices': 'x'}, {'choices': {}},
                         {'choices': []}, {'choices': ['x']}, {'choices': [None]},
                         {'choices': [{'message': {'content': '{}'}},
                                      {'message': {'content': '{}'}}]}]:
            self.assertEqual(refs.reference_response(response, evidence),
                             ('response_error', 'Invalid response envelope', None))
        for message in [{}, {'content': 7}, {'content': None},
                        {'role': 'assistant'}, {'role': 'user', 'content': 'text'}]:
            self.assertEqual(refs.reference_response({'choices': [{'message': message}]},
                                                     evidence),
                             ('response_error', 'Missing assistant text', None))
        for choice in [{}, {'message': None}, {'message': 'text'}, {'content': 'text'}]:
            self.assertEqual(refs.reference_response({'choices': [choice]}, evidence),
                             ('response_error', 'Missing assistant message', None))

    def test_reference_response_grants_no_tool_authority(self):
        evidence = self.evidence()
        answer = json.dumps({'status': 'supported',
                             'claims': [{'text': 'Claim text', 'spans': [1]}], 'reason': ''})
        for message in [{'content': answer, 'tool_calls': [{'id': 'call'}]},
                        {'content': answer, 'function_call': {'name': 'lookup'}}]:
            self.assertEqual(refs.reference_response({'choices': [{'message': message}]},
                                                     evidence),
                             ('forbidden', 'Document answers have no tool authority', None))

    def test_reference_response_reports_structural_failures_as_invalid(self):
        evidence = self.evidence()
        for content in ['{bad', 'null', '"text"', '[]',
                        json.dumps({'status': 'supported', 'claims': None, 'reason': ''}),
                        json.dumps({'status': 'supported',
                                    'claims': [{'text': 'Claim text', 'spans': [99]}],
                                    'reason': ''}),
                        json.dumps({'status': 'supported',
                                    'claims': [{'text': 'Claim text', 'spans': [1],
                                               'extra': True}], 'reason': ''})]:
            validation, error, value = refs.reference_response(
                {'choices': [{'message': {'content': content}}]}, evidence)
            self.assertEqual((validation, value), ('invalid', None))
            self.assertTrue(error)
            self.assertLessEqual(len(error), 512)
        oversized_reason = 'z' * (refs.LIMITS['reason_encoded_bytes'] + 1)
        validation, error, value = refs.reference_response(
            {'choices': [{'message': {'content': json.dumps({
                'status': 'insufficient_evidence', 'claims': [],
                'reason': oversized_reason})}}]}, evidence)
        self.assertEqual((validation, value), ('invalid', None))
        self.assertIn('insufficient-evidence reason', error)

    def test_reference_response_truncates_overlong_failure_diagnostics(self):
        def watched(message):
            class WatchedSpans(list):
                def __getitem__(self, key):
                    raise ValueError(message)
            return self.evidence(WatchedSpans(['First span.']))

        diagnostic = 'd' * 600
        validation, error, value = refs.reference_response(
            {'choices': [{'message': {'content': json.dumps({
                'status': 'supported',
                'claims': [{'text': 'Claim text', 'spans': [1]}], 'reason': ''})}}]},
            watched(diagnostic))
        self.assertEqual((validation, value), ('invalid', None))
        self.assertEqual(error, diagnostic[:512])

    def test_reference_response_refuses_abstention_over_ineligible_spans(self):
        evidence = self.evidence(['x' * 2047])
        self.assertFalse(refs.catalog(evidence)[0]['selectable'])
        validation, error, value = refs.reference_response(
            {'choices': [{'message': {'content': json.dumps({
                'status': 'insufficient_evidence', 'claims': [],
                'reason': 'Cannot establish the answer from the supplied spans.'})}}]},
            evidence)
        self.assertEqual((validation, value), ('invalid', None))
        self.assertIn('capacity unresolved', error)


if __name__ == '__main__':
    unittest.main()
