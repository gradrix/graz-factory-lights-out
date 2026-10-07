import copy
import hashlib
import json
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_ensemble as r

REPO = Path(__file__).resolve().parents[1]
COHORT = REPO / 'evaluations/review-cohort-2/manifest.json'
COHORT_SHA = '06b6fc2a2ef036f5e59fae8e721ff2e2d85a1d5dad224658ab6d1cdfdd64a972'
TRIAL = Path('/home/gradrix/repos/gflo/.gflo/executable-review-protocol-trial-1')
CONFIG = {'endpoint': 'http://127.0.0.1:18000', 'model': 'flash-next-coder', 'reasoning': 'medium'}


def catalog_value():
    return {'commands': [{'id': 1, 'role': 'battery', 'command': 'tests'}, {'id': 2, 'role': 'docs', 'command': 'readme'}],
            'segments': [{'id': 1, 'command_id': 1, 'text': 'OK'}, {'id': 2, 'command_id': 2, 'text': 'ACTUAL EXIT: 2'}]}


def payload():
    found = r.statements('A1: Tests pass. README example works.\n')
    return found, r.judge_payload(found, {'README.md': 'example\n'}, catalog_value())


def unit_wire(decision='pass', ids=(2,), observations=(2,)):
    findings = [] if decision == 'pass' else [{'severity': 'major', 'source': {'path': 'README.md', 'line': 1},
                'requirements': list(ids), 'observations': list(observations), 'inference': 'Documented example fails.'}]
    return {'version': 1, 'decision': decision, 'findings': findings, 'question': ''}


def audit(bearing='unrelated'):
    return {'version': 1, 'commands': [{'id': 1, 'bearing': 'unrelated', 'segments': []},
            {'id': 2, 'bearing': bearing, 'segments': [] if bearing == 'unrelated' else [2]}]}


class RoleFake:
    def __init__(self, answers, reasoning=100):
        self.answers = answers; self.reasoning = reasoning; self.roles = []
    def request(self, path, body, timeout, max_response_bytes):
        if path == '/tokenize':
            value = self.reasoning.get(self.roles[-1], 100) if isinstance(self.reasoning, dict) else self.reasoning
            if isinstance(value, list): value = value.pop(0)
            return {'tokens': [0] * value}
        text = body['messages'][1]['content'].split('ASSIGNMENT: ', 1)[1]
        role = 'audit' if text.startswith('Role: evidence auditor') else 'prosecutor' if text.startswith('Role: prosecutor') else 'judge'
        self.roles.append(role); self.last = body
        return {'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(self.answers[role]),
                'reasoning_content': 'r'}}], 'usage': {}, 'timings': {}}


class Statements(unittest.TestCase):
    def test_sentence_split_and_units(self):
        found = r.statements('A1: Tests pass. README example works; it must run.\n\nA2: (Optional) docs.\n')
        self.assertEqual([s['text'] for s in found], ['A1: Tests pass.', 'README example works; it must run.', 'A2: (Optional) docs.'])
        self.assertEqual([s['id'] for s in found], list(range(1, len(found) + 1)))
        planned = r.units(found)
        self.assertEqual(sum(len(u['ids']) for u in planned), len(found))
        self.assertTrue(all(len(u['text']) <= r.UNIT_CHARS or len(u['ids']) == 1 for u in planned))
        self.assertEqual(len({u['line'] for u in planned}), 2)

    def test_real_cohort_objectives(self):
        manifest = r.verify_cohort(COHORT, COHORT_SHA)
        for case in manifest['cases']:
            found = r.statements((COHORT.parent / case['objective']).read_text())
            planned = r.units(found)
            self.assertTrue(4 <= len(planned) <= r.MAX_UNITS, (case['id'], len(planned)))

    def test_cohort_tamper(self):
        tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, tmp)
        copy_root = tmp / 'c'; shutil.copytree(COHORT.parent, copy_root, ignore=shutil.ignore_patterns('private'))
        target = copy_root / 'public/d05/source/domain.py'; target.write_text(target.read_text() + '#')
        with self.assertRaises(ValueError): r.verify_cohort(copy_root / 'manifest.json', COHORT_SHA)


