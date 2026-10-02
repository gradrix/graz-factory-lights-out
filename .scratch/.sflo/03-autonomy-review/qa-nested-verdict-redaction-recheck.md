# Nested-verdict privacy recheck — PASS with conservative-redaction boundary

Frozen candidate `89d66ea4f925e64459a6674f92de034476deb931`. Scope: original embedded-verdict leak, raw/nested delimiter variants, actual worker recordings and loopback HTTP artifacts. No model/GPU calls or maintained edits.

**Original privacy finding is closed.** Thirty independently chosen cases cover six raw assignment forms at zero through four additional JSON encodings: double/single quotes, escaped quote, embedded newline, unfinished quote and trailing backslash. Every actual worker trace parses and hides both synthetic value fragments. Every actual HTTP artifact response hides the fragments, preserves ordinary fields and integer/boolean/null types, and parses as JSON. Worker request capture receives the exact original previous verdict; original input objects and private artifact bytes remain unchanged.

Focused regressions: **8 worker + 12 observation tests pass**, including owner-startup behavior and invalid artifact boundaries. Prior failing reproduction remains pinned to 4346ba5.

## Observed boundary

A valid raw closing quote preceded by an even backslash run is conservatively missed. Construct `text = 'token="ALPHA' + chr(92)*2 + '" ordinary=KEEP'`: `redact(text)` returns `token=[redacted]`, also removing `ordinary=KEEP`. The delimiter-depth search treats any immediately preceding backslash as disqualifying instead of recognizing escaped backslash parity. This is evidence-display loss, **not a demonstrated privacy leak**. Separate JSON fields remain intact. Retain this limitation or improve parity handling before claiming exact preservation of nonsensitive text within the same leaf; do not weaken conservative privacy handling merely to improve display.

Reproduce: `python3 .scratch/.sflo/03-autonomy-review/qa-nested-verdict-redaction-recheck-probe.py` (exit 0). Complete executable/results/log have that basename with `.py`, `.json`, `.log`. Regression evidence: `qa-nested-recheck-worker.log`, `qa-nested-recheck-observer.log`; commands use `qa_pinned.py 89d66ea4f925e64459a6674f92de034476deb931 -m unittest discover -s tests -p test_worker.py` and `test_observation.py`.
