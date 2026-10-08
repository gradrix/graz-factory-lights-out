# Usage

Action pack: fields is a list of {width: integer 1..16, value: integer}. Concatenate unsigned values most significant field first; return {value: packed integer, bits: total width}. Reject any value below zero or >=2**width with ValueError. Empty fields returns {value:0,bits:0}. Action unpack: widths is a list of integers 1..16 and value is an integer; return the field values in order. Reject negative value or a value that cannot fit total width (including nonzero for empty widths). Total width <=128.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "pack", "fields": [{"width": 3, "value": 5}, {"width": 4, "value": 2}]}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
