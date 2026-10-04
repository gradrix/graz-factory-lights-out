# Format3 document references: independent security assessment

2026-10-04. **Outcome: PASS within the chosen bounded-reference contract; no material defect found. Coverage: frozen source review, 63 focused controls and independent offline comparison of 18 actual historical records.** No model calls, rig operations, source acquisition, maintained edits or service changes. No scoped security blocker to the separately gated 13-question trial.

## Frozen identity and scope

Commit **`92deaab`**; [builder-candidate.json](builder-candidate.json) SHA-256 **`acd723171fe9b3f5ce9b90b2dc8aea29dbb5e57d41854cf322798690556bc698`**; contract SHA-256 `4e1077bd1e2ef48f4a76375e79eb5c42dd9ce6ca0719ca6418474fe5e5ffd106`. All 15 bound paths match before/after, immutable commit and private reconstructed runtime. [Before](security/hashes-before.json), [after](security/hashes-after.json).

The model chooses span IDs within one controller-bound immutable evidence record. Only the controller constructs source IDs and exact whole-span excerpts. Source/model text grants no tools, new sources, paths or execution authority. The assessment retains the controller-owned store assumption and distinguishes literal provenance from semantic support. It does not rescind or rescore either failed exact-quote trial outcome.

## Reference and capacity controls

[references.py](security/references.py) and [reference-results.json](security/reference-results.json) contain 42 observations:

- Strict ID/type/range and schema rejection: boolean, zero, negative, out-of-range, float, string and null IDs; empty/five-reference claims; nine claims; 17 occurrences; extra evidence/quote fields; and a bad ID in a later claim. A watched source list raises if indexed for expansion: these invalid cases reject before any expansion, including after an initially valid claim.
- Exact encoded claim, excerpt and reason limits pass; one additional encoded byte rejects. Paired cases include ASCII, astral Unicode and escaped control characters. The canonical JSON string's quotes/escapes are included in each count.
- Eight maximum-sized claims and 16 repeated occurrences of a maximum-sized span produce **42,893 encoded bytes**, below the 48 KiB canonical limit. Repeated references are charged each time. The 128-reference expansion admitted by the old prototype is excluded by the occurrence ceiling.
- Pure serializer controls enforce 12 KiB metadata and 48 KiB canonical answer, each with a +1 rejection. The 48 KiB defense is not reached by a legal bounded reference result; its negative control deliberately isolates serialization rather than pretending to be a legal model answer. The unchanged final 64 KiB receipt check remains authoritative.
- An ordinary reference materializes exact source U+2019 without any model quote field. With long source context, eligible selection still succeeds; selecting the long span then repairing to abstention yields two invalid attempts and an unreplayable capacity diagnostic. With all spans eligible, insufficient evidence remains a valid one-call answer. Source spans remain unchanged.
- Cancellation before repair and during final sync publishes nothing and never starts a second call.

The reader validates all fields/counts/IDs/selected-span capacities before constructing citation dictionaries, then applies the existing canonical provenance validator. Protocol metadata binds the exact deterministic catalog and limits; the model cannot replace that mapping.

## Metadata edge requested by coordinator

[metadata.py](security/metadata.py), [metadata-results.json](security/metadata-results.json) exercise an operator context exactly at the **12,288-byte preflight reservation**. A terminal error containing 512 astral characters encodes to **6,146 bytes**, exceeding the per-string U+FFFF reservation used in the preflight helper. This is not a defect for the reachable state combinations tested:

| Terminal path at exact admission edge | Actual saved metadata | Result |
| --- | ---: | --- |
| First call returns a 512-astral-character transport error | 8,942 bytes | Immutable failed diagnostic, one call |
| Invalid first response, then that transport error | 9,252 bytes | Immutable failed diagnostic, response1 retained, two calls |
| Reservation increased by one byte | 12,289 bytes | Refused before any call/publication |

