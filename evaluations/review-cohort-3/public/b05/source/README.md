# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: field_names. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Actions encode(fields) and decode(line). A log line is tab-separated key=value fields. Fields is an object mapping keys matching ASCII [A-Za-z_][A-Za-z0-9_]* to string values. Encode keys in sorted order. In values escape backslash as two backslashes, TAB as backslash+t, LF as backslash+n, and CR as backslash+r; do not escape other characters (including equals or Unicode). Decode splits on literal TAB, then on the FIRST equals only. Decode precisely those four backslash escapes and rejects unknown/trailing escapes. Invalid keys, duplicate keys, empty fields (including trailing TAB), or fields without equals raise ValueError. Empty line decodes to {}; empty fields encodes to empty string. Return object/string as appropriate. Preserve field_names. All argument types are valid.

Example:

```sh
printf '%s\n' '{"action": "encode", "fields": {"msg": "a\tb", "level": "info"}}' | python cli.py
```

Output:

```json
"level=info\tmsg=a\\tb"
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
