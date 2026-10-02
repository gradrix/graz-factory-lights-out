import json
from pathlib import Path
import subprocess
import tempfile
import unittest


class InvoiceAcceptance(unittest.TestCase):
    def run_csv(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'invoices.csv'
            path.write_text(text)
            return subprocess.run(['python', 'invoice.py', str(path)], capture_output=True, text=True)

    def test_money_csv_and_refunds(self):
        result = self.run_csv('customer,amount\n"Smith, Inc",0.005\n"Smith, Inc",0.005\nOther,2.675\nOther,-0.005\nZero,0\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {'Smith, Inc': '0.02', 'Other': '2.67', 'Zero': '0.00'})

    def test_large_values_do_not_lose_cents(self):
        result = self.run_csv('customer,amount\nA,9007199254740992.01\nA,0.01\n')
        self.assertEqual(json.loads(result.stdout), {'A': '9007199254740992.02'})

    def test_empty(self):
        self.assertEqual(json.loads(self.run_csv('customer,amount\n').stdout), {})

    def test_invalid_input(self):
        for text in ('customer,amount\nA,NaN\n', 'customer,amount\nA,inf\n', 'customer,amount\nA,no\n', 'wrong,amount\nA,2\n', 'customer,amount\n,2\n', 'customer,amount\nA,\n'):
            with self.subTest(text=text):
                result = self.run_csv(text)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(result.stderr.strip())
                self.assertNotIn('Traceback', result.stderr)


unittest.main()
