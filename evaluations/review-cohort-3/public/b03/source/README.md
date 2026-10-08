# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: attempts. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action schedule with now (integer seconds), attempt (integer >=1), base (positive integer seconds), cap (positive integer seconds), max_attempts (integer >=1), outcome ('success', 'permanent', or 'transient'), and optional retry_after (null or nonnegative integer seconds). Validate numeric bounds and outcome even when no retry would occur; invalid values raise ValueError. Return {retry: bool, at: integer-or-null, delay: integer-or-null}. Only transient outcomes with attempt < max_attempts retry. Delay = max(min(cap, base * 2**(attempt-1)), retry_after or 0). Server retry_after can exceed cap; it is relative to now. Other outcomes return false/null/null. Preserve action attempts. Use exact integer arithmetic; no random jitter or sleeping.

Example:

```sh
printf '%s\n' '{"action": "schedule", "now": 100, "attempt": 2, "base": 3, "cap": 10, "max_attempts": 5, "outcome": "transient", "retry_after": null}' | python cli.py
```

Output:

```json
{"retry": true, "at": 106, "delay": 6}
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
