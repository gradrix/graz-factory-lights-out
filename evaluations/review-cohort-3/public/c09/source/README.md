# Usage

Action seconds: text is string up to 100 characters. Parse one or more adjacent tokens: unsigned ASCII decimal integer immediately followed by h, m or s. Units must appear at most once and in descending order (h then m then s, omissions allowed). Values need not be below 60. Leading zeroes allowed. Empty text, whitespace, signs, unknown units, repeated/reordered units or dangling digits raise ValueError. Return exact total seconds.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "seconds", "text": "1h2m3s"}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
