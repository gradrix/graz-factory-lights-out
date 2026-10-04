# Bounded document references: successor option

2026-10-04. **Read-only option analysis, not a chosen contract, implementation or acceptance.** Unit07's exact-excerpt trial remains unaccepted: coordinator reports8published answers,2citation failures and13calls, including ASCII `won't` versus source U+2019 in both gather attempts. The shield failure is not diagnosed by this document. No source/test changes, experiments or model calls were made for this analysis.

## Smallest supported direction

Use **references to bounded whole source spans first**. The controller supplies deterministic IDs and restores exact excerpts from immutable evidence; the model writes claims and selects IDs, never retypes quotations. Keep the existing public canonical answer/citation schema and its provenance validator.

Coordinator measurements put the largest actual span's canonical ASCII-escaped JSON size at838bytes for asyncio,1117 forCSV and488 forJSON. A2048-byte encoded excerpt ceiling covers these sources. Segmentation is therefore unnecessary for the next trial. The [prior prototype assessment](document-citation-prototype/qa.md) still applies: whole-span references can eliminate a copying error without establishing entailment, and unrestricted reference expansion is unsafe.

Example model-facing form:

```json
{"status":"supported","claims":[{"text":"Claim about the source.","references":["s0061","s0044"]}],"reason":""}
```

For a single evidence record, ID `s0001` means stored span1, with strict ASCII syntax and range1–2048. The full immutable evidence ID and a catalog hash bind that namespace in the request/receipt. The controller materializes each selected ID as the existing `{evidence_id, span, excerpt}` citation, where `excerpt` is the **entire unchanged stored span**. No Unicode normalization, quote repair, fuzzy matching, truncation, model-supplied excerpt or filesystem interpretation of an ID occurs.

## Proposed explicit limits

Count bytes using the existing canonical serializer (`ensure_ascii=True`, compact separators, deterministic keys); encoded string limits include their JSON quotation marks and escapes.

| Item | Proposed limit / rule |
| --- | --- |
| One excerpt | Whole stored span;≤4096UTF8bytes under existing validation **and≤2048bytes for its canonical encoded JSON string**. Both checks before selection/materialization. |
| Claims | At most8; each nonempty claim text≤1024encoded-string bytes, also within the existing4096UTF8byte limit. |
| References per claim |1–4; distinct IDs within that claim. |
| Total reference occurrences | At most16 across the answer. Repeated citation of one span in several claims consumes one occurrence each time. Do not budget unique references and then expand duplicates for free. |
| Insufficient-evidence reason | Nonempty,≤2048encoded-string bytes, within existing4096UTF8bytes; zero claims/references. Capacity ambiguity is handled below. |
| Materialized canonical answer |≤48KiB encoded, enforced before publication; unchanged existing citation validator runs afterward. |
| Receipt metadata excluding answer |≤12KiB encoded; fixed schema and bounded diagnostics. |
| Complete receipt | Existing≤64KiB final serialized bound remains authoritative. |
| Raw attempts / record | Existing≤2 response files,≤64KiB each;≤192KiB total record; fixed filenames only. Existing child transport may conservatively admit slightly less than a64KiB response due to its envelope. |
| Inference/lifetime | Same local model/profile,2048output/512thinking, at most one structural repair,120s per call and260s total, unchanged authority/cancellation/owner cleanup. No new fallback call. |

The expansion is bounded **before building the answer**:≤16×2048bytes of excerpt strings,≤8×1024bytes of claim strings, and less than roughly3KiB of fixed citation/claim structure gives less than44KiB. A64-character evidence hash and at most4decimal span digits bound citation overhead.48KiB leaves margin; the explicit serializer check remains required rather than relying only on this calculation.48KiB answer plus12KiB metadata also leaves margin below64KiB. The prototype's128-reference/approximately538KiB result is refused by occurrence count before expansion.

This deliberately tightens new-format claim/reference capacity while preserving old readers. An answer needing more room fails honestly; do not split it into unbounded records, silently drop claims, enlarge the receipt or relabel capacity failure as source insufficiency.

## Long spans and repair behavior

Keep all original source spans available as untrusted context, with deterministic IDs and explicit citable/ineligible metadata. The source record is unchanged. **An overlimit selected span is a structural capacity error**, even when its ID exists. The controller does not trim it to a convenient sentence or let the model provide replacement quote bytes. At most one repair may choose different eligible spans that genuinely support the same requested facts; the entire revised answer receives semantic review.

If the necessary support exists only in an ineligible long span, the result is a **non-success citation-capacity diagnostic**, not a semantic `insufficient_evidence` success. The validator cannot infer which span is semantically necessary. To enforce this distinction without inventing a relevance classifier, the conservative option is: when any spans are ineligible, an `insufficient_evidence` response is saved as `citation_capacity_unresolved` rather than promoted as successful abstention. This can refuse a genuinely unsupported question on a source containing an unrelated long span; that explicit tradeoff is preferable to claiming the source lacks evidence the protocol cannot cite. A selected-overlimit first attempt followed by abstention likewise remains a failed capacity outcome.

The current three sources have no ineligible spans under the proposed2048-byte encoded ceiling, so that conservative rule does not affect this cohort. A later measured case requiring a long span should trigger a separately versioned deterministic segmentation design. Such a design would preserve code-point boundaries, exact contiguous substrings, fixed offsets/IDs and occurrence budgets; it must not silently change the meaning of current `sNNNN` IDs. It is deferred here.

## Versioning and immutable replay

Introduce a distinct **answer format3 / citation protocol `span-ref-v1`**, while evidence records retain their existing format and identity. Do not repurpose format2. Its reader currently reconstructs request hashes through the exact base/repair prompt builders: editing those builders in place invalidates already published format2 successes **and failures**. Preserve the exact format2 prompt/profile/repair reconstruction and dispatch new requests/readers by protocol version. Format1 remains unchanged.

Format3 receipt binds evidence ID/text identity, catalog hash, protocol/materializer version, fixed limits/profile, question, attempt request hashes, complete returned-response hashes/sizes, validation history and the canonical materialized answer or failed diagnostic. The catalog is derived deterministically from stored spans; it need not become another stored response-sized file. Its hash covers each ID, exact text and eligibility/bounds metadata. A future catalog/prompt/materializer change requires compatible versioned dispatch.

On resolve/replay: verify record/file integrity, reconstruct the exact versioned catalog/request, reparse the raw reference response, validate all counts/IDs/byte budgets, materialize from frozen source, and compare the canonical result with the saved answer. Do not trust a saved canonical answer independently of the selected references. Failure records remain inspectable and unreplayable as cited answers. All rendering/failure-ID preparation and validation precede the final cancellation fence and atomic rename; no fallible filesystem work follows commit.

## Qualification before any promotion

- Show exact source curly apostrophes/non-ASCII text emerge byte-for-byte despite no model quote field. Unknown/cross-evidence IDs, user-supplied quote fields and malformed reference types must fail.
- Pair2048/+1 encoded excerpt and4096/+1UTF8 controls;8/+1 claims,4/+1 references per claim and16/+1 total occurrences. Include repeated IDs across claims and the prior128-reference expansion case. Refuse before expansion; never truncate.
- Preserve long-only support as a capacity failure, including repair-to-abstention; a small eligible-span positive still succeeds when unrelated long context exists.
- Check48KiB answer,12KiB metadata and64KiB receipt boundaries with escaped Unicode, not just ASCII character counts. Retain bounded raw attempts on ordinary terminal failure.
- Replay actual format1 and format2 successful, insufficient and failed ledgers offline with unchanged bytes/request hashes; format3 replay must use neither model nor extraction/network.
- Reuse the existing cancellation, owner-death, deadline, prior-good, tamper and final-publication gates for changed seams. Independently assess every final claim and selected excerpt: an authentic unrelated reference still passes provenance and can fail semantics.

This option targets deterministic quote copying and bounded expansion. It does not resolve the as-yet undiagnosed shield failure or establish that the model will choose supporting spans. The coordinator must freeze a successor contract and candidate before implementation or another qualification trial; failed exact-excerpt attempts remain visible historical evidence.
