# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: sizes. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action validate with entries (list of {path:string,size:integer}) and max_total (nonnegative integer). Validate an archive manifest, without reading/writing files. Paths use POSIX '/' separators: reject empty paths, leading '/', backslashes, NUL, any '..' segment and any colon anywhere. Ignore '.' and empty segments while normalizing, then require at least one remaining segment. Reject duplicate normalized paths. Also reject file/directory conflicts: no normalized path may be an ancestor of another path using whole segments (all entries describe files). Reject negative size or negative max_total. Reject total size > max_total, allowing equality. On success return {files: list of {path:normalized,size:original size} sorted lexicographically by normalized path, total:sum}. Preserve sizes. Types are valid; no symlinks or archive byte extraction are involved.

Example:

```sh
printf '%s\n' '{"action": "validate", "entries": [{"path": "./docs//b.txt", "size": 3}, {"path": "a.txt", "size": 2}], "max_total": 10}' | python cli.py
```

Output:

```json
{"files": [{"path": "a.txt", "size": 2}, {"path": "docs/b.txt", "size": 3}], "total": 5}
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
