# Atomic warehouse adjustments

Existing action snapshot is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

The warehouse SQLite database has exactly table stock(sku TEXT PRIMARY KEY, quantity INTEGER NOT NULL) with nonnegative quantities. Add action adjust with db: absolute path to an existing writable database and changes: list of {sku:nonempty string,delta:integer -1000..1000}, up to 100 changes. Apply changes in input order in ONE atomic transaction. A missing SKU or an intermediate quantity below zero raises ValueError and rolls back every change from that call. Repeated SKUs are allowed; apply each delta to the latest quantity. On success return all rows as [{sku,quantity},...] sorted by sku using Python string order, and persist them. Empty changes returns current rows. No new rows or schema changes. Preserve the existing action snapshot and its output. Only the named database may be changed; close resources before returning. The fixture is a local database with no concurrent clients. The baseline snapshot takes {action:"snapshot",db:path}.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "adjust", "changes": [{"sku": "a", "delta": -2}, {"sku": "b", "delta": 3}], "db": "/tmp/warehouse.db"}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
