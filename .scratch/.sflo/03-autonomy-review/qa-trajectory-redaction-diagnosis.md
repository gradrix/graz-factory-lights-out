# Trajectory redaction diagnosis — confirmed defect

Read-only inspection of current `gflo/worker.py:83` and `gflo/observe.py:41` shows redaction applied after JSON serialization. The redaction regex consumes JSON escape backslashes around quoted assignment values. This both breaks parseability and leaves the intended value visible.

Synthetic reproduction, containing no real secret:

```python
import json
from gflo.observe import redact
json.loads(redact(json.dumps({'text': 'token="ordinary"'})))
```

Observed: `JSONDecodeError`. The redacted string contains an unescaped quote and still contains `ordinary`. `secret="abc"` and assignment text followed by an escaped newline/quoted expression reproduce the same failure. Control `token = value` produces valid JSON with its value redacted.

Recommended repair: redact structured objects before serialization, including sensitive-key values and assignment-like text in string leaves. Preserve nonsensitive JSON types and nesting. Apply the same structured boundary to worker trajectories, observation events and execution detail metadata. Add escaped-quote/newline and sensitive-field controls; an observation-detail test should ensure the current unredacted path is also covered.

Retain original malformed traces unchanged. Historical metrics derived from these traces must disclose malformed-record counts and resulting coverage gaps, rather than claiming complete accounting. This diagnosis does not invalidate the separate environment-preflight QA and does not assess whether other secret formats are comprehensively detected. No real trajectory/secret lines were published, and no rig/runtime changes were made.
