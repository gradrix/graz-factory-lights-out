import json
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_units_prototype as u
import review_evidence_prototype as e

REPO = Path(__file__).resolve().parents[1]
TRIAL = Path('/home/gradrix/repos/gflo/.gflo/executable-review-protocol-trial-1/artifact-hashes.json')
CONFIG = {'endpoint': 'http://127.0.0.1:18000', 'model': 'flash-next-coder', 'reasoning': 'medium'}


def payload():
    return {'objective': 'A1: tests pass.\n\nA2: docs exist.\n', 'objective_lines': ['A1: tests pass.', '', 'A2: docs exist.'],
            'files': {'test.py': 'bad()\n'},
            'catalog': {'commands': [{'id': 1, 'command': 'python -m unittest', 'exit_code': 0}],
                        'segments': [{'id': 1, 'command_id': 1, 'text': 'FAILED (errors=1)'}]}}


def diagnosis(decision='pass', line=1, findings=None):
    if findings is None:
        findings = [] if decision == 'pass' else [{'severity': 'major', 'source': {'path': 'test.py', 'line': 1},
                    'requirements': [line], 'observations': [1], 'inference': 'Suite fails.'}]
    return {'version': 1, 'decision': decision, 'findings': findings, 'question': ''}


class Fake:
    def __init__(self, content, reasoning_tokens=200, meter_error=None, error=None):
        self.content = content; self.reasoning_tokens = reasoning_tokens; self.meter_error = meter_error; self.error = error
        self.calls = []
    def request(self, path, body, timeout, max_response_bytes):
        self.calls.append((path, body))
        if path == '/tokenize':
            if self.meter_error: raise self.meter_error
            return {'tokens': list(range(self.reasoning_tokens))}
        if self.error: raise self.error
        return {'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': self.content,
                'reasoning_content': 'r' * self.reasoning_tokens}}], 'usage': {'completion_tokens': 1}, 'timings': {'cache_n': 0}}


