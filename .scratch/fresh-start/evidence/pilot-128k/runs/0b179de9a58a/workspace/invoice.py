"""Summarize invoice CSV amounts per customer.

Usage: python invoice.py PATH

Reads a CSV with columns ``customer,amount`` (extra columns are ignored),
rounds every amount to cents with ROUND_HALF_UP, sums per customer with
Decimal arithmetic, and prints a JSON object mapping customer names to
amount strings with exactly two decimal digits.

Exit codes: 0 success, 2 invalid input (a clear message is written to
stderr, no traceback).
"""
import csv
import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTS = Decimal('0.01')
REQUIRED_COLUMNS = ('customer', 'amount')


def _format_amount(value):
    """Render a Decimal with exactly two decimal digits (ROUND_HALF_UP)."""
    quantized = value.quantize(CENTS, rounding=ROUND_HALF_UP)
    if quantized == 0:
        quantized = abs(quantized)  # avoid rendering negative zero
    return str(quantized)


def parse_amount(raw, context='amount'):
    """Parse one CSV amount field into a finite Decimal.

    Raises ValueError with a clear, user-facing message on empty,
    non-numeric, or non-finite values.
    """
    text = raw.strip()
    if not text:
        raise ValueError('empty amount value (%s)' % context)
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ValueError('invalid amount value %r (%s)' % (raw, context))
    if not value.is_finite():
        raise ValueError('non-finite amount value %r (%s)' % (raw, context))
    return value


def summarize(stream):
    """Sum invoice amounts per customer from an open CSV text stream.

    Returns a dict mapping customer names to amount strings with exactly
    two decimal digits. A header-only CSV yields an empty dict. Raises
    ValueError with a clear message when the header is missing the
    ``customer`` or ``amount`` columns, or when a row has an empty
    customer name or an empty/invalid/non-finite amount.
    """
    reader = csv.DictReader(stream)
    if reader.fieldnames is None:
        return {}
    missing = [column for column in REQUIRED_COLUMNS
               if column not in reader.fieldnames]
    if missing:
        raise ValueError('missing required column(s): %s' % ', '.join(missing))

    totals = {}
    for row in reader:
        customer = (row['customer'] or '').strip()
        if not customer:
            raise ValueError('empty customer name in a row')
        amount = parse_amount(row['amount'], 'row for customer %r' % customer)
        amount = amount.quantize(CENTS, rounding=ROUND_HALF_UP)
        totals[customer] = totals.get(customer, Decimal('0')) + amount
    return {customer: _format_amount(total) for customer, total in totals.items()}


def main(argv):
    if len(argv) != 2:
        print('usage: python invoice.py PATH', file=sys.stderr)
        return 2
    try:
        with open(argv[1], newline='') as stream:
            totals = summarize(stream)
    except OSError as exc:
        print('error: %s' % exc, file=sys.stderr)
        return 2
    except ValueError as exc:
        print('error: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(totals, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
