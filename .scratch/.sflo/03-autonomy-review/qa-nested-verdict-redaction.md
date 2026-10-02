# Embedded-verdict privacy defect at 4346ba5

Candidate `4346ba5289f24f228f83f6f45646f32e41cd48c1`. Independent synthetic reproduction; D and raw artifacts unchanged.

```python
verdict = {'passed': False, 'review': {'evidence': 'token="ALPHA BETA"'}}
embedded = 'Previous attempt evidence. Repair the retained files:\n' + json.dumps(verdict)
public = redact_json({'content': embedded})
```

Expected: valid outer JSON, entire synthetic secret absent. Actual: valid JSON but `ALPHA BETA` remains. Control: passing `verdict` directly to `redact_json` hides the value. Encoding the verdict inside a string escapes the quotes; the textual assignment pattern does not recognize that representation.

Concrete worker path: `ModelWorker.__call__` constructs previous-evidence user content using `json.dumps(previous)`; `record` invokes structured redaction on the outer request. `qa-review-loop-handoff.py` proves the value survives the saved request trace, while the actual model receives the exact original previous verdict (correctly unchanged).

The exposure is not limited to private traces. A `worker.json` whose summary contains the same prefixed JSON string returns the value through the loopback `/api/runs/<id>/artifact?name=attempts/1/worker.json` endpoint. The independent HTTP probe verifies this. Ordinary structured verification/review fields carrying the unencoded assignment are a passing control; this does not establish that existing real artifacts contain secrets.

A repair can parse recognized embedded JSON into a temporary copied structure, recursively redact it, and re-encode **only the recording/display copy**. The known previous-evidence prefix provides an exact parse boundary. A generic whole-string JSON parser alone misses the prefixed form; tool argument JSON and other free-text embedded JSON require an explicit bounded policy. Do not mutate the model message or prior verdict. Alternatively extend the textual scrubber to correctly handle escaped delimiters, with direct/embedded controls and bounded depth/size. The needed guarantee is privacy of recorded/displayed evidence, not alteration of repair guidance.

Reproduce: `python3 .scratch/.sflo/03-autonomy-review/qa-nested-verdict-redaction-probe.py` (exit 0 means leak plus conforming control reproduced). Exact executable and result: `.py`/`.log` alongside this note. No real secrets, target models, GPU calls, or maintained changes.