class Units(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp); self.n = 0

    def unit(self, fake, line=1, text='A1: tests pass.'):
        self.n += 1
        return u.run_unit(self.tmp / 'units' / f'{self.n:02d}', payload(), line, text, CONFIG, time.monotonic() + 150, fake)

    def test_units_skip_blank_lines_and_cap(self):
        self.assertEqual(u.units(payload()), [(1, 'A1: tests pass.'), (3, 'A2: docs exist.')])
        big = payload(); big['objective'] = '\n'.join(f'R{i}' for i in range(33))
        with self.assertRaises(ValueError): u.units(big)
        empty = payload(); empty['objective'] = '\n \n'
        with self.assertRaises(ValueError): u.units(empty)

    def test_prefix_identical_across_units(self):
        a = u.prompt(payload(), 1, 'A1: tests pass.'); b = u.prompt(payload(), 3, 'A2: docs exist.')
        prefix = e.render(payload())
        self.assertTrue(a.startswith(prefix) and b.startswith(prefix)); self.assertNotEqual(a, b)

    def test_one_completion_and_metering_per_unit(self):
        fake = Fake(json.dumps(diagnosis('repair')))
        result = self.unit(fake)
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual([c[0] for c in fake.calls], ['/v1/chat/completions', '/tokenize'])
        body = fake.calls[0][1]
        self.assertEqual(body['response_format'], {'type': 'json_object'}); self.assertNotIn('tools', body)
        self.assertTrue(body['messages'][1]['content'].endswith('ASSIGNMENT: {"line":1,"text":"A1: tests pass."}'))

    def test_exhaustion_fails_closed_even_for_valid_pass(self):
        self.assertEqual(self.unit(Fake(json.dumps(diagnosis()), reasoning_tokens=1024))['status'], 'exhausted')
        self.assertEqual(self.unit(Fake('not json', reasoning_tokens=1024))['status'], 'exhausted')
        self.assertEqual(self.unit(Fake(json.dumps(diagnosis()), reasoning_tokens=1023))['status'], 'accepted')

    def test_metering_failure_and_transport_failure(self):
        self.assertEqual(self.unit(Fake(json.dumps(diagnosis()), meter_error=RuntimeError('down')))['status'], 'invalid')
        failed = self.unit(Fake('', error=TimeoutError('slow')))
        self.assertEqual(failed['status'], 'failed')
        ledger = json.loads((self.tmp / 'units' / f'{self.n:02d}' / 'ledger.json').read_bytes())
        self.assertEqual([r['status'] for r in ledger['requests']], ['failed'])

    def test_findings_must_target_assigned_line(self):
        self.assertEqual(self.unit(Fake(json.dumps(diagnosis('repair', line=3))))['status'], 'invalid')
        self.assertEqual(self.unit(Fake(json.dumps(diagnosis('repair', line=3))), 3, 'A2: docs exist.')['status'], 'accepted')

    def test_aggregation_truth_table(self):
        ok = lambda d: {'status': 'accepted', 'diagnosis': {'decision': d}}
        self.assertEqual(u.aggregate([ok('pass'), ok('pass')], 2), 'pass')
        self.assertEqual(u.aggregate([ok('pass'), ok('repair')], 2), 'repair')
        self.assertEqual(u.aggregate([ok('needs_input'), ok('pass')], 2), 'needs_input')
        self.assertEqual(u.aggregate([ok('needs_input'), ok('repair')], 2), 'repair')
        self.assertEqual(u.aggregate([ok('pass')], 2), 'incomplete')
        self.assertEqual(u.aggregate([ok('repair'), {'status': 'exhausted', 'diagnosis': {'decision': 'pass'}}], 2), 'incomplete')

    def test_reverify_rejects_tampered_summary(self):
        results = [self.unit(Fake(json.dumps(diagnosis('repair')))), self.unit(Fake(json.dumps(diagnosis())), 3, 'A2: docs exist.')]
        child = {'planned_units': 2, 'payload_sha256': e.digest(e.encoded(payload())), 'units': results, 'decision': 'repair'}
        self.assertTrue(u.reverify(child, payload()))
        self.assertFalse(u.reverify({**child, 'decision': 'pass'}, payload()))
        forged = json.loads(json.dumps(child)); forged['units'][0]['reasoning_tokens'] = 1024
        self.assertFalse(u.reverify(forged, payload()))

    def test_predecessor_calibration(self):
        # Measured on the rig with /tokenize: all four predecessor responses used exactly 1024 reasoning tokens.
        for measured in (1024, 1024, 1024, 1024):
            self.assertGreaterEqual(measured, u.REASONING_BUDGET)

    def test_real_cases_fit_unit_capacity(self):
        out = self.tmp / 'pkg'; e.prepare(REPO / 'evaluations/executable-review/manifest.json', TRIAL, out)
        for case in ('case-01', 'case-02', 'case-03', 'case-04'):
            value = json.loads((out / case / 'payload.json').read_bytes())
            planned = u.units(value); self.assertEqual(len(planned), 7)
            for line, text in planned: u.prompt(value, line, text)

    def test_controller_crash_stops_remaining_cases(self):
        from unittest import mock
        out = self.tmp / 'pkg'; e.prepare(REPO / 'evaluations/executable-review/manifest.json', TRIAL, out)
        sha = e.digest((out / 'manifest.json').read_bytes())
        args = mock.Mock(manifest=str(out / 'manifest.json'), manifest_sha256=sha, config=str(self.tmp / 'c.json'),
                         identity=str(self.tmp / 'i.json'), output=str(self.tmp / 'run'), lease=str(self.tmp / 'lease'))
        outcome = {'stop': None, 'exit_code': 1, 'client_group_absent': True, 'work_finished_before_deadline': True}
        with mock.patch.object(u, 'wait_idle', return_value=True), \
             mock.patch.object(u, 'supervise', side_effect=lambda *a, **k: dict(outcome, cleanup_deadline=time.monotonic() + 1)) as supervise:
            results = u.batch(args)
        self.assertEqual([r['status'] for r in results], ['incomplete']); self.assertEqual(supervise.call_count, 1)


if __name__ == '__main__': unittest.main()
