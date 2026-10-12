"""Boundary and error-path checks for format3 reference answer materialization."""
import json
import unittest

from gflo import documents
from gflo import document_references as refs


class ReferenceMaterializationTests(unittest.TestCase):
    @staticmethod
    def evidence(spans=None):
        return {'id': 'b' * 64,
                'spans': ['First span.', 'Second span.'] if spans is None else spans,
                'receipt': {'approval': {'source_version': 'Historical test version'},
                            'retrieved_utc': '2026-01-01T00:00:00+00:00'}}

    @staticmethod
    def claim(text='Claim text', spans=(1,)):
        return {'text': text, 'spans': list(spans)}

    @staticmethod
    def supported(claims, reason=''):
        return {'status': 'supported', 'claims': claims, 'reason': reason}

    @staticmethod
    def abstain(reason='The supplied spans do not state the answer.'):
        return {'status': 'insufficient_evidence', 'claims': [], 'reason': reason}

    def test_materialize_expands_span_ids_into_frozen_citations(self):
        evidence = self.evidence()
        value = self.supported([self.claim('Both spans support this.', (2, 1))])
        answer = refs.materialize(value, evidence)
        self.assertEqual(answer, {
            'status': 'supported',
            'claims': [{'text': 'Both spans support this.', 'citations': [
                {'evidence_id': evidence['id'], 'span': 2, 'excerpt': 'Second span.'},
                {'evidence_id': evidence['id'], 'span': 1, 'excerpt': 'First span.'}]}],
            'reason': ''})
        self.assertEqual(documents.validate_answer(answer, evidence), answer)

    def test_materialize_rejects_unsupported_status_and_nonempty_reason(self):
        evidence = self.evidence()
        for value in [dict(self.supported([self.claim()]), reason='because'),
                      dict(self.supported([self.claim()]), status='unsupported'),
                      dict(self.supported([self.claim()]), status='supportd')]:
            with self.assertRaisesRegex(ValueError, 'claims and empty reason'):
                refs.materialize(value, evidence)

    def test_materialize_requires_one_to_eight_claims_and_one_to_four_spans(self):
        evidence = self.evidence()
        for count in (1, 8):
            value = self.supported([self.claim('Claim %d' % index, (1, 2))
                                    for index in range(count)])
            self.assertEqual(len(refs.materialize(value, evidence)['claims']), count)
        with self.assertRaisesRegex(ValueError, 'claims and empty reason'):
            refs.materialize(self.supported([self.claim('Claim %d' % index, (1,))
                                             for index in range(9)]), evidence)
        with self.assertRaisesRegex(ValueError, 'claims and empty reason'):
            refs.materialize(self.supported([]), evidence)
        with self.assertRaisesRegex(ValueError, 'bounded reference claim'):
            refs.materialize(self.supported([self.claim(spans=(1, 1, 1, 1, 1))]), evidence)

    def test_materialize_counts_repeated_occurrences_up_to_the_limit(self):
        evidence = self.evidence()
        at_limit = self.supported([self.claim('Claim %d' % index, (1, 2, 1, 2))
                                   for index in range(4)])
        self.assertEqual(sum(len(claim['citations'])
                             for claim in refs.materialize(at_limit, evidence)['claims']), 16)
        over_limit = self.supported([self.claim('Claim %d' % index, (1, 2, 1, 2))
                                     for index in range(4)] + [self.claim('Extra claim')])
        with self.assertRaisesRegex(ValueError, 'occurrence limit'):
            refs.materialize(over_limit, evidence)

    def test_materialize_bounds_claim_text_by_canonical_json_bytes(self):
        evidence = self.evidence()
        for text in ['a' * 1022, '\u20ac' * 170 + 'aa', '\U0001f600' * 85 + 'aa']:
            self.assertEqual(len(documents.encoded(text)), 1024)
            self.assertEqual(refs.materialize(self.supported([self.claim(text)]),
                                              evidence)['claims'][0]['text'], text)
            with self.assertRaisesRegex(ValueError, 'bounded reference claim'):
                refs.materialize(self.supported([self.claim(text + 'a')]), evidence)

    def test_materialize_rejects_blank_or_oversized_abstention_reason(self):
        evidence = self.evidence()
        for reason in ['a' * 2046, '\u20ac' * 341, '\x01' * 341]:
            self.assertEqual(len(documents.encoded(reason)), 2048)
            value = self.abstain(reason)
            self.assertEqual(refs.materialize(value, evidence), value)
            with self.assertRaisesRegex(ValueError, 'insufficient-evidence reason'):
                refs.materialize(dict(value, reason=reason + 'a'), evidence)
        for blank in ['', '   ', ' \n\t ']:
            with self.assertRaisesRegex(ValueError, 'insufficient-evidence reason'):
                refs.materialize(self.abstain(blank), evidence)
        with self.assertRaisesRegex(ValueError, 'insufficient-evidence reason'):
            refs.materialize({'status': 'insufficient_evidence',
                              'claims': [self.claim()], 'reason': 'cited but abstained'},
                             evidence)

    def test_materialize_refuses_abstention_when_capacity_is_unresolved(self):
        for span in ['x' * 2047, '\u20ac' * 342]:
            self.assertFalse(refs.catalog(self.evidence([span]))[0]['selectable'])
            with self.assertRaisesRegex(ValueError, 'capacity unresolved'):
                refs.materialize(self.abstain(), self.evidence([span]))
        self.assertEqual(refs.materialize(self.abstain(), self.evidence(['x' * 2046])),
                         self.abstain())

    def test_materialize_validates_every_span_id_before_expansion(self):
        def watched():
            class WatchedSpans(list):
                def __getitem__(self, key):
                    raise AssertionError('source read before every bound passed')
            return self.evidence(WatchedSpans(['First span.', 'Second span.']))

        bad = [self.supported([self.claim(spans=spans)]) for spans in
               ([0], [3], [1, 0], [True], [False], [1.0], ['1'], [None], [[]], [])]
        bad += [self.supported([{'text': 'Claim text', 'spans': [1], 'extra': True}]),
                self.supported([{'text': '   ', 'spans': [1]}]),
                self.supported([{'text': None, 'spans': [1]}]),
                self.supported([{'text': 'Claim text', 'spans': None}]),
                self.supported([self.claim()], reason='reason')]
        for value in bad:
            with self.assertRaises(ValueError):
                refs.materialize(value, watched())
        with self.assertRaisesRegex(ValueError, 'span ID'):
            refs.materialize(self.supported([self.claim(spans=(2,))]), self.evidence(['only']))
        with self.assertRaisesRegex(ValueError, 'citation capacity'):
            refs.materialize(self.supported([self.claim(spans=(1,))]), self.evidence(['x' * 2047]))

    def test_materialize_rejects_answer_shape_and_type_defects(self):
        evidence = self.evidence()
        for value in ['supported', None, 7, [],
                      {'status': 'supported', 'claims': None, 'reason': ''},
                      {'status': 'supported', 'claims': [self.claim()], 'reason': None},
                      {'status': 'supported', 'claims': [self.claim()], 'reason': '', 'extra': 1},
                      {'status': 'supported', 'claims': set('ab'), 'reason': ''},
                      {'status': 'supported', 'claims': (self.claim(),), 'reason': ''}]:
            with self.assertRaises(ValueError):
                refs.materialize(value, evidence)
        with self.assertRaisesRegex(ValueError, 'status, claims and reason'):
            refs.materialize({'status': 'supported', 'claims': [self.claim()]}, evidence)

    def test_materialize_keeps_answers_inside_the_canonical_answer_bound(self):
        evidence = self.evidence(['x' * 2046] * 4)
        largest = self.supported([self.claim('a' * 1022, (1, 2, 3, 4)) for _ in range(4)])
        answer = refs.materialize(largest, evidence)
        self.assertEqual(len(documents.encoded(answer)), 38653)
        self.assertLessEqual(len(documents.encoded(answer)), refs.LIMITS['answer_bytes'])


if __name__ == '__main__':
    unittest.main()
