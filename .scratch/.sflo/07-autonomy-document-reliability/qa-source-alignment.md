# Independent pre-inference source alignment

**PASS: all ten frozen cases align with the three actual candidate acquisitions.** No model calls. Candidate2fe870d / manifest `4e1481dede629f9c83be9bbd0002d0975eccbd33820d4456ef5c75bd9eecfc2e`; qualification manifest `0fd8ecff10b17c584e049ae072eb9f31c67f6c33f4dc70beebfbc457e1394de1`.

Binding SHA256 `090bce9a18ad5ef85a37b5077d81c8e5959ec2ed89e530df0bb5ca83cfda4def`. Independent gate [source-alignment-gate.json](source-alignment-gate.json) SHA256 `ccdde4b640c7c70a20a60cd2db757d9c701abeef4650f8495d221e718619e336`; **coordinator_go=false**. Root may create its explicitly authorized gate version after reviewing this report; this file is not model-call authorization.

Verified each evidence-file hash, source URL/version, evidence ID, body identity and complete spans against the preserved baseline. All bodies and all spans match; no drift addenda or oracle changes are necessary. Actual document-text-v2 outputs: CSV226spans, JSON301, asyncio440. Retrieval times2026-10-04T15:32:37–40UTC; acquisitions1.33–1.48s. The source is freshly acquired historical3.12 documentation, not a current-runtime or exact-patch claim. Serving ID/image/96K/Q4/one-slot fields match before/after.

| Cases | Independent grounding |
|---|---|
| row_shape_defaults | CSV44/61 establish default writer loss and extra/missing field behavior; question explicitly excludes optional writer modes. |
| json_hooks | JSON89/131 support priority, ordered pairs and return-value replacement, all explicitly asked. |
| csv_newlines | CSV192 supports embedded-newline interpretation, extra CR on CRLF writers and CSV-owned newline handling. |
| json_skipkeys | JSON67/166 support default TypeError and True skipping unsupported-key items. |
| asyncio_taskgroup |128/129/130 establish cancellation, waiting and grouped non-cancellation failures. |
| asyncio_gather |152 establishes immediate propagation to awaiting task and continued sibling awaitables. |
| asyncio_wait_for |231/233 establish cancellation, TimeoutError and waiting beyond the timeout. |
| asyncio_shield |186/191 establish caller versus inner cancellation and weak-reference collection risk. |
| Both future-date questions | Complete sources provide no3.16 premise/date; expected insufficiency remains justified. No arbitrary refusal wording required. |

[Complete passage evidence](qa/source-alignment-evidence.json), [reproducible offline verifier](qa/align-sources.py). Span IDs are aids, not exclusive permissible citations. Answer semantics and all extra claims still require independent review after inference; alignment does not pre-award success. The four old asyncio acquisition failures remain unattempted in their original cohort.

## Rig offline replay approach after answers

Use one fresh ordinary runc container from pinned Python image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, networknone, nonroot uid/gid matching private record ownership, readonly root, capdropALL/no-new-privileges, bounded memory/PIDs/time and tmpfs. Mount frozen `gflo` sourceRO, the new storeRW only for its lease, and a private copied legacy storeRW. Mount no model config, keys, socket or other project trees. Execute a fixed small trusted script calling `DocumentStore.replay` for every successful format2 answer and the two previously accepted actual format1 answer IDs; `resolve` diagnostic format2 failures and require `replay` refusal if any exist.

Host computes every regular record-file hash before and after, excluding only the known store lease file; verify exact map equality, not merely a subset. Compare replay answers/evidence IDs/source versions with saved public outputs, allowing only age_seconds to differ. Include the actual inspected container resources/network/mounts, exit and cleanup readback. Retain original legacy artifacts; copy with private modes unchanged. Root chooses the current exact legacy store path on rig from the preserved trial1 record, rather than relying on a stale checkout path. This plan is not evidence that offline replay has already run.
