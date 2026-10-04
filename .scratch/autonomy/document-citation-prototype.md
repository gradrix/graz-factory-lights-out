# Citation-output design experiment

2026-10-04. **Private discovery only; no maintained code, runtime, service, model profile, or original evidence changed.** [Issue07](issues/07-document-reliability.md). Browser06 qualification and acceptance remain separate.

## Recommendation

Prefer **one bounded structural repair retaining exact excerpts** for the next narrow implementation trial. This repaired the known quotation error without changing source bytes or relaxing provenance. Do not claim semantic acceptance from that repair: its extra version assertion still lacked a supporting citation. Whole-span selection is promising and performed better in these four cases, but is not ready for promotion: it cannot represent an accepted source span over4,096UTF-8 bytes and can expand a small model response beyond the64KiB receipt limit. Robustness and compatible replay matter more than the observed token reduction.

This is an implementation-direction recommendation, not acceptance of either production design. Independent semantic QA is separate. No new model calls are planned.

## Frozen comparison

[Contract](document-citation-prototype/contract.json) SHA256 `03f51ebe72780e13df4435f50f5306ea3736d5e797f4c5ca4a1ff7b66206adf8`; [script](document-citation-prototype/prototype.py) SHA256 `464f11deac0733a390243e69df5bada927fa9fe292b5ae2305821d64b013a9ee`. Both frozen before inference. Accepted document source is2049361; documents.py hash `ac39b8dab36e52561f1e08206096ca6602cf874b7b8c65af31fbcfe4dbc1a169` matches maintained source. Existing cached Python3.12 CSV/JSON snapshots were reused, without fetch or extraction. They describe a historical floating-series snapshot, not a current-version guarantee.

Each method received identical evidence/question and numerical budgets: temperature0, medium reasoning,512thinking tokens,2,048maximum output tokens per call,120-second outer deadline and65,536-byte response bound. Each could use at most one additional call **only following structural validation failure**, with the failed assistant output and validator error. No semantic retry, transport retry, source normalization, or case replacement. Alternating method order; all calls serial. Maximum allowance was two calls/240seconds of model time per case-method, plus bounded process cleanup.

Exact used accepted answer_request and validate_answer. References changed only the system citation instructions/schema: model selects evidence_id and integer span; controller validates identity/range/type, copies that complete unchanged span into excerpt, then runs the accepted validator. Both preserve raw output separately from validated/derived output. Expected facts/span review aids were never included in model requests.

[Allowlisted serving identity](document-citation-prototype/serving-identity.json): container `2cac4229053dac00fdbcadb1952db80f0a9da3fd07b8f40bce1ba8cd3114f6e0`, image `sha256:249ed60fdd67b96db472e16f945af5aaba565b20159d192ba378035b6d136a1c`, alias flash-next-coder, context98,304, parallel1, K/Vq4_0. Identity was unchanged after calls. Original private serving capture contains command arguments, including a key-file path but no inline key; it is not reproduced here. Future capture should allowlist these fields at collection time. No credential content is stored in requests/responses.

## Observations

| Frozen case | Exact calls / seconds | References calls / seconds | Semantic review |
| --- | ---: | ---: | --- |
| CSV row_shape diagnostic | 2 /51.404 | 1 /35.542 | Asked default facts correct in both. Exact adds a source-true version detail without its supporting citation. |
| DictReader omitted/provided headers and ordering | 1 /31.495 | 1 /29.028 | Both answer all three explicitly requested facts with support. |
| JSON unsupported keys, default and skipkeys=True | 1 /48.862 | 1 /37.216 | Both answer both requested behaviors with support. |
| Unsupported future CSV default-change date | 1 /29.497 | 1 /27.403 | Both correctly abstain without inventing a date. |

