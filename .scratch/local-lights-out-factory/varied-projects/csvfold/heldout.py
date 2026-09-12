import csv
import io
import random
import core

rng = random.Random(8271)
for trial in range(40):
    expected = {}
    rows = []
    for _ in range(rng.randrange(1, 45)):
        label = rng.choice(['a', 'A', 'ž', 'with,comma', 'with"quote', 'zero'])
        count = rng.randrange(-20, 21)
        rows.append([' ' + label + ' ', str(count)])
        expected[label] = expected.get(label, 0) + count
    rng.shuffle(rows)
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\r\n' if trial % 2 else '\n')
    writer.writerow(['label', 'quantity'])
    writer.writerows(rows)
    actual = core.run(stream.getvalue())
    assert actual == [dict(label=k, quantity=expected[k]) for k in sorted(expected)], (trial, actual, expected)
    assert all(type(row['quantity']) is int and set(row) == {'label', 'quantity'} for row in actual)
for label in ['a\r', '\na', 'x'*41]:
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerows([['label', 'quantity'], [label, '1']])
    try:
        core.run(stream.getvalue())
    except ValueError:
        pass
    else:
        raise AssertionError(('invalid heldout label', label))
print('heldout-ok')
