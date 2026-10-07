# Support bundle redaction

Existing action root_kind is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action redact with document:any JSON value with nesting depth <=10 and <=500 values, keys:list of strings (<=50), replacement:any scalar JSON value (null, boolean, integer, string; integers magnitude <=10**12). Return a deep copy of document where every object member whose key case-insensitively matches a listed key is replaced with replacement, at any depth. Case-insensitive means Python str.casefold(), with no whitespace stripping. Arrays are traversed, scalars stay unchanged; when replacing an object member, replace its entire value without traversing it further. Preserve object keys, array order, and exact types of untouched values. No in-place mutation or aliasing of returned mutable containers to input containers. document contains null, booleans, integers, strings, lists, and string-keyed objects; no floats.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "redact", "document": {"Token": "s", "nested": [{"token": {"a": 1}, "keep": false}, true]}, "keys": ["TOKEN"], "replacement": "***"}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
