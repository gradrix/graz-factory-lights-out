# Usage

Action parse: query is ASCII string up to 2000 characters, without a leading question mark, consisting of ampersand-separated fields. Ignore empty fields. Split each nonempty field at first =; missing = means empty value. Decode + as space and percent escapes as bytes then strict UTF-8. Percent must be followed by exactly two hex digits or raise ValueError; invalid UTF-8 raises ValueError. Return ordered list of [key,value], preserving duplicate/empty keys and values. No normalization or sorting.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "parse", "query": "a=1&a=2&empty&=x&&"}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
