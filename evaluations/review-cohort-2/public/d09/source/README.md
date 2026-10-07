# Invoice CSV exporter

Existing action invoice_ids is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action export with invoices:list of {id:nonempty string,customer:string,items:list of {quantity:integer 0..1000,unit_cents:integer 0..1000000}}, up to 100 invoices and 100 items each. Return a CSV string with header id,customer,total and one row per invoice in input order. total is exact sum(quantity*unit_cents), expressed in decimal currency units with exactly two fractional digits and no thousands separator. Empty items total is 0.00. Use standard CSV quoting: comma separator, quote fields containing comma, double quote, carriage return or newline; embedded quotes doubled; every record terminates with CRLF, including header and final row. Do not normalize text. ids/customer <=200 code points. Empty invoices still returns header.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "export_csv", "invoices": [{"id": "a", "customer": "Ada", "items": [{"quantity": 3, "unit_cents": 105}, {"quantity": 0, "unit_cents": 1}]}]}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
