# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: read. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action update with records (object of id -> {version: nonnegative integer,data:object}), id (string), expected (null or nonnegative integer) and patch (JSON object). Return {applied:bool, records:new independent object, record:current/new independent record-or-null}. If id is absent and expected is null, create version 1 and data equal to patch. If id exists and expected equals its version, shallow-merge patch keys into data and increment version by one. Otherwise return applied false and unchanged records/current record; expected=null means create-only, never unconditional overwrite. Patch null values are stored, not deleted. All returned nested containers must be independent of input and record must be independent of returned records too. Preserve read, including missing id -> null and independent returned data. No storage, concurrency primitives or retries are required: this models one compare-and-set transaction.

Example:

```sh
printf '%s\n' '{"action": "update", "records": {"r1": {"version": 1, "data": {"a": 1}}}, "id": "r1", "expected": 1, "patch": {"b": 2}}' | python cli.py
```

Output:

```json
{"applied": true, "records": {"r1": {"version": 2, "data": {"a": 1, "b": 2}}}, "record": {"version": 2, "data": {"a": 1, "b": 2}}}
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