All8 final outputs passed structural provenance. Exact first-call provenance was3/4; references4/4. Exact's first row_shape call used ASCII `isn't` where span44 contains curly `isn’t`, reproducing the original diagnostic. Its repair used the exact curly character. Both raw responses remain intact; the controller did not fix text. The repair also slightly rephrased a claim, demonstrating that a repair is a fresh answer requiring full revalidation.

**Do not call this4/4 semantic success for exact.** Its extra QUOTE_NOTNULL claim says “added in version3.12” while citing only span111; the version fact is in uncited span113. The writer behavior/inference is supported, and the version is true in the wider source, but the cited span does not support that added detail. Under strict all-details-supported-by-citations review, exact is3/4 and references4/4. These are builder manual judgments, not automated entailment scores; [review notes](document-citation-prototype/semantic-review.json) preserve the distinction. The legacy row_shape wording asks whether writer *can* preserve a distinction, while its expected facts describe default behavior; both default answers satisfy those frozen facts. The exact answer's optional quote-mode explanation addresses that broader wording. This ambiguity limits any comparative semantic conclusion and was not silently rewritten after results.

Totals: exact161.257seconds/5calls/3,666completion tokens; references129.189seconds/4calls/2,026completion tokens. Median case-method time40.178 versus32.285seconds. These are observations, not a throughput certification or causal speed estimate: four single-trial cases, unequal realized call counts, different generated prose, alternating order, prompt-cache differences (repair reused7,810tokens) and no cold-cache reset. No request failed transport/deadline and no output hit its token ceiling.

## Bounds and backward replay

[Post-trial offline analysis](document-citation-prototype/offline-analysis.json), [reproducible probe](document-citation-prototype/offline-analysis.py), no further inference:

- Whole-span derivation accepts4,096UTF-8 bytes and rejects4,097; a multibyte4,096-byte span passes and4,098 fails. No truncation occurs. Cached CSV/JSON maximum spans are1,109/457bytes, so these four cases did not stress that limitation. Accepted extraction permits128KiB total text without a4,096-byte per-span ceiling. Exact excerpts can select a short substring within a longer span; this whole-span prototype cannot.
- A structurally legal16claims×8citations selection with4,096-byte spans produces a538,349-byte derived answer from12,397-byte reference JSON. It passes individual citation bounds but cannot fit the existing65,536-byte receipt cap. Any future path must measure the *complete encoded receipt* before publication, including source escaping, answer, model response and audit metadata; reject honestly rather than drop claims/citations or truncate.
- Observed answer sizes: exact1,889/1,091/1,270/321bytes; references2,205/1,891/1,476/283bytes. Full spans repeat surrounding text and duplicate spans across claims. Raw responses plus derived answer peaked11,889bytes for the repaired exact case, all comfortably below the receipt cap here. These are payload-component measurements, not publication tests or a worst-case bound.
- The previously saved exact answer `bf354fdec1b1c6e86af4e653f8a490270565ffdbad895f594b79136009819896` replayed through accepted code in an isolated cache copy with executor forbidden; its receipt bytes/hash remained unchanged. Three CSV-derived answers also fit the existing replay answer shape. No new answer receipt was published by this prototype. Reference selection therefore does **not inherently require migrating old answers**: derive/store the existing exact citation representation, retain original evidence/span identity, and keep old format readers. Raw-reference provenance and method/map identity still need an explicit new-record audit design.

For a later reference design, do not silently shorten long spans. The smallest honest current policy is explicit refusal for an oversized selected span/receipt; this reduces coverage versus exact substring selection. A stronger alternative needs a separate bounded-unit experiment: expose deterministic Unicode-safe contiguous ranges of the existing span, model selects a range ID, controller derives the exact substring and retains original span index plus range-map version/hash. Preserve every source byte and old span numbering. Enforce aggregate receipt bounds independently; small individual chunks alone do not solve expansion. Neither range-map behavior nor persisted new-record compatibility has been qualified here.

For the preferred repair trial, retain existing exact validator and old replay semantics, impose one explicit overall two-call budget, validate the entire second answer, and preserve the first failure plus both raw responses without overwriting a saved answer. Two individually bounded responses can jointly exceed64KiB; reserve a complete receipt/audit envelope before requesting repair or fail closed on publication size. A versioned new receipt may be needed to bind both attempts, while existing IDs/bytes remain unchanged. Owner-death/cancellation and receipt publication behavior must be tested in that implementation unit, not inferred from this private script.

## Evidence and limits

Full private artifacts: `.gflo/document-citation-prototype/`, mirrored rig directory `/home/gradrix/gflo-citation-prototype-03f51ebe/`. Every call has saved request, raw HTTP JSON, parsed response, exact content, outcome and—only when valid—derived/validated answer. [Results](document-citation-prototype/results.json), [run log](document-citation-prototype/run.log), [84-file artifact manifest](document-citation-prototype/artifact-manifest.json), manifest SHA256 `6e2904ac4b8aad39cd29bba0f1990e45bcc95393e92fc0f1b7d71ebf8c2bf100`. Frozen source/input hashes reverified after calls. Disposable offline replay cache is excluded from that manifest.

The small cohort does not establish general entailment, long-page accuracy, prompt-injection resistance, migration safety, or production repair lifecycle. The prototype preserves actual failures and separates required facts, whole-source truth, and citation-specific support. It does not broaden Stage4 acceptance.
