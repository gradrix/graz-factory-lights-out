# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: count. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action admit with history (list of integer accepted-request timestamps), now (integer), window (positive integer) and limit (nonnegative integer). history must be nondecreasing with no timestamp greater than now; violations and invalid window/limit raise ValueError. The active window is (now-window, now], excluding the left boundary. Expire old entries, admit this request iff active count < limit, append now only when admitted. Return {allowed: bool, history: new active list, retry_at: null when admitted, otherwise the earliest timestamp at which one slot becomes free (oldest active timestamp + window); for limit=0 retry_at is null}. Multiple requests at the same timestamp count separately. If active count already exceeds limit, retry_at is the timestamp when enough oldest entries expire to make count strictly less than limit. Preserve action count. No persistent clock or sleeping.

Example:

```sh
printf '%s\n' '{"action": "admit", "history": [5, 5], "now": 10, "window": 10, "limit": 2}' | python cli.py
```

Output:

```json
{"allowed": false, "history": [5, 5], "retry_at": 15}
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
