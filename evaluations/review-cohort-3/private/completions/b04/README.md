# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: keys. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action resolve with defaults (arbitrary JSON object), layers (ordered list of JSON objects) and required (list of nonempty top-level key strings). Start with defaults and merge each layer in order, later values win. When old and new values are objects, recursively merge. Arrays/scalars replace entirely. A null value in a layer deletes that key if present, including at nested depth; deletion of absent keys is a no-op. Nulls already in defaults remain unless overridden/deleted. Objects introduced where no old object exists must still apply their nested null deletions against an empty object. Return the resolved object. If any required top-level key is absent after all layers, raise ValueError; a present null/default key counts as present. Preserve action keys. Do not read environment variables or files.

Example:

```sh
printf '%s\n' '{"action": "resolve", "defaults": {"db": {"host": "localhost", "port": 5432}, "debug": false}, "layers": [{"db": {"port": null}}, {"debug": true}], "required": ["db"]}' | python cli.py
```

Output:

```json
{"db": {"host": "localhost"}, "debug": true}
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
