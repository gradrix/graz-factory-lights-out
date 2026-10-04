# Independent format3 rig semantic/replay QA

**PASS for this bounded cohort:10/10 repeated diagnostics and3/3 fresh transfer cases. Actual cross-version offline replay:25/25 checks pass.** Candidate92deaab; manifest `acd723171fe9b3f5ce9b90b2dc8aea29dbb5e57d41854cf322798690556bc698`; combined fixture `27e94d04f753112ce7e96470fbfc75980f7a8da3d61feea7ac6dcd0a370fb24c`; authorized gate `e6856dc86febe89b35357334397b9317b1c1c540072a143a359fead8693cfbe8`.

Reviewed all23raw responses, every original/final claim and explanatory reason, all selected spans and controller-materialized citations against frozen sources/oracles. Verified request reconstruction, attempt ledger, response/receipt identities, complete exact excerpts and final statuses. Full private evidence remains `.gflo/document-reference-trial1` and rig `/home/gradrix/gflo-documents-92deaab/.gflo/qualification-1`. [Reproducible audit](qa/review-answers.py), [complete attempt/canonical evidence](qa/answer-review-evidence.json). No inference/retry/installation by this reviewer.

## Semantic outcomes

| Group / case | Final assessment |
|---|---|
| Repeat: row_shape_defaults | All default extra/missing field and writer-loss facts complete;61/44 entail them. |
| Repeat: json_hooks | Priority, ordered pairs and return replacement complete;89/131. |
| Repeat: csv_newlines | Both newline hazards and CSV newline handling complete;192. Extra reader/writer file-opening advice supported39/44; read as documented advice, not a claimed runtime enforcement error. |
| Repeat: json_skipkeys | Default TypeError and True skipping complete;67/166. |
| Repeat: asyncio_taskgroup | Remaining cancellation, exit waiting and grouped failures complete;128–130. |
| Repeat: asyncio_gather | Immediate propagation and continued siblings complete;152. Controller excerpt preserves source curly punctuation. |
| Repeat: asyncio_wait_for | Cancellation, TimeoutError and overrun complete;231/233/237. Extra propagation during cancellation supported233. |
| Repeat: asyncio_shield | Protected inner task, caller CancelledError and strong-reference need complete;186/191. No invented immunity from other cancellation. |
| Repeat: both future-date cases | Correct insufficient_evidence, empty claims; historical3.12 reasons do not invent dates or validate future premises. |
| Fresh: csv_nonnumeric_reader | Default strings and unquoted numeric→float conversion complete; quoted numeric-looking fields excluded from conversion, read with default-string statement.40/106. Scope stays within numeric-looking fields. |
| Fresh: json_raw_decode_suffix | Initial document despite trailing data, tuple values and document-end index complete;143/144. No unsupported leading-whitespace behavior. |
| Fresh: asyncio_wait_timeout | No TimeoutError, done/pending sets, unfinished tasks in pending and no timeout cancellation complete;244/248/258. Distinguishes wait from wait_for. |

All initial explanatory reasons were also supported summaries of the same selected evidence. No unsupported extra/version claim was found. Whole-span citations can be broader than individual claims; manual entailment, not literal source identity alone, supports this verdict.

## Repair behavior and costs

Only3/13 answers were valid first-call: shield and both insufficiency cases. The other10 initially returned a nonempty `reason` despite supported status. Each exhausted exactly its one allowed structural repair successfully. Independent JSON comparison shows **every repair only changes reason to the empty string**; claims and span selections remain identical. Original invalid responses remain preserved and invalid. [Repair delta evidence](qa/repair-delta.json).

23calls, no third calls/external retry; all finish `stop`,130–711completion tokens versus2048cap. Sum of answer durations850.939s:658.454s for ten repeats,192.485s for three fresh cases; maximum case83.104s. This is successful bounded recovery, not reliable first-call schema adherence or evidence of a speed improvement. The prior exact-quote8/10 trial remains failed under its original rules; these ten questions are repeats, not newly unseen successes.

## Actual rig network-none replay

Prepared [probe](qa/offline-replay.py) SHA256 `7976002b8ed2f3b6a3733ae14fe3fb0971d86f3b405933253f81dff793530ae4` executed once after the13-case phase completed. Explicit candidate/newtrial and reviewed historical summary/receipt hashes bound inputs. Three private stores copied with preserved modes; originals never mounted.

Pinned Python image `fb1118…`, runc/networknone/nonroot/readonly root, capdropALL/no-new-privileges,256MiB memory=swap,1CPU,64PIDs, bounded tmpfs. Only frozen sourceRO, trusted probe/case filesRO and three private copied storesRW were mounted; no model config, keys, Docker socket or other project tree. Actual inspection and cleanup saved.

13format3 answers,8actualformat2 successes and2actualformat1 successes replayed identically except age_seconds. Both preserved format2 failure diagnostics resolved and refused replay with their unchanged error semantics. All original/copied record hashes remained unchanged, excluding only each root lease; frozen candidate files unchanged.25checks in0.684s, container removed with confirmed absence. [Result/hash maps](qa/replay/result.json), [container facts](qa/replay/container.json), [cleanup](qa/replay/cleanup.json).

## Scope

The requested rig semantic and replay gates are met. Coordinator may combine this with candidate-bound functional/security/full-suite evidence for the narrow unit decision. Long/unselectable spans remain an explicit bounded-protocol limitation; this cohort's eligible sources do not establish broad-document coverage. No general accuracy guarantee, public search/browser acceptance, independent unseen-document result or end-to-end autonomous delivery claim follows.
