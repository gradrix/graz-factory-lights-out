# Independent thirteen-case source alignment

**PASS: all10repeated diagnostics and3fresh transfer cases align.** Candidate92deaab / manifest `acd723171fe9b3f5ce9b90b2dc8aea29dbb5e57d41854cf322798690556bc698`; combined fixture `27e94d04f753112ce7e96470fbfc75980f7a8da3d61feea7ac6dcd0a370fb24c`.

Actual binding SHA256 `79d9f4311250d413a1056e95f58f7d000434102dc411a789c07ab2bb16b82725`. Independent [gate](source-alignment-gate.json) SHA256 `d3650e2ac787342aaec88c4beb0cfc57aa178c623011efa93c10d9423f4d677d`; **coordinator_go=false**. No model calls; root authorization and security gate remain separate.

All three acquired evidence-file hashes, source URLs/versions, newIDs, body/text hashes, extractor document-text-v2 and complete spans were checked against preserved actualtrial1 sources. Bodies and every span match; new evidence IDs correctly differ because this is a new acquisition. CSV226spans, JSON301, asyncio440, retrieved2026-10-04T16:03:47–50UTC. Baseline IDs remain intact in [alignment evidence](qa/source-alignment-evidence.json); no drift addendum or expected-fact revision required. Serving identities agree before/after.

The ten diagnostic facts retain their prior grounding: CSV44/61/192, JSON67/89/131/166, asyncio128–130/152/186/191/231/233. Both unsupported future-premise questions remain unsupported across the complete sources. Three fresh cases also align: CSV40/106 explicitly limit float conversion to unquoted fields; JSON143/144 establish the raw_decode result tuple/document-end index and trailing-data use; asyncio244/247/248/258 establish done/pending, no TimeoutError and no timeout cancellation. No unasked writer/whitespace/return_when behavior is required.

This gate binds the new source records; it does not award future model semantic success. Entire final answers, all extra claims, raw attempts and canonical citation selection still require independent review. Newly acquired historical3.12 pages do not establish current-runtime or exact installed-patch guidance. Ten repeats and three fresh cases must retain separate denominators.
