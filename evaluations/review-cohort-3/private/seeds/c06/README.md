# Usage

Action check: number is a string of 0..100 ASCII decimal digits, spaces, or hyphens. Remove spaces and hyphens, return false if no digits remain; otherwise return whether its Luhn checksum is divisible by ten (rightmost digit is the check digit; double alternate digits moving left, subtract nine if result >9). Action append: number uses same syntax; require at least one digit or raise ValueError. Return normalized digits plus the unique Luhn check digit. Leading zeroes must survive.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "check", "value": "7992 7398-713"}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
