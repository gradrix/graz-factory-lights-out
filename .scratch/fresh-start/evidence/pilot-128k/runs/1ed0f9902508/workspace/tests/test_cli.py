"""Regression tests for the inventory CLI (put/get/reserve)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cli(*argv):
    proc = subprocess.run([sys.executable, os.path.join(ROOT, 'cli.py')] + list(argv),
                          capture_output=True, text=True)
    return proc


class TestCLI(unittest.TestCase):

    def test_cli_put_get_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            p = run_cli(db, 'put', 'BOOK', '10')
            self.assertEqual(p.returncode, 0)
            self.assertEqual(json.loads(p.stdout), {'sku': 'BOOK', 'quantity': 10})
            p = run_cli(db, 'get', 'BOOK')
            self.assertEqual(p.returncode, 0)
            self.assertEqual(json.loads(p.stdout), {'sku': 'BOOK', 'quantity': 10})

    def test_cli_reserve_success_subtracts_once(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            run_cli(db, 'put', 'BOOK', '10')
            p = run_cli(db, 'reserve', 'BOOK', '4')
            self.assertEqual(p.returncode, 0)
            self.assertEqual(json.loads(p.stdout),
                             {'sku': 'BOOK', 'reserved': True, 'quantity': 6})
            p = run_cli(db, 'get', 'BOOK')
            self.assertEqual(json.loads(p.stdout), {'sku': 'BOOK', 'quantity': 6})

    def test_cli_reserve_unknown_sku_and_insufficient_stock(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            run_cli(db, 'put', 'BOOK', '3')
            p = run_cli(db, 'reserve', 'GHOST', '1')
            self.assertEqual(p.returncode, 0)
            self.assertEqual(json.loads(p.stdout),
                             {'sku': 'GHOST', 'reserved': False, 'quantity': None})
            p = run_cli(db, 'reserve', 'BOOK', '4')
            self.assertEqual(p.returncode, 0)
            self.assertEqual(json.loads(p.stdout),
                             {'sku': 'BOOK', 'reserved': False, 'quantity': 3})
            p = run_cli(db, 'get', 'BOOK')
            self.assertEqual(json.loads(p.stdout), {'sku': 'BOOK', 'quantity': 3})

    def test_cli_reserve_invalid_quantity_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            run_cli(db, 'put', 'BOOK', '5')
            for bad in ('0', '-3', 'abc'):
                p = run_cli(db, 'reserve', 'BOOK', bad)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(p.stdout, '')
                self.assertTrue(p.stderr.strip())
                self.assertNotIn('Traceback', p.stderr)
            # missing quantity entirely is also invalid for reserve
            p = run_cli(db, 'reserve', 'BOOK')
            self.assertEqual(p.returncode, 2)
            self.assertEqual(p.stdout, '')
            self.assertTrue(p.stderr.strip())
            self.assertNotIn('Traceback', p.stderr)
            p = run_cli(db, 'get', 'BOOK')
            self.assertEqual(json.loads(p.stdout), {'sku': 'BOOK', 'quantity': 5})

    def test_cli_reserve_concurrent_processes_never_oversell(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            run_cli(db, 'put', 'BOOK', '5')
            procs = [subprocess.Popen([sys.executable, os.path.join(ROOT, 'cli.py'),
                                       db, 'reserve', 'BOOK', '4'],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True) for _ in range(2)]
            outputs = []
            for p in procs:
                out, _err = p.communicate(timeout=30)
                outputs.append(json.loads(out))
            successes = [o for o in outputs if o['reserved'] is True]
            self.assertEqual(len(successes), 1)
            p = run_cli(db, 'get', 'BOOK')
            self.assertEqual(json.loads(p.stdout), {'sku': 'BOOK', 'quantity': 1})


if __name__ == '__main__':
    unittest.main()