class Audit(unittest.TestCase):
    def test_complete_coverage_required(self):
        r.validate_audit(audit('contradicts'), catalog_value())
        bad = [{'version': 1, 'commands': audit()['commands'][:1]},
               {'version': 1, 'commands': audit()['commands'] + [audit()['commands'][0]]},
               {'version': 1, 'commands': [{'id': 1, 'bearing': 'supports', 'segments': [2]}, audit()['commands'][1]]},
               {'version': 1, 'commands': [{'id': 1, 'bearing': 'unrelated', 'segments': [1]}, audit()['commands'][1]]},
               {'version': 1, 'commands': [{'id': 1, 'bearing': 'supports', 'segments': []}, audit()['commands'][1]]},
               {'version': True, 'commands': audit()['commands']}, {**audit(), 'summary': 'ok'}]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError): r.validate_audit(value, catalog_value())


class Roles(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp)
        self.found, self.payload = payload(); self.unit = r.units(self.found)[0]
        self.view = r.evidence_view('A1: Tests pass. README example works.\n', self.payload['files'], self.found, self.payload['catalog'])

    def run_unit(self, fake, name='u'):
        return r.judge_unit(self.tmp / name, 1, self.unit, self.view, self.payload, CONFIG, time.monotonic() + 600, fake)

    def test_clean_unit_skips_judge(self):
        fake = RoleFake({'audit': audit(), 'prosecutor': unit_wire()})
        result = self.run_unit(fake)
        self.assertEqual((result['status'], result['decision'], fake.roles), ('accepted', 'pass', ['audit', 'prosecutor']))
        body = fake.last
        self.assertEqual((body['thinking_budget_tokens'], body['max_tokens']), (8192, 12288))
        self.assertEqual(body['response_format'], {'type': 'json_object'}); self.assertNotIn('tools', body)

    def test_contradiction_invokes_judge_with_exact_excerpts(self):
        fake = RoleFake({'audit': audit('contradicts'), 'prosecutor': unit_wire(), 'judge': unit_wire('repair')})
        result = self.run_unit(fake)
        self.assertEqual((result['decision'], result['basis'], fake.roles), ('repair', 'judge', ['audit', 'prosecutor', 'judge']))
        self.assertIn('ACTUAL EXIT: 2', fake.last['messages'][1]['content'].split('Contested: ', 1)[1])

    def test_judge_can_reject_prosecutor(self):
        fake = RoleFake({'audit': audit(), 'prosecutor': unit_wire('repair'), 'judge': unit_wire()})
        self.assertEqual(self.run_unit(fake)['decision'], 'pass')

    def test_exhaustion_or_invalid_role_is_incomplete(self):
        fake = RoleFake({'audit': audit(), 'prosecutor': unit_wire()}, reasoning={'audit': 100, 'prosecutor': [8192, 24576]})
        result = self.run_unit(fake, 'a')
        self.assertEqual((result['status'], fake.roles), ('incomplete', ['audit', 'prosecutor', 'prosecutor']))
        self.assertEqual([a['budget'] for a in result['roles']['prosecutor']['attempts']], [8192, 24576])
        self.assertEqual(fake.last['thinking_budget_tokens'], 24576)
        fake = RoleFake({'audit': {'version': 1, 'commands': []}, 'prosecutor': unit_wire()})
        result = self.run_unit(fake, 'b')
        self.assertEqual((result['status'], fake.roles), ('incomplete', ['audit']))

    def test_escalation_recovers_exhausted_role(self):
        fake = RoleFake({'audit': audit(), 'prosecutor': unit_wire()}, reasoning={'audit': [8192, 9000], 'prosecutor': 100})
        result = self.run_unit(fake)
        self.assertEqual((result['status'], result['decision'], fake.roles), ('accepted', 'pass', ['audit', 'audit', 'prosecutor']))
        self.assertEqual(result['roles']['audit']['budget'], 24576)
        self.assertTrue((self.tmp / 'u' / 'audit-escalated' / 'ledger.json').exists())
        source = self.tmp / 'src'; source.mkdir(); (source / 'README.md').write_text('example\n')
        objective = 'A1: Tests pass. README example works.\n'; planned = r.units(self.found)
        child = {'units': [result], 'planned_units': len(planned), 'decision': 'pass',
                 'view_sha256': r.digest(r.evidence_view(objective, {'README.md': 'example\n'}, self.found, self.payload['catalog']).encode())}
        self.assertTrue(r.reverify(child, self.payload['catalog'], source, objective))
        forged = copy.deepcopy(child); forged['units'][0]['roles']['audit']['budget'] = 8192
        self.assertFalse(r.reverify(forged, self.payload['catalog'], source, objective))

    def test_reverify(self):
        fake = RoleFake({'audit': audit('contradicts'), 'prosecutor': unit_wire(), 'judge': unit_wire('repair')})
        result = self.run_unit(fake)
        planned = r.units(self.found)
        source = self.tmp / 'src'; source.mkdir(); (source / 'README.md').write_text('example\n')
        objective = 'A1: Tests pass. README example works.\n'
        child = {'units': [result], 'planned_units': len(planned), 'decision': r.aggregate([result], len(planned)),
                 'view_sha256': r.digest(r.evidence_view(objective, {'README.md': 'example\n'}, self.found, self.payload['catalog']).encode())}
        self.assertTrue(r.reverify(child, self.payload['catalog'], source, objective))
        self.assertFalse(r.reverify({**child, 'decision': 'pass'}, self.payload['catalog'], source, objective))
        forged = copy.deepcopy(child); forged['units'][0]['decision'] = 'pass'; forged['decision'] = 'pass'
        self.assertFalse(r.reverify(forged, self.payload['catalog'], source, objective))
        forged = copy.deepcopy(child); forged['units'][0]['roles']['prosecutor']['reasoning_tokens'] = 8192
        self.assertFalse(r.reverify(forged, self.payload['catalog'], source, objective))

    def test_aggregate(self):
        ok = lambda d: {'status': 'accepted', 'decision': d}
        self.assertEqual(r.aggregate([ok('pass'), ok('repair')], 2), 'repair')
        self.assertEqual(r.aggregate([ok('pass')], 2), 'incomplete')
        self.assertEqual(r.aggregate([ok('pass'), {'status': 'incomplete'}], 2), 'incomplete')


