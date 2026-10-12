# Invoice summary

Run `python invoice.py PATH` to total CSV rows by customer.

## Usage

```
python invoice.py invoices.csv
```

Input CSV must have a header containing the columns `customer,amount`
(extra columns are ignored). Customer names may be quoted CSV fields and
are kept intact, including any intentional leading/trailing spaces
(e.g. `" A "` becomes the key ` A `; `"Smith, J"` becomes `Smith, J`).

## Behaviour

- Amounts are parsed with `decimal.Decimal` (no binary float rounding
  errors) and each row is rounded to cents with `ROUND_HALF_UP` before
  being summed per customer.
- Negative amounts (refunds) are supported. A total that rounds to zero
  is rendered as `0.00` (never `-0.00`).
- Output is a JSON object mapping customer names to amount strings with
  exactly two decimal digits, including zero totals (e.g. `{"A": "0.00"}`).
- A header-only CSV prints `{}`.

## Errors

Invalid input produces a clear message on stderr and exit code `2`
(no traceback):

- no header at all (empty input file), or a header missing the
  `customer` or `amount` column;
- empty or whitespace-only customer name in any row (a nonempty name
  with intentional leading/trailing spaces is preserved exactly);
- a row missing the amount column value (e.g. `customer,amount` header
  followed by a bare `A`), or extra values beyond the header columns;
- empty, non-numeric, or non-finite (`NaN`, `Infinity`) amount values;
- unreadable/missing file path.

## Tests

Regression tests live in `tests/test_invoice.py`:

```
python -m unittest discover -s tests
```
