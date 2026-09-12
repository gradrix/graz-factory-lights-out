# dagorder

Topological sort of a JSON dependency graph.

## Installation

Install offline with:

```bash
pip install --no-deps --no-build-isolation --target DIR .
```

Then invoke the console entry point:

```bash
python DIR/bin/dagorder input.json
```

## CLI Usage

Run the CLI module directly:

```bash
python -m cli input.json
```

The CLI reads a UTF-8 JSON input file from the one required positional file path,
calls `core.run(text)`, and prints the JSON result followed by one newline.
Success returns 0. Invalid arguments, invalid input, or missing/unreadable files
return 2 with an explanatory message on stderr and empty stdout. `--help` returns 0.

## Python API

Use the `run` function from `core.py`:

```python
from core import run
result = run('{"a": [], "b": ["a"], "z": []}')
print(result)  # ["a", "b", "z"]
```

## Input Format

The input is a JSON object mapping node names to prerequisite lists. Names must
match ASCII `[a-z][a-z0-9_]{0,31}`. Every prerequisite must name a key, and lists
contain distinct names. An empty object yields `[]`.

## Ordering

The result returns every node exactly once in topological order, prerequisites
first. At each step the lexicographically smallest currently available node is
chosen. The result is independent of object-key order and prerequisite-list order.

## Invalid Input

Non-string input, malformed JSON, duplicate JSON object keys, non-object root,
invalid names, non-list values, non-string entries, duplicate prerequisites,
missing prerequisite keys, self-dependencies, and cycles all raise `ValueError`.

## Tests

Run the test suite with pytest:

```bash
pytest
```

The tests in `tests/test_core.py` cover valid, empty, invalid inputs, ordering,
and duplicate handling using the real `core.run`.
