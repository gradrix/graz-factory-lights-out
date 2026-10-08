# Usage

Action encode: values is a list of integers; return list of [value,count] for maximal adjacent equal runs. Empty returns []. Action decode: runs is a list of two-element [integer value, integer count] lists. Each count must be positive and total decoded length <=10000, else ValueError. Adjacent same-valued runs are permitted. Return expanded list. Encode input length <=10000.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "encode", "values": [1, 1, 2, 1, 1]}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
