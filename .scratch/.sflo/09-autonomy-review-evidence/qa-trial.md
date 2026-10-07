# Saved-evidence finalization trial: semantics and accounting

**FAIL — 3/4 expected classifications.** Case04 is a false acceptance despite decisive captured evidence. Mechanism, integrity, lifecycle and accounting pass.

Assessor: Claude Code coordinator (resumed the Codex session after its usage limit). Independent of the local model under test, but not a separate checker context as in predecessor QA. Raw trial artifacts: `.gflo/review-evidence-c3673ba/trial-1` (54 files, [hashes](trial-artifact-hashes.json) verified after download).

## Classification and grounding

| Case | Expected | Returned | Completion tokens | Assessment |
|---|---|---|---:|---|
| case-01 | repair | repair | 1203 | Correct and grounded. Source `tests/test_manifest_tool.py:178` holds `cwd='/workspace'`; requirement line11 (A6); segments2–3 show `FileNotFoundError: '/workspace'` and `FAILED (errors=1)`. Claim that commands5/7 ran the CLI from `/tmp` and `/candidate` matches captured output. No unexecuted-test, verified-fix or portability claim. |
| case-02 | pass | pass, no findings | 1043 | Label correct; not evidence of a completed review (see below). |
| case-03 | pass | pass, no findings | 1043 | Label correct; same limitation. |
| case-04 | repair | pass, no findings | 1043 | **False acceptance.** Catalog segment5: README example run verbatim returns `{"error":"invalid input"}` exit2; segment7: README digests are 60 and 62 characters; segment9: the same request with 64-character digests succeeds. |

The predecessor's measured truth defect (unexecuted corrected-suite claim) did not recur in case01.

## Cause

Every response's `reasoning_content` ends mid-sentence: the frozen 1024-token thinking budget was exhausted on 13–18K-token prompts in all four cases. Cases02–04 then emitted the minimal 59-byte JSON `pass`. Case04 was still walking A1 validation probes when truncated and never reached README/A6 evidence. Case01 had already formed the A6 finding before truncation.

Predecessor final requests used 39–677 completion tokens because the reasoning had already happened across 4–7 exploratory turns. Removing that trajectory removed contamination and also the reasoning space; a single fresh request under the frozen profile cannot complete a whole-objective review. Passes produced after budget truncation are defaults, not review evidence.

## Accounting

4 charged requests (one per case, all `returned`, `finish_reason=stop`), 0 commands, 0 retries. 64,521 prompt + 4,332 completion = 68,853 total tokens. Request elapsed 42.193 / 61.010 / 59.422 / 77.287 s (239.912 s sum). All cases: exit0, client group absent, same-identity idle confirmed before and after, input packages verified at dispatch and completion. Prior 26 requests / 33 commands remain attributed to the predecessor.
