# Manifest tool

Compare two file manifests (lists of `{path, size, sha256}` entries) and report
what changed between them. Input is validated strictly before anything is
compared: at most 100 entries per manifest, unique paths of 1..120 ASCII
characters whose `/`-separated segments match `[A-Za-z0-9_.-]+` (never `.`,
`..`, absolute, trailing or repeated slashes, or backslashes), `size` a strict
integer in 0..1000000 (booleans rejected), and `sha256` exactly 64 lowercase
hex characters. Invalid input raises `ValueError` in the library API and the
inputs are never mutated, on success or failure.

`domain.compare(before, after)` returns exactly `added`, `removed`,
`modified` (`{path, before_size, after_size}`), `renamed` (`{from, to}`) and
`unchanged`. Shared paths are classified first: unchanged when both `size` and
`sha256` match, otherwise modified, and they never take part in rename
matching. A rename is recognised only among paths missing from the opposite
manifest, keyed by the signature `(size, sha256)`, and only when exactly one
unmatched old path and exactly one unmatched new path share that signature;
ambiguous signatures stay as additions/removals (no greedy pairing), and the
matching is independent of input order. Path lists and `modified` sort
ascending by path, `renamed` sorts by `from`.

`report.totals(before, after)` sums every entry size of each manifest and
returns `{before_bytes, after_bytes, delta_bytes}` with `delta_bytes =
after_bytes - before_bytes`. `api.run(payload)` handles
`{"action": "ping"}` (returns `{"ok": true}`) and
`{"action": "compare", "before": [...], "after": [...]}` (domain result plus
`summary = totals(...)`); an unknown action, unknown/missing fields or a
malformed payload raise `ValueError`.

## Running the CLI

The CLI reads exactly one JSON document from standard input and writes only the
JSON result to standard output, exiting 0. Malformed JSON or an invalid
action/payload prints exactly `{"error":"invalid input"}` and exits 2, with no
traceback. It touches no files, so it works from any working directory.

```console
$ echo '{"action":"ping"}' | python3 /workspace/main.py
{"ok":true}
$ echo '{"action":"nope"}' | python3 /workspace/main.py
{"error":"invalid input"}
$ echo 2
```

Concrete request/response for a compare (one file renamed, one modified):

```console
$ python3 /workspace/main.py <<'JSON'
{"action": "compare",
 "before": [{"path": "a/x", "size": 3, "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            {"path": "keep", "size": 1, "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}],
 "after":  [{"path": "b/y", "size": 3, "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            {"path": "keep", "size": 2, "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}]}
JSON
{"added":[],"modified":[{"after_size":2,"before_size":1,"path":"keep"}],"removed":[],"renamed":[{"from":"a/x","to":"b/y"}],"summary":{"after_bytes":5,"before_bytes":4,"delta_bytes":1},"unchanged":[]}
$ echo $?
0
```

Errors behave the same way from any directory:

```console
$ cd /tmp
$ echo 'not json' | python3 /workspace/main.py
{"error":"invalid input"}
$ echo $?
2
```

## Library use

```python
from manifest_tool import api
from manifest_tool.domain import compare
from manifest_tool.report import totals

api.run({"action": "ping"})            # -> {"ok": True}
compare(before, after)                 # -> {added, removed, modified, renamed, unchanged}
totals(before, after)                  # -> {before_bytes, after_bytes, delta_bytes}
```

## Tests

Python 3.12 standard library only; no third-party dependencies and no network
access is needed. Tests live in `tests/test_manifest_tool.py` and are
discoverable from the project root:

```console
$ python -m unittest discover -s /workspace -v
```

There is no server mode; the only entry point is the stdin/stdout CLI above
(`python3 /workspace/main.py`), which is also what the tests exercise
subprocess-wise.
