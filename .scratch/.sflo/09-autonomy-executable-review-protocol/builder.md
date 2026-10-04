# Executable-review protocol successor handoff

**Frozen source:** `c69e90f8359603b9bf6636fa02a6b0887a4ba2af38f9f481243f9c8e831530a8`, in the separate `gflo-review-protocol-prototype` worktree. Root owns commit/admission. No builder rig/model calls, candidate execution or prior-record edits. Contract `f4381c22e730f53bd5bab1af93e4794aa4c83fe0ce31c2a1a2767fc9a51a076f` governs this new experiment; previous failed trial remains unchanged.

## Implemented behavior

- The case ledger records explore/final phase,180-second exploration scheduling boundary, one-use length recovery and an independently reserved final request. All attempts retain their original shared eight-request and300-second work budget. The seventh exploration attempt cannot consume the eighth final slot; failed final transport remains charged after client reconstruction.
- Every exploratory transport/tool timeout is shortened to remaining phase time. Normal completed-operation boundaries may transition to finalization when evidence and overall time remain. Transport/lifecycle failures remain terminal. Executor cleanup continues under the overall deadline; phase expiry never bypasses cleanup.
- An exploratory no-tool response is retained as untrusted context, never parsed as the verdict. Capacity/time boundaries transition only with an attested command. One separately charged final request omits tools/tool_choice, requests JSON-object mode and uses existing strict grounded review validation. Malformed, fenced, truncated or tool-bearing final output remains incomplete; no salvage or final retry.
- Exactly one length-truncated exploratory response can produce neutral compact-command feedback. No command from that response executes, and malformed tool calls are not inserted into API history. Explicit unknown authority and non-list tool collections remain terminal, including when length-truncated. Nontruncated schema failures are terminal.
- Nontruncated over-budget proposed batches are refused atomically as before. If a valid batch crosses the time boundary between commands, only actual executed calls/results enter final history; skipped IDs have durable evidence and explicit controller feedback. No invented tool results are produced.
- Neutral instructions request finite truthful evidence and programmatic generation of repeated test data. No case-specific hints, new authority or semantic acceptance rules were added.

## Evidence and exact reuse

Behavior-first builder controls initially showed missing phase/recovery methods and an eighth exploration debit incorrectly succeeding. They now pass with separate final charging and no interpretation of exploratory fenced prose. Independent controls cover whole-batch truncation refusal, one-use recovery, authority/envelope refusal, final falsey tool collections, mid-batch phase boundaries, final reconstruction and publication cancellation.

Final combined command:

```sh
python3 -m unittest discover -s ops -p 'test_executable_review_*.py' -v
```

**62 collected,61 passed,1 skipped in1.356seconds.** The skipped test is the unchanged actual local Docker slice; its previous evidence is explicitly carried, and root will run independent actual-rig synthetic phase wiring. No redundant local Docker execution occurred. `combined-controls.txt` binds the final source. The earlier61-test gate is preserved as `combined-controls-before-envelope.txt`; the independent newly added non-list/length red evidence is retained under `security/`.

`builder-carry-forward.json` proves all32 prior runtime/helper files and eight executor/source-validation/lifecycle class/function bodies byte-identical, including CommandExecutor, input copying/validation and exact-owned cleanup. Independent security41 controls pass on the final source; independent QA13 plus builder8 are included in the combined run. `builder-candidate.json` binds all five mechanism/test/vertical-driver identities, contract, fixture manifest, controls and limits.

## Limits and remaining gates

The180-second phase boundary is a dispatch/scheduling boundary with shortened transport/tool timeouts; transport timeout is not a recovery event. The unchanged independent outer supervisor still owns the300-second case wall bound and150-second cleanup. An accepted internal status means completed structurally valid review, never independent correctness of classification.

Metadata now accurately describes unchanged model feedback truncation: at most16,384 characters after decoding the first16,384 raw combined bytes, potentially49,152 UTF-8 bytes after replacement decoding. This clarifies the existing bounded-output behavior without modifying the executor or its qualification.

Root must commit/freeze and independently execute the synthetic actual-rig vertical gate before any once-only repeated four-case model batch. Public fixture bytes/modes, original objective, order and private expected outcomes remain unchanged. This successor does not rescore the old trial, establish a reliability rate, qualify fresh cases or promote a maintained reviewer.

Final coordinator commit: `847f90e9d4fe515e6c6eada9eb200008b6441fd2`. Mechanism remains `c69e90f8359603b9bf6636fa02a6b0887a4ba2af38f9f481243f9c8e831530a8`; no edits followed final combined verification. Root owns the authoritative committed candidate binding and actual-rig admission.
