# Usage

Action evaluate: coefficients is a list of integer coefficients in ascending power order, x is an integer. Return {value: polynomial at x, derivative: formal first derivative at x}. Empty polynomial is zero. Up to 30 coefficients, each and x in -100..100. Use exact integers.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "evaluate", "coefficients": [2, 3, 4], "x": 2}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
