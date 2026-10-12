"""Regression tests for invoice.py (run with unittest discover)."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import invoice




class TestSummarize(unittest.TestCase):
    def _summarize(self, text):
        return invoice.summarize(io.StringIO(text))

    def test_rounding_half_up_per_row(self):
        # Each row is rounded to cents with ROUND_HALF_UP before summing.
        self.assertEqual(
            self._summarize('customer,amount\nA,10.005\nA,2.5\n'),
            {'A': '12.51'})

    def test_negative_refunds(self):
        self.assertEqual(
            self._summarize('customer,amount\nA,-3.335\nB,-0.004\n'),
            {'A': '-3.34', 'B': '0.00'})

    def test_zero_amounts_render_two_decimals(self):
        self.assertEqual(
            self._summarize('customer,amount\nA,0\nB,0.001\n'),
            {'A': '0.00', 'B': '0.00'})

    def test_exact_decimal_arithmetic(self):
        # Float arithmetic would give 0.30000000000000004 style errors.
        self.assertEqual(
            self._summarize('customer,amount\nA,0.1\nA,0.2\n'),
            {'A': '0.30'})

    def test_quoted_customer_names_intact(self):
        self.assertEqual(
            self._summarize('customer,amount\n"Smith, J",100\n'),
            {'Smith, J': '100.00'})

    def test_header_only_returns_empty_dict(self):
        self.assertEqual(self._summarize('customer,amount\n'), {})

    def test_empty_input_missing_header_rejected(self):
        # No header at all: required columns cannot exist, so this is an
        # error (clear ValueError), not an empty dict.
        with self.assertRaises(ValueError) as ctx:
            self._summarize('')
        self.assertIn('missing header', str(ctx.exception))

    def test_extra_columns_ignored(self):
        self.assertEqual(
            self._summarize('customer,note,amount\nA,hi,1.234\n'),
            {'A': '1.23'})

    def test_missing_amount_column_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._summarize('customer,note\nA,hi\n')
        self.assertIn('amount', str(ctx.exception))

    def test_missing_customer_column_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._summarize('name,amount\nA,5\n')
        self.assertIn('customer', str(ctx.exception))

    def test_empty_customer_name_rejected(self):
        with self.assertRaises(ValueError):
            self._summarize('customer,amount\n ,5\n')

    def test_short_row_missing_amount_no_attributeerror(self):
        # Review regression: "customer,amount" header + bare "A" row must
        # raise a clear ValueError (not AttributeError) about the amount.
        with self.assertRaises(ValueError) as ctx:
            self._summarize('customer,amount\nA\n')
        self.assertIn('amount', str(ctx.exception))

    def test_short_row_missing_amount_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._summarize('customer,amount\nA\n')
        self.assertIn('missing amount value', str(ctx.exception))

    def test_extra_values_in_row_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._summarize('customer,amount\nA,1,oops\n')
        self.assertIn('extra column', str(ctx.exception))

    def test_quoted_customer_spaces_preserved(self):
        # Intentional leading/trailing spaces inside a quoted name survive.
        self.assertEqual(
            self._summarize('customer,amount\n" A ",10\n" A ",1\n'),
            {' A ': '11.00'})

    def test_whitespace_only_customer_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._summarize('customer,amount\n"  ",5\n')
        self.assertIn('empty customer name', str(ctx.exception))

    def test_empty_amount_rejected(self):
        with self.assertRaises(ValueError):
            self._summarize('customer,amount\nA,\n')

    def test_non_numeric_amount_rejected(self):
        with self.assertRaises(ValueError):
            self._summarize('customer,amount\nA,abc\n')

    def test_non_finite_amounts_rejected(self):
        for bad in ('NaN', 'Infinity', '-Infinity'):
            with self.assertRaises(ValueError):
                self._summarize('customer,amount\nA,%s\n' % bad)


class TestCli(unittest.TestCase):
    def test_cli_success(self):
        path = self._write('customer,amount\nA,1.005\n"Q, Q",2\n')
        result = subprocess.run(
            [sys.executable, '-I',
             os.path.join(os.path.dirname(os.path.dirname(
                 os.path.abspath(__file__))), 'invoice.py'), path],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            json.loads(result.stdout), {'A': '1.01', 'Q, Q': '2.00'})
        self.assertEqual(result.stderr, '')

    def test_cli_bad_amount_exits_2_without_traceback(self):
        path = self._write('customer,amount\nA,NaN\n')
        result = subprocess.run(
            [sys.executable, '-I', self._script(), path],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertIn('error:', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_cli_short_row_missing_amount_exits_2(self):
        path = self._write('customer,amount\nA\n')
        result = subprocess.run(
            [sys.executable, '-I', self._script(), path],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertIn('missing amount value', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertNotIn('AttributeError', result.stderr)

    def test_cli_quoted_customer_spaces_preserved(self):
        path = self._write('customer,amount\n" B ",3.335\n')
        result = subprocess.run(
            [sys.executable, '-I', self._script(), path],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {' B ': '3.34'})

    def test_cli_missing_file_exits_2(self):
        result = subprocess.run(
            [sys.executable, '-I', self._script(), '/definitely/missing.csv'],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)

    def _script(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'invoice.py')

    def _write(self, text):
        fd, path = tempfile.mkstemp(suffix='.csv')
        with os.fdopen(fd, 'w') as handle:
            handle.write(text)
        self.addCleanup(os.remove, path)
        return path


if __name__ == '__main__':
    unittest.main()
