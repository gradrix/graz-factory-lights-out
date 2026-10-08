# Usage

Action occurrences: start is valid ISO YYYY-MM-DD date in years 2000..2090, day integer 1..31, count integer 0..24. Return count ISO dates starting with the month containing start, on requested day or last day of month when requested day is absent; omit dates before start and continue into future months until count results. Clamp independently each month, do not let February change later desired day.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "occurrences", "start": "2024-01-31", "day": 31, "count": 3}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
