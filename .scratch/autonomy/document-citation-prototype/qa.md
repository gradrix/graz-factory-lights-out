# Independent semantic QA — private citation prototype

**Recommendation: retain exact excerpts plus at most one structural repair for the next bounded implementation; keep span references as a promising experiment until long-span handling is designed.** This four-case trial supports reducing copying failures, not general semantic superiority or promotion. No model calls or maintained mutations were made by this reviewer.

Bound to contract SHA256 `03f51ebe72780e13df4435f50f5306ea3736d5e797f4c5ca4a1ff7b66206adf8`, accepted source2049361, frozen prototype SHA256 `464f11deac0733a390243e69df5bada927fa9fe292b5ae2305821d64b013a9ee`. Verified every contract input hash, all nine raw responses against saved content, request profiles, every structural result/rejection, and final answers against complete saved CSV/JSON spans. [Offline verifier](qa/verify.py), [evidence](qa/verification.json), [log](qa/verify.log). Full original attempts remain `.gflo/document-citation-prototype/results`; no evidence was rewritten.

## Semantic results

| Case | Exact plus one repair | References with controller excerpt |
|---|---|---|
| row_shape | All three frozen expected facts supported. First attempt rejected ASCII `isn't` versus source curly apostrophe; second repairs that quote. Extra QUOTE_NOTNULL capability follows span111, but **“added in3.12” is not supported by its citation111**; source113 supplies the missing version fact. Structurally valid final answer is citation-incomplete. | All three frozen expected facts supported by61/44, exact whole spans. No extras. See question ambiguity below. |
| header_selection | All three facts supported by60: omitted names consume first row, explicit names retain it, order preserved. No extras. | Same three facts and support; whole span60 repeated three times. No extras. |
| skipkeys | Both requested facts supported by67/166: default False raises TypeError; True skips unsupported-key items. No extras. | Same facts/support. No extras. |
| unpublished_future_csv | Correct insufficient_evidence; no claims/date/change invented. Reason accurately limits itself to supplied historical3.12 evidence. | Same correct insufficiency and historical boundary. |

The QUOTE_NOTNULL writer distinction is justified: non-None empty string is quoted, None is unquoted. Source119's3.12 reader bug does not contradict that **writer-only** statement. Neither exact attempt claims successful automatic reader round-trip, so omission of the reader caveat is not itself a defect. The extra version fact is present elsewhere in the frozen source, so this is missing citation support, not an invented fact. Repair changed only the apostrophe and “meaning”→“so”; it did not remove or fix this citation gap.

### Frozen oracle scope ambiguity

The row_shape question asks how DictReader behaves “by default” and then whether csv.writer **can preserve** the distinction. Its expected list tests only default loss. The references answer truthfully qualifies its answer “By default,” satisfying the frozen expected facts, but does not settle the broader configurable-capability reading. Exact does discuss that capability. Therefore report **both methods4/4 frozen expected-fact/status coverage**, exact final3/4 fully citation-supported answers, references4/4 citation-supported answers, while retaining this unresolved literal-question scope. Do not turn the latter score into4/4 unqualified question completeness or silently rewrite the frozen oracle. A future fixture should explicitly ask default behavior versus configurable writer capability.

## Mechanism and bounds

Exact:3/4 first-call valid,4/4 after one repair;5 calls,161.257s total. References:4/4 first-call valid;4 calls,129.189s. All nine saved requests used model flash-next-coder, temperature0, medium reasoning,512thinking tokens,2048completion cap. Profile and response bounds are shared; ordering alternates, cache hits differ, and these are single deterministic trials. No statistical accuracy or speed claim follows.

Whole-span citations increase excerpt bytes: row_shape1401 vs684, header1101 vs325, skipkeys680 vs459. These counts sum final citation excerpts, including repeated spans; they are not full answer sizes. Actual maximum source spans are CSV1109bytes and JSON457bytes, far below4096, so this cohort did not exercise the production limit.

Offline discriminator: replacing one synthetic span with4097ASCII bytes makes reference enrichment fail accepted validation; a one-character exact substring from the same span passes. No truncation is justified: it could remove the supporting clause. Span splitting or offset selection would require a separately specified immutable addressing/validation design. Also, a deliberately false future-date claim with a valid original citation passes structural validation, directly demonstrating that both methods prove provenance rather than entailment.

## Decision boundary

A single bounded structural repair is a proportional response to the observed apostrophe failure, provided the original failure and complete revised answer remain visible and the repaired answer receives fresh semantic review. It does not certify the revised claims. Whole-span references are worth further testing because they eliminate model quote copying, but are not a drop-in replacement under the current4096-byte excerpt cap and can cite broader irrelevant text. Any later promotion needs a defined long-span policy and disambiguated capability/version cases; no further live calls are needed to interpret this experiment honestly.
