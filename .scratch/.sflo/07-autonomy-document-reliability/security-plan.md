# Document reliability: prefreeze security boundary review

2026-10-04. Skill: security-check. **Outcome: suitable narrow implementation direction, subject to the concrete invariants below. Coverage: read-only design/current-source review; no implemented unit07 candidate has been qualified.** Builder owns all maintained mutations. No model, fetch, Docker, rig or service operation was performed.

Reviewed [contract.md](contract.md), SHA-256 **`b2adcce1ceaaa777d855d570b5a354b5480bb63209aeda5c7843c13f9e135456`**, [ADR006](../../../docs/decisions/architecture/006-document-validation-repair.md), current `gflo/documents.py`, document CLI and prior event-limit evidence. Original unit05 receipts and failed trials remain evidence, not material to overwrite.

## Trust and assets

Controller owns approved question/source, immutable evidence, model/profile, request construction, validation and publication. Source HTML, extracted text and both model responses are untrusted data. A model response cannot choose tools, fetch a new source, change the question/profile, broaden retry eligibility or create receipt paths. Exact citations establish literal provenance only; the revised answer needs independent semantic review because a structural repair may alter claims.

Assets are truthful success/failure identity, retained attempts and prior records, bounded controller/store/model resource use, and host credentials/authority. Existing controller-owned-store, local-inference child ownership and approved fetch/extraction boundaries persist. Privileged hostile host writers, model semantic correctness from schema alone and power-loss durability are not established here.

## Concrete design risks sent to builder

### 1. Separate repairable validation from inference/authority failures

Current `bounded_answer` reports transport, response overflow, child failure and deadline conditions using exceptions including `ValueError`. A broad catch around the entire call would therefore accidentally authorize a second request. Only validation of **returned assistant text**—JSON, answer shape or citations—can spend the one repair allowance. Tool/function calls, malformed provider response envelope, unavailable evidence, cancellation and ordinary inference errors must terminate without repair. Provider content is never executable authority.

Persist each available bounded response before deciding its validation result. If the second call fails to return usable bytes, retain the rejected first response and a bounded terminal error. For a tool-authority violation retain the available response as a failed diagnostic without executing or retrying it. Do not relabel missing/oversized/truncated transport as a complete model attempt. Strictly distinguish valid `insufficient_evidence` from exhausted invalid output.

Use the same frozen question/evidence and fixed model/profile for the repair request. Put the first response and concise validation error inside explicitly untrusted data, not interpolated privileged instructions. Bound this extra request material and the error string; no fixture-specific answer hints. Record both request hashes and exact profile metadata, with no credentials or key-file content in a receipt.

### 2. Make the version2 ledger internally consistent

Resolve by explicit format/kind, not by opportunistically falling back to format1 when new files are missing. For version2 require the exact fixed file set implied by one or two contiguous attempts, no extra file/links/specials, each available file's full byte length/hash, bounded metadata and receipt size. Zero response files are legitimate only for an explicitly recorded first-call failure that returned no usable response; do not invent bytes to satisfy a schema. Reject missing declared files, duplicate, reordered, spliced or extra attempt references and an unknown terminal state. Each response is at most64KiB; all files plus receipt are at most192KiB under unchanged store/staging limits.

The canonical answer must correspond to the selected **last validated response**, with matching validation metadata; a rejected response cannot be promoted by changing a status field. Validate decoded shape/provenance again on replay against the frozen evidence. A success label alone is insufficient. The failed diagnostic kind must be inspectable but rejected by the cited-answer replay/API path, even if its raw response happens to contain a plausible answer.

Check encoded sizes, not Python character count. A legal response near64KiB can still crowd the receipt once canonical answer, question, two request hashes and validation metadata are included. Budget the canonical answer and receipt before committing rather than increasing receipt size or losing retained attempts after an overflow. Receipt overhead belongs inside the stated192KiB ceiling. Store accounting must include the two response files for both successes and diagnostics; no silent eviction.

### 3. Preserve cancellation/publication semantics for every outcome

