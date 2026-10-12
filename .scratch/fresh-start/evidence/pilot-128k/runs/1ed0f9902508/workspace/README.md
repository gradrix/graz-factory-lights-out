# Inventory

SQLite-backed inventory store (`store.py`) with a small CLI (`cli.py`).

## Usage

```
python cli.py DB ACTION SKU [QUANTITY]
```

- `python cli.py inventory.sqlite put BOOK 10` — set BOOK's stock to 10.
- `python cli.py inventory.sqlite get BOOK` — print `{"sku": "BOOK", "quantity": 10}` (`quantity` is `null` for an unknown SKU).
- `python cli.py inventory.sqlite reserve BOOK 4` — atomically reserve 4 units of BOOK; prints `{"sku": "BOOK", "reserved": true, "quantity": 6}`. On an unknown SKU or insufficient stock it prints `"reserved": false` and leaves stock unchanged (`quantity` reports the untouched stock, or `null` for an unknown SKU).

`QUANTITY` for `reserve` must be a positive integer; otherwise the CLI writes
an error to stderr and exits with status `2` (no traceback).

## API

- `store.initialize(path)` — create the `stock` table if missing.
- `store.put(path, sku, quantity)` — set stock for `sku`.
- `store.available(path, sku)` — current stock or `None`.
- `store.reserve(path, sku, quantity) -> bool` — atomically subtract `quantity` from `sku`'s stock exactly once if enough is held; returns whether the reservation succeeded. Non-positive/non-integer quantities return `False` without touching stock.

## Concurrency

`reserve` performs its check-and-subtract in a single guarded SQLite
`UPDATE` (`UPDATE stock SET quantity=quantity-? WHERE sku=? AND quantity>=?`),
which SQLite applies atomically. Concurrent processes sharing the database
can never oversell it: two reservations of 4 against stock 5 yield exactly
one success and 1 remaining.
