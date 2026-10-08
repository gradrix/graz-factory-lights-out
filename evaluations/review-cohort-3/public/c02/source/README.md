# Usage

Action distance: grid is a rectangular list of strings containing only . and #, dimensions 1..30 each. start and end are [row,column] integer coordinates within grid. Return shortest orthogonal path length (edge count), or null when unreachable. Blocked start or end returns null, even if identical. Never traverse #.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "distance", "grid": ["...", "##.", "..."], "start": [0, 0], "end": [2, 0]}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