Retain `_publish`'s private validation/sync, final cancellation/deadline fence and atomic rename as the last filesystem operation. Prepare successful replay output or the failed-record identifier/error before publication. Immediately relinquish staging ownership after successful rename; no fallible path stat, cleanup, rendering or record read follows that commit. Raising a precomputed failure containing its committed diagnostic ID is compatible with this invariant; a postcommit filesystem failure is not.

Cancellation before repair, while the second child runs, during validation/sync or just before rename must never publish success. The contract selects refusal of publication for ordinary cancellation, with private interrupted state handled by explicit cleanup. Preserve existing prior good and avoid creating a success from a rejected first attempt when repair is cancelled. Unexpected owner death may leave private staging; it must not expose a partial public ledger or retain a live answer child.

### 4. Treat260 seconds as one operation deadline

Two independent120-second call limits plus two possible10-second child cleanup waits already consume260seconds, before ledger validation/publication. Use one monotonic deadline for the complete answer operation, pass remaining budget through both calls/cleanup, and reserve what is needed to finish or refuse safely. Do not reset the total deadline for repair. Keep per-call120seconds as a maximum, and ensure an exhausted global budget cannot begin another request. No third call or transport retry is introduced by this feature.

### 5. Version extraction and keep old records offline

Change only the HTML event ceiling and extractor identity. Retain body/text/depth/block/time/memory, fetch allowlist/DNS/TLS/redirect/retention and framing rules. An unchanged floating source URL is not a new exact source version: receipts bind actual raw bytes and extraction identity. Prior10000-event evidence remains valid historical output, not silently recomputed using40000.

Format1 inspection/replay must retain original response/canonical answer semantics and byte-identical records with no model, network, extraction or migration. Format2 likewise resolves offline. Unknown versions and tampered files fail closed; old records do not gain a synthetic repair history. The original failed asyncio admission and copied-apostrophe response remain separately preserved.

## Focused frozen-candidate security checks

| Boundary | Positive and negative controls |
| --- | --- |
| Repair authority | Valid first response makes exactly one call; invalid returned JSON/citation then corrected response makes exactly two; tool calls, transport error, timeout, overflow and unavailable evidence make no repair. Inspect both requests for fixed evidence/question/profile/no tools. |
| Failed ledger | Two invalid texts publish one inspectable failed diagnostic with both original files, nonzero CLI/API outcome and ID; replay refuses it. Failure on second transport retains available first attempt without inventing second bytes. |
| File integrity/resources | Exact per-file/receipt sizes versus+1; encoded Unicode expansion; missing/extra/name traversal/links/specials/hash/size mismatch; canonical answer inconsistent with selected response; store accounting and prior-good retention. |
| Lifetime/publication | Cancellation before second request and during final sync; owner death with second child active; bounded per-call/total timeout; private write/sync/rename failure; no public partial/success and no late postcommit I/O. |
| Compatibility | Frozen format1 evidence/answer replay with unchanged hashes and zero client/executor calls; format2 one-call/two-call/insufficient-evidence replay; failed diagnostics never replay as answers. |
| Extraction | Cached measured asyncio body plus40000/+1 event and unchanged depth/text/block paired cases in pinned offline resource envelope; new helper identity recorded, old evidence untouched. |

The actual ten-question5090 semantic cohort and target offline replay are assigned separate QA gates. Source/structural security success does not convert malformed outputs, unattempted acquisitions or unsupported extra claims into correct answers. Later security outcome and coverage must be bound to a frozen candidate, with controlled versus actual measurements distinguished.

## Source handoff to independent QA

Read-only rehash confirmed cached official asyncio body `.gflo/document-event-prototype/asyncio-body.html`:156345bytes, SHA-256 `b395cf62082c34beeebfdc8b7a5a34f997411f6499fa14cf66425bcd20ff1381`. Provenance/measurements are in `.scratch/autonomy/document-event-prototype/`; prior measured complete output440spans/37712UTF8bytes, compact ASCII-escaped JSON hash `14d4153f4ce19c76b10bf2f1acbcad5c284d655c0d5b7ebcae1dfefeb1f4177e`. Full spans were not saved by the measurement wrapper. The four originally unattempted questions/facts are in unit05 `research-cohort/asyncio_groups.json` and `asyncio_timeouts.json`. These paths/hashes were sent to QA; no source refetch or inference was needed.
