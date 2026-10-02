# Additional document research cohort QA

**Mixed extension outcome; no rescore or full-gate acceptance.** Candidate2049361 / manifest `9c01da103e9f145bfc426e4a4c3f02780b85a845594a4716d1437d36c413cb3c`. All four pre-frozen question-contract hashes verify. Original two accepted answers remain separate and unchanged.

## Independent answer assessment

| Question | Structural outcome | Semantic assessment |
|---|---|---|
| JSON nonfinite | Saved;26.575s | PASS: False raises ValueError for nonfinite floats; default emits NaN/Infinity/-Infinity. All extra claims about standards noncompliance, JavaScript compatibility and examples are directly supported by spans70/169/214–216. |
| JSON hooks | Saved;19.760s | PASS for the actual question: object_pairs_hook takes priority and receives ordered pairs. Spans89/131 support both claims. **Incomplete against the frozen expected-facts list**, which additionally demands that the return value replace the dictionary. That behavior was not asked: this is an overconstrained oracle item, not an omission from the actual question or a model defect. Preserve the original frozen comparison; any corrected rubric must be versioned separately. |
| CSV newlines | Saved;22.742s | PASS: explains quoted embedded newlines, extra carriage return on CRLF-writing systems, and CSV's own newline handling. Additional reader/writer file-opening recommendation is supported by spans39/44; central explanation is supported by192. |
| CSV row_shape | Rejected;28.155s | Exact-citation failure confirmed. Claim2/span44 quotes ASCII `isn't`; frozen source uses curly `isn’t` (U+2019). Replacing only that character would match, but no output was repaired or accepted. All other supplied citations match. |

The rejected row_shape answer's substantive default DictReader/restkey/restval/None facts are supported. Extra QUOTE_NOTNULL/QUOTE_STRINGS claims follow spans111/112/115/116, and its final claim correctly includes span119's Python3.12 reader bug/Python3.13 fix. Read together they distinguish the documented intended reader behavior from the actual3.12 bug. These extra facts do not rescue the exact-provenance failure. The validator correctly rejects; this is a model quotation error rather than fabricated source subject matter or a broken validator.

## Preserved cohort accounting

Eight additional frozen questions: **3 saved structural successes,1 invalid-citation rejection,4 unattempted because acquisition failed**. The three saved answers address their actual questions correctly. Frozen expected-fact completeness is2passes plus1overconstrained/incomplete item; do not silently count that third answer as satisfying the unchanged frozen fact list. No numerical score is rewritten here.

Both asyncio group receipts contain no attempted questions. Root's separate subsequent diagnostic reports `HTML event limit` at10,000 during extraction, not an inference or network failure. Initial receipts retain only bounded generic acquisition failure; this review does not infer a more specific original exception from them or relax the extractor limit.

## Evidence

Frozen inputs: `research-cohort/{manifest,json,csv,asyncio_groups,asyncio_timeouts}.json`. Preserved raw trial outputs and stores: `.gflo/document-research-cohort/`. Independent [verification script](qa-research-cohort/verify.py), [results](qa-research-cohort/results.json), [log](qa-research-cohort/verify.log) verify contract/evidence/answer identities and every cited span, isolating the single apostrophe discrepancy.

```sh
python3 .scratch/.sflo/05-autonomy-documents/qa-research-cohort/verify.py
```

No source/output edits, new fetches or model calls. This extension does not complete the ten-answer research gate, search/public-browser scope or full Stage4. Browser fixture work can proceed independently; ready for pinned-runtime fixture validation after builder freeze.
