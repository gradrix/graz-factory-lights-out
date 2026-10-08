# Usage

Action allocate: weights is a list of nonnegative integers, seats an integer 0..1000. Allocate seats proportionally using largest remainders: floor each exact quota, then distribute remaining seats in descending fractional remainder, breaking ties by lower index. Empty weights returns [] only when seats=0; positive seats with zero total weight raises ValueError. Zero seats always returns one zero per weight.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "allocate", "weights": [1, 1, 1], "seats": 2}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
