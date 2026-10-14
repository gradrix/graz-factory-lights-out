import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ops.benchmark import gate


def row(commit, delivered, false_accept=False, scored=True, elapsed=100):
    return {'commit': commit, 'arm': 'single', 'scored': scored, 'delivered': delivered, 'false_accept': false_accept,
            'factory_status': 'accepted' if delivered or false_accept else 'exhausted', 'elapsed_s': elapsed}


class ModelGateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.out = Path(directory.name)
        self.gates = json.loads(gate.GATES.read_text())

    def write(self, suite, found):
        (self.out / suite).mkdir(parents=True, exist_ok=True)
        (self.out / suite / 'results.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in found))

    def test_summary_counts_the_last_row_of_a_resumed_task(self):
        self.write('features', [row('a', False, scored=False), row('a', True, elapsed=300), row('b', False, True, elapsed=100)])
        found = gate.summarize(self.out)['features']
        self.assertEqual((found['delivered'], found['false_accepts'], found['of'], found['unscored']), (1, 1, 2, 0))
        self.assertEqual(found['tasks'], {'a': 'delivered', 'b': 'false accept'})
        self.assertEqual(found['median_s'], 200)

    def test_gates_pass_fail_borderline_and_incomplete(self):
        expected = {'small': 16, 'features': 6, 'tests': 3}
        summary = {'small': {'delivered': 15, 'false_accepts': 0, 'of': 16, 'unscored': 0},
                   'features': {'delivered': 3, 'false_accepts': 1, 'of': 6, 'unscored': 0},
                   'tests': {'accepted': 0, 'of': 3}}
        verdicts = {r['id']: r['verdict'] for r in gate.verdicts(summary, self.gates, expected)}
        self.assertEqual(verdicts, {'adopt': 'pass', 'features': 'borderline', 'tests': 'fail'})
        summary['features'] = {'delivered': 6, 'false_accepts': 3, 'of': 6, 'unscored': 0}
        summary['small']['of'] = 15
        verdicts = {r['id']: r['verdict'] for r in gate.verdicts(summary, self.gates, expected)}
        self.assertEqual((verdicts['adopt'], verdicts['features']), ('incomplete', 'fail'))

    def test_report_reads_the_overnight_queue_and_writes_both_files(self):
        self.write('small', [row(str(i), i < 14, i == 14) for i in range(16)])
        (self.out / 'tests' / 'queue').mkdir(parents=True)
        (self.out / 'tests' / 'queue' / 'queue.json').write_text(json.dumps(
            {'done': {'m1.py': {'status': 'accepted'}, 'm2.py': {'status': 'accepted'}, 'm3.py': {'status': 'exhausted'}}}))
        (self.out / 'model.json').write_text(json.dumps({'id': 'flash-next-coder', 'weights': ['new.gguf'], 'code': 'abc'}))
        with patch('builtins.print'):
            results = {r['id']: r['verdict'] for r in gate.report(self.out)}
        self.assertEqual(results, {'adopt': 'pass', 'features': 'incomplete', 'tests': 'pass'})
        self.assertIn('| small | 14/16 delivered, 1 false accepts (median 100 s) | 14/16 delivered, 1 false accepts |',
                      (self.out / 'report.md').read_text())
        self.assertEqual(json.loads((self.out / 'summary.json').read_text())['summary']['tests']['accepted'], 2)

    def test_an_out_directory_belongs_to_one_model(self):
        gate.claim(self.out, {'id': 'flash-next-coder', 'weights': ['old.gguf']})
        gate.claim(self.out, {'id': 'flash-next-coder', 'weights': ['old.gguf']})
        with self.assertRaises(SystemExit):
            gate.claim(self.out, {'id': 'flash-next-coder', 'weights': ['new.gguf']})


if __name__ == '__main__':
    unittest.main()
