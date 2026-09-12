import csv
import re


def summarize(stream, max_rows=1000000, max_labels=1000):
    if any(type(n) is not int or n < 1 for n in (max_rows, max_labels)):
        raise ValueError('row 1: invalid limits')
    row_number = 1
    totals = {}
    try:
        rows = csv.reader(stream, strict=True)
        if next(rows, None) != ['label', 'quantity']:
            raise ValueError('invalid header')
        row_number = 2
        for row in rows:
            if row_number-1 > max_rows or len(row) != 2:
                raise ValueError('row count or field count')
            label, quantity = row
            if '\r' in label or '\n' in label or not 1 <= len(label.strip()) <= 120:
                raise ValueError('invalid label')
            if not re.fullmatch(r'[+-]?[0-9]{1,10}', quantity):
                raise ValueError('invalid quantity')
            amount = int(quantity)
            if abs(amount) > 1000000000:
                raise ValueError('quantity magnitude')
            label = label.strip()
            totals[label] = totals.get(label, 0) + amount
            if len(totals) > max_labels:
                raise ValueError('label count')
            row_number += 1
    except (ValueError, TypeError, csv.Error, UnicodeError) as exc:
        raise ValueError(f'row {row_number}: {exc}') from exc
    return [{'label': key, 'quantity': totals[key]} for key in sorted(totals)]
