import csv, io, re

def run(text):
    if not isinstance(text, str):
        raise ValueError('text required')
    try:
        rows = list(csv.reader(io.StringIO(text, newline=''), strict=True))
    except csv.Error as exc:
        raise ValueError('invalid CSV') from exc
    if not rows or rows[0] != ['label', 'quantity']:
        raise ValueError('header')
    totals = {}
    for row in rows[1:]:
        if len(row) != 2:
            raise ValueError('fields')
        label, amount = row
        if '\r' in label or '\n' in label or not 1 <= len(label.strip()) <= 40:
            raise ValueError('label')
        if not re.fullmatch(r'[+-]?[0-9]+', amount):
            raise ValueError('quantity')
        label = label.strip()
        totals[label] = totals.get(label, 0) + int(amount)
    return [{'label': k, 'quantity': totals[k]} for k in sorted(totals)]
