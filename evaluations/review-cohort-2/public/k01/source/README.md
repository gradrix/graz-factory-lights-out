# Manifest tool

Compare two file manifests (`before` and `after`) and report what changed.
Each manifest is a JSON list of at most 100 entries, where every entry has
exactly the keys `path`, `size` and `sha256`. Paths are relative, ASCII,
1–120 characters, split by `/` into nonempty segments matching
`[A-Za-z0-9_.-]+` (the segments `.` and `..` are excluded); absolute paths,
trailing or repeated slashes and backslashes are rejected. Sizes are plain
integers from 0 to 1000000 (booleans are rejected), and `sha256` must be
exactly 64 lowercase hex characters. Paths must be unique within each list.
Any violation raises `ValueError` in the library API and never mutates the
input lists, on success or on failure.

`compare` buckets shared paths first: identical size and hash are `unchanged`,
anything else is `modified` (with `before_size`/`after_size`). Paths only in
`after` are `added`, paths only in `before` are `removed`. Among those
unmatched paths only, a `(size, sha256)` signature shared by exactly one old
and one new path becomes a `renamed` `{from, to}` entry; ambiguous signatures
stay additions/removals with no greedy pairing. Shared paths never take part
in rename matching. All lists are sorted (path lists ascending, `renamed` by
`from`). `summary` reports `before_bytes`, `after_bytes` and
`delta_bytes = after - before` over all entries of each manifest.

## CLI usage

`main.py` reads one JSON document on stdin and prints only the JSON result.
On success it exits 0; on malformed JSON or an invalid action/payload it
prints exactly `{"error": "invalid input"}` and exits 2, with no traceback.
It works from any working directory and touches no files besides stdin/stdout.

Request:

```bash
echo '{"action":"compare","before":[{"path":"docs/a.txt","size":12,"sha256":"0000000000000000000000000000000000000000000000000000000000000000"},{"path":"old/name","size":7,"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}],"after":[{"path":"docs/a.txt","size":12,"sha256":"0000000000000000000000000000000000000000000000000000000000000000"},{"path":"new/name","size":7,"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]}' | python main.py
```

Response (exit code 0):

```json
{"added": [], "modified": [], "removed": [], "renamed": [{"from": "old/name", "to": "new/name"}], "summary": {"after_bytes": 19, "before_bytes": 19, "delta_bytes": 0}, "unchanged": ["docs/a.txt"]}
```

Ping is still supported:

```bash
echo '{"action":"ping"}' | python main.py   # -> {"ok": true}
echo 'not json' | python main.py            # -> {"error": "invalid input"}, exit code 2
```

## Running the tests (offline, stdlib only)

From the project root:

```bash
python -m unittest discover -s .
# equivalently: python -m unittest discover -s /path/to/project
```
