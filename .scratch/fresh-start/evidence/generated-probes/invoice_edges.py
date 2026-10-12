import json
import pathlib
import subprocess
import tempfile
import unittest

class InvoiceEdges(unittest.TestCase):
    def run_csv(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'data.csv'
            path.write_text(text)
            return subprocess.run(['python', 'invoice.py', str(path)], capture_output=True, text=True)
    def test_missing_amount_is_a_clean_input_error(self):
        result = self.run_csv('customer,amount\nA\n')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn('Traceback', result.stderr)
    def test_empty_input_rejects_missing_required_header(self):
        result = self.run_csv('')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)
    def test_quoted_customer_name_is_preserved(self):
        result = self.run_csv('customer,amount\n" Acme ",1.00\n')
        self.assertEqual(json.loads(result.stdout), {' Acme ': '1.00'})

unittest.main()