Only one arbitrary transport error can terminate a run; the preceding structural error and terminal failure label are bounded fixed messages. The complete two-slot/error/failure reservation is conservative for those reachable outcomes despite its per-string surrogate assumption. This conclusion is specific to the current version, not a generic claim that U+FFFF is the largest encoded Unicode character. Final metadata checks remain necessary.

## Authority, tampering and publication

Five [authority controls](security/authority-results.json), reproduced by [authority.py](security/authority.py), show tool/function calls, malformed envelope and transport `ValueError` each terminate after one call with a failed diagnostic. Invalid ID followed by valid selection makes exactly two calls, retaining the original failure; original request messages/profile remain unchanged and rejected output is appended as untrusted user data. Neither request exposes tools/functions.

Thirteen [ledger/publication controls](security/ledger-results.json), reproduced by [ledger.py](security/ledger.py), reject rehashed catalog/limit/canonical excerpt/source/span/request changes, a rehashed raw selection inconsistent with the canonical answer, boolean/unknown format, an attempted format2 downgrade, and an extra response file. Each uses a fresh receipt identity so collision rejection cannot mask validation. Prior passing output remains replayable. Both success and failed-diagnostic paths trigger **no read/write/render/cleanup operation after final rename** under armed sentinels.

The final receipt still binds the complete returned responses and canonical answer, which is recomputed using the selected versioned materializer. Failed diagnostics are inspectable but not replayable as cited answers. No clipping, silent source mutation, protocol fallback or extra repair call is introduced.

## Actual legacy compatibility and carried lifecycle evidence

[legacy.py](security/legacy.py) privately copies the preserved actual trial1 and earlier CSV/JSON stores. It runs frozen `2fe870d` and frozen `92deaab` in separate processes against those copies. [legacy-results.json](security/legacy-results.json) confirms identical resolve/replay outputs, excluding only dynamic `age_seconds`, for **5 format1 evidence records, 3 format1 answers, 8 format2 answers and 2 format2 failed diagnostics**. Failed replay error text remains `Replay requires a saved answer ID`. Every original/copied record-file hash remains unchanged; model and executor callbacks are forbidden.

Source comparison also verifies byte-identical `validate_answer`, `answer_request`, `repair_request`, `response_answer` and `bounded_answer`. Hashes are in the legacy result. Seven store/lifecycle methods—publication, replay, cleanup, reservation, lease, executor and acquisition—are unchanged, with [method hashes](security/carried-methods.json).

The preceding [48-control assessment](../07-autonomy-document-reliability/security-documents.md) therefore carries forward for those unchanged seams, including actual fake-client second-child owner SIGKILL/cancellation/deadline, response-file integrity and byte bounds, failed CLI behavior and private-stage cleanup. This review renewed affected reference-reader, capacity, legacy and publication seams rather than repeating unrelated process/container tests. Child lifetime measurements are carried evidence, not newly performed against a changed guardian or model server.

## Reproduction and remaining acceptance boundary

Run the named Python probes from the repository. [fixture.py](security/fixture.py) reconstructs `92deaab` under ignored `.gflo/document-reference-security/frozen/`; it is an imported helper. The legacy probe also reconstructs `2fe870d` and requires preserved local stores at `.gflo/document-reliability-trial1/store` and `.gflo/document-research-cohort/{json,csv}/store`. It never modifies those originals. Scripts overwrite their own result files on rerun; preserve evidence first. No duplicate runtime trees are published.

The 63 focused controls are 42 reference/boundary cases, 3 metadata-edge cases, 5 authority cases and 13 ledger/publication cases; the 18 actual legacy record comparisons are reported separately. All conclusions bind the stated source hashes.

**Structural success does not establish that selected spans support every requested fact or extra claim.** Source alignment, ten repeated diagnostics, three frozen fresh questions, complete semantic/citation review and actual rig cross-version network-none replay remain separate gates. No general document-reliability rate, public browsing/search acceptance, host-compromise resistance or full Stage4 acceptance follows from this scoped verdict.