class Catalog(unittest.TestCase):
    def test_real_receipts_and_bounded_head_tail(self):
        sources = []
        for case in ('case-01', 'case-04'):
            creation = json.loads((TRIAL / case / 'commands/01/creation.json').read_bytes())
            mount = next(m['Source'] for m in creation['mounts'] if m['Destination'] == '/candidate')
            sources.append(r.attested(TRIAL / case, mount))
        self.assertEqual([len(s) for s in sources], [7, 12])
        mounts = {}
        for case in ('case-01', 'case-04'):
            creation = json.loads((TRIAL / case / 'commands/01/creation.json').read_bytes())
            mounts[str(TRIAL / case)] = next(m['Source'] for m in creation['mounts'] if m['Destination'] == '/candidate')
        value = r.catalog([('tester', TRIAL / 'case-01'), ('docs', TRIAL / 'case-04')], mounts)
        self.assertEqual(len(value['commands']), 19); self.assertEqual({c['role'] for c in value['commands']}, {'tester', 'docs'})
        rows = sources[0] + sources[1]
        for command, row in zip(value['commands'], rows):
            text = ''.join(s['text'] for s in value['segments'] if s['command_id'] == command['id'])
            raw = row['text'].encode()
            if command['elided_bytes']:
                self.assertTrue(raw.startswith(text[:100].encode()))
                self.assertEqual(len(text.encode()) + command['elided_bytes'], len(raw))
            else:
                self.assertEqual(text, row['text'])

    def test_unattested_command_rejected(self):
        tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, tmp)
        root = tmp / 'case'; shutil.copytree(TRIAL / 'case-01', root, ignore=shutil.ignore_patterns('candidate'))
        ledger = json.loads((root / 'ledger.json').read_bytes()); ledger['commands'][0]['status'] = 'uncertain'
        (root / 'ledger.json').write_text(json.dumps(ledger))
        with self.assertRaises(ValueError): r.attested(root, 'x')


if __name__ == '__main__': unittest.main()
