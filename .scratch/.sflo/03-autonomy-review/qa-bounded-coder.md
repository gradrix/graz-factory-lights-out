# Bounded coder slice QA — BLOCKED on quoted-value privacy

Frozen candidate `49559e96a6b936a4abb24c7e5558862d1e1ad644`, including environment preflight `4a552b6`. Reviewed worker reasoning/trajectory changes, structured observation and public JSON artifacts, resumed-owner startup reporting, and environment guard. All runs imported reconstructed pinned source.

**Confirmed defect:** assignment-like strings still expose secret suffixes after whitespace or escaped quotes. `redact_json({'summary':'password="ALPHA BETA"'})` leaves `BETA`; `token="ALPHA\\"BETA"` also leaves `BETA`. The independent probe observes the same leakage through the actual loopback artifact HTTP endpoint. A structured `password` field holding the same value is fully hidden, providing a conforming control. These are synthetic values only. Repair quoted-assignment parsing to consume complete quoted values, including escaped delimiters, while preserving outer JSON and original model context.

| Coverage | Result |
|---|---|
| Reasoning wire and recorded settings | PASS: actual local HTTP fixture checks none compatibility versus top-level 1024/4096 medium profile |
| Trace parseability and model context | PASS: structured trace parses, tested source content and returned model summary unchanged |
| Nested sensitive-key redaction / ordinary types | PASS: structured secret fields hidden, bool/int retained |
| Quoted whitespace/escaped-delimiter privacy | FAIL: suffix exposed through HTTP artifact, control fully hidden |
| Malformed/oversized artifact HTTP | PASS: both rejected with 404, no raw preview |
| Resumed-owner startup death | PASS: deterministic process regression, plus cancellation lifecycle tests |
| Prior environment guard | PASS: 3 regressions on this candidate |

Regression totals: 7 worker + 10 observation + 3 qualification tests passed. Passing regressions do not cover the newly demonstrated suffix leak. No target-model/GPU calls, rig changes, or maintained edits.

Reproduction: `python3 .scratch/.sflo/03-autonomy-review/qa-bounded-coder-probe.py` (exit 0 means both known leaks and conforming control were reproduced). Probe source/output: `qa-bounded-coder-probe.py`, `.json`, `.log`. Suite logs: `qa-bounded-worker.log`, `qa-bounded-observation.log`, `qa-bounded-environment.log`. Re-run suites through `qa_pinned.py 49559e96a6b936a4abb24c7e5558862d1e1ad644 -m unittest discover -s tests -p <test_worker.py|test_observation.py|test_qualification.py> -v`.
