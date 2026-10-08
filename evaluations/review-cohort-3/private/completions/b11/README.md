# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: sources. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action ingest with watermarks (object source->nonnegative integer last accepted sequence) and events (list of {source:string,seq:positive integer,data:JSON}). Missing sources start at watermark 0. For each source, disregard incoming events with seq<=its starting watermark; group later events by (source,seq), accepting identical repeated data as duplicates but raising ValueError for conflicting data at the same source/seq. Conflicts among ignored old events do not matter. JSON equality defines data equality. For each source release only the contiguous sequence beginning at starting watermark+1; gaps retain later events in pending. Return {watermarks:new object retaining original sources and adding every new input source at least with 0, released:list,pending:list}. Both lists are sorted by (source lexicographic, seq numeric), with one object per unique source/seq. No persistent dedup memory beyond input watermarks. Preserve sources. Types/ranges are valid; do not infer timestamps or reorder by input arrival.

Example:

```sh
printf '%s\n' '{"action": "ingest", "watermarks": {"a": 1}, "events": [{"source": "a", "seq": 3, "data": "x"}, {"source": "a", "seq": 2, "data": "y"}, {"source": "b", "seq": 2, "data": "z"}]}' | python cli.py
```

Output:

```json
{"watermarks": {"a": 3, "b": 0}, "released": [{"source": "a", "seq": 2, "data": "y"}, {"source": "a", "seq": 3, "data": "x"}], "pending": [{"source": "b", "seq": 2, "data": "z"}]}
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
