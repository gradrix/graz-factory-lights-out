# Independent transfer fixture and prefreeze test-plan assessment

Three fresh questions frozen before inference at `.scratch/autonomy/document-reference-transfer`: contract SHA256 `f213c39e439b06beb2c5e7bbcf31a36ed16b6a1915525a58604e107dcdebcb9e`, manifest `50dedc21413e8f97b41c8cd8096d1507bc2f0830ac4c0ddeff542dd3a0404b2a`. Source bindings are exact actualtrial1 evidence IDs/body/text/file hashes; no new acquisition or model calls.

| Transfer case | Asked facts / grounding |
|---|---|
| CSV nonnumeric reader | Default strings; QUOTE_NONNUMERIC unquoted numeric→float; quoted numeric-looking fields remain strings. Source40/106. Reading-only scope. |
| JSON raw_decode suffix | Initial document can be decoded despite trailing data; tuple Python representation/index; index marks document end. Source143/144. Input explicitly starts with validJSON. |
| asyncio.wait timeout | No TimeoutError; returns(done,pending); unfinished tasks in pending; no timeout cancellation. Source244/247/248/258. Nonempty Tasks/Futures; distinct from wait_for. |

`questions.json` contains only names/source keys/questions; `oracle.json` contains expectations, precise scope and full grounding passages. `novelty.json` records hashes and question text from the original2-question trial,8-question extension,4-case reference prototype and10-question repair cohort. None asked these three target behaviors. Source pages are already exposed; this is fresh question/behavior transfer, not unseen-document or model-training novelty. All expectations are asked explicitly; do not add writer modes, leading-whitespace rules or return_when details as required facts.

## Successor contract test plan — no implementation verdict

Read contract `4e1077bd…` and ADR007. The bounded format3 design directly addresses the measured quote-copying and expansion failures without weakening source bytes. A proportional frozen-candidate review should discriminate:

- Strict reference shape: booleans/floats/zero/out-of-range and unexpected keys reject; valid endpoints pass; repeated references count toward16occurrences, not only unique IDs;4/5perclaim and8/9claims controls.
- Canonical ASCII JSON **string** sizes include quotes/escapes: exact1024/1025claim,2048/2049reason/selectedspan; multibyte/control-character tests distinguish UTF8 length from encoded expansion. Validate before expanding; do not rely solely on a final-size catch.
- Supported answer selecting one eligible span still works with an unrelated overlong source span. Selecting an overlong span rejects; insufficient_evidence with any unselectable span rejects as capacity unresolved; a fully selectable unsupported source can return valid insufficiency. Preserve source spans without clipping.
- Expanded answer/metadata/final receipt/total record byte accounting: use reachable bounded combinations; identify mathematically unreachable thresholds rather than fabricating claims of testing them through invalid inputs. Two retained responses count toward192KiB. Failed diagnostic remains bounded and cannot replay as success.
- Rehashed format/request/response/canonical/attempt-ledger tampering and unknown version reject. Preserve exact old format1/2 reconstruction, old success outputs and diagnostic error meaning; only new public answers defaultformat3.
- Existing no-authority/no-thirdcall/cancel/ownerdeath/publication/priorgood controls remain required. Reuse unaffected lifecycle evidence proportionally; probe changed ledger/expansion seams independently.

Acceptance still needs separately identified ten **repeated diagnostics** plus these three fresh transfer cases, all complete and entailed, followed by actual rig networknone replay of newformat3 and preserved actualformat1/2 successes/failures with unchanged record hashes. No promotion verdict is available before the candidate freezes and these gates run. Whole-span selection still cannot establish entailment; conservative capacity refusal is a documented limitation, not a supported negative answer.
