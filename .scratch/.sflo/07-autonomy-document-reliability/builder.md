# Unit07 builder handoff

2026-10-04. Frozen candidate manifest: [builder-candidate.json](builder-candidate.json), SHA256 `4e1481dede629f9c83be9bbd0002d0975eccbd33820d4456ef5c75bd9eecfc2e`. Contract SHA256 `b2adcce1ceaaa777d855d570b5a354b5480bb63209aeda5c7843c13f9e135456` unchanged. Baseline0af8dbf; coordinator metadata parent at freeze681a7fc. No commit made by builder. Independent QA/security and ten-question actual-model qualification remain required.

## Delivered behavior

- Extractor `document-text-v2` changes only HTML event ceiling10000→40000. Existing body/text/depth/block/runtime/authority limits remain. Old evidence is read from stored spans, never re-extracted or rewritten.
- Exact-excerpt answer schema remains. One repair is eligible only for returned assistant text failing JSON, answer shape or exact citation validation. The failed output is JSON-encoded as untrusted data in a user message; original question/evidence/system prompt remain. Guidance asks for requested facts and discourages extras. No quote normalization or semantic-success inference.
- Transport, timeout, overflow, missing/invalid response envelope, tool/function calls and cancellation do not authorize retry. At most two calls, each capped by120seconds and the remaining absolute260-second operation deadline. Each bounded call reserves10seconds for process cleanup; caller reserves a further second before publication. Existing owner-death binding remains.
- New format2 records have receipt.json≤65536bytes and up to two fixed response files≤65536bytes each. Attempts bind contiguous numbers, reconstructed request hashes, full returned JSON hashes/lengths, shared profile and validation/error outcomes. Resolver revalidates returned content against evidence and checks canonical answer equality with the last validated response. Exact file sets, regular owned readonly single-link files, complete receipt size and SHA identity remain enforced.
- Normal terminal failures publish `kind=answer_failure`, no canonical answer, with available bounded responses and attempt metadata. `AnswerFailure(ValueError).identifier` exposes the immutable diagnostic ID; existing CLI error handling returns1 and prints it. Inspect resolves the diagnostic; replay refuses it. First-call transport failure has one attempt and zero invented response files. A successful insufficient-evidence answer remains a normal replayable answer.
- Prepublication rendering/failure exception construction, staging validation, final cancellation/deadline fence and final atomic rename preserve the publication invariant. No fallible filesystem work follows commit. Format1 replay remains supported without rewriting. Ordinary cancellation removes private staging; owner loss can leave private staging for existing explicit cleanup.

## Changed maintained paths

`gflo/documents.py`, `gflo/recipes/document_extract.py`, `docs/document-evidence.md`, `tests/test_document_repair.py`, `tests/test_document_answer_process.py`, `tests/test_document_protocol.py`, `tests/test_documents.py`.

The manifest additionally binds unchanged CLI, fetch/protocol, worker, guardian and sandbox dependencies. No browser implementation, package policy, service configuration, rig runtime, or model profile was edited. Coordinator-owned run/contract/ADR updates were not builder edits.

## Behavior-first evidence

[Initial red](builder-red.log):40000-event boundary rejected, repair failed after one call, and no exhausted-attempt diagnostic. After the first vertical slice, all three new public behaviors passed. Subsequent focused controls cover no-retry categories, preserving the first response when the second transport fails, cancellation after response and during final staging sync, immutable failure/nonzero CLI, canonical-answer/request/profile/attempt tampering, response content/hash/extra-file/link refusal, receipt overflow with a preserved valid response, old format1 replay, and the shortened child deadline. Existing owner-death and publication fault controls remain in the affected suite.

[Affected suite](builder-affected.log): **43 tests passed in1.208seconds**. The original event-limit assertion was updated to40001; the old invalid-output test now requires non-success diagnostic records instead of an empty store, matching the explicitly changed contract. It still forbids replayable answers for invalid citations/tool calls.

[Full gate](builder-coverage.log): `make coverage` **162 tests passed in139.875seconds, branch-aware total87%**, above85% gate; documents module90%. Gate included actual local browser and offline package tests. No source changes after the gate. `git diff --check` passed. No optional broader rerun.

## Actual extraction control

[builder-asyncio.json](builder-asyncio.json) records current maintained helper running through DocumentStore's actual local offline extraction executor, original pinned Python image/runc/256MiB/5second envelope. Cached official body SHA256 `b395cf62082c34beeebfdc8b7a5a34f997411f6499fa14cf66425bcd20ff1381` produced **440spans /37712UTF-8 text bytes in0.404seconds**. Complete output SHA256 `14d4153f4ce19c76b10bf2f1acbcad5c284d655c0d5b7ebcae1dfefeb1f4177e` matches the prior isolated40K experiment. This used the retained historical body, with no new fetch, rig or model call. Raw control files remain `.gflo/document-reliability-builder/`.

## Limits and reviewer seams

Controlled clients prove mechanics, not model reliability or entailment. The independent frozen ten-question cohort and actual rig offline replay remain pending. The260second deadline is enforced at call and publication boundaries, with reserved process-cleanup time; blocking host filesystem/kernel failure is not a hard-real-time guarantee. Original child owner-death behavior is retained, not replaced with a new framework.

V2 request reconstruction intentionally binds this version's exact base/repair prompt, profile, question and frozen evidence metadata. Future prompt changes must retain a reader for this receipt version rather than invalidate existing request hashes. Both attempt files store complete returned JSON objects using canonical encoding; they preserve every content character and returned field, not HTTP whitespace or transport headers. Oversized/unavailable transport output cannot be invented or stored above its cap; its failure metadata is retained. No power-loss durability guarantee or semantic acceptance is added.
