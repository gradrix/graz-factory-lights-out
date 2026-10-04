# Independent unit07 rig semantic/replay QA — trial1

**Cohort FAIL:8/10 meet the frozen answer outcomes;2/10 are preserved citation failures. Functional fail-closed behavior and actual offline replay PASS.** Candidate2fe870d, manifest `4e1481dede629f9c83be9bbd0002d0975eccbd33820d4456ef5c75bd9eecfc2e`; authorized gate `d5fb4148d14257f373e9793f7c418e72eae7614a138108dd0453ef6c06d31f21`. No inference or retries by this reviewer; no maintained edits or installation.

Full immutable trial copy: `.gflo/document-reliability-trial1`; original rig `/home/gradrix/gflo-documents-2fe870d/.gflo/qualification-1`. Reviewed all13 raw responses, all original/repaired claims, final citations and insufficient reasons against the independently aligned source and frozen oracle. Verified content-addressed receipt/response sizes/hashes and final literal citation matches. [Reproducible audit](qa/review-answers.py), [complete claim/attempt evidence](qa/answer-review-evidence.json), [punctuation discrimination](qa/quote-diagnosis.json).

| Question | Attempts / outcome | Independent semantic assessment |
|---|---|---|
| row_shape_defaults |2 / PASS | Extra/missing fields and default writer distinction all covered61/44. First quote substituted ASCII apostrophe; repair corrected it. Extra default QUOTE_MINIMAL claim supported142. Initial parenthetical QUOTE_MINIMAL in the writer-loss claim was only supported by the separate third claim citation; final response removes that parenthetical and retains the correctly cited third claim. |
| json_hooks |1 / PASS | Priority, ordered pairs and return replacement all covered89/131, no extras. |
| csv_newlines |1 / PASS | Both newline hazards and CSV newline handling covered192. Extra reader/writer file-opening advice supported39/44. |
| json_skipkeys |1 / PASS | Default TypeError and explicit skipping supported67/166, no extras. |
| asyncio_taskgroup |1 / PASS | Cancellation, awaited completion and grouped non-cancellation failures supported128–130; no unsupported version details. |
| asyncio_gather |2 / FAIL | Both raw answers express correct immediate propagation and continued sibling execution. Both replace source `won’t` with ASCII `won't` in excerpts152. Repair broadens both citations to the whole span but repeats the mismatch. No usable answer published. |
| asyncio_wait_for |1 / PASS | Cancellation, TimeoutError and possible timeout overrun supported231/233. Extra propagation of exceptions during cancellation supported233. |
| asyncio_shield |2 / FAIL | Both raw answers express correct caller/inner cancellation and weak-reference risk. Both change source curly quotes around “await” to straight quotes in186, and curly apostrophes in191 to ASCII. Repair retains both defects. No usable answer published. |
| future_csv_date |1 / PASS | Correct insufficiency; no invented date/change. Reason's extra3.12.15 documentation label is present in source22/214; it is not a claim about installed Python runtime. |
| future_taskgroup_date |1 / PASS | Correct insufficiency; no invented premise/date. Historical3.12 boundary and TaskGroup introduction3.11 match source33/77/123; no unsupported forward-version claim. |

## Exact failure diagnosis and unchanged scoring

All eight nonmatching excerpts across the rejected attempts become source substrings when only the indicated straight punctuation is replaced with the source curly characters. This offline comparison is diagnostic only: original bytes remain invalid, validation was not weakened, and failed questions were not rescored. These are exact-quote generation/repair failures, not demonstrated misunderstanding of the requested facts. Neither failure exhausted tokens: all13 responses finish `stop`,264–1018completion tokens versus2048cap.

Seven questions succeed first-call; the one repaired CSV answer makes eight final successes. Three cases invoke the one allowed repair, two exhaust it.13calls total; sum of public answer durations460.340s. Gather46.121s, shield71.623s including their repairs. Five repeat diagnostics all meet outcomes; among five new inference cases, TaskGroup/wait_for/futureTaskGroup pass while gather/shield fail. This is not a ten-unseen success. Old asyncio source-acquisition failures retain their original unattempted scores; this trial acquired all three sources successfully.

## Actual rig offline replay PASS

Frozen [offline-replay.py](qa/offline-replay.py) SHA256 `5b7fc6f3b9576802c2f63a6dc3e6aac41cd79c7590baf36de160625261d27827` ran only after the answer phase completed. It privately copied the new store and actual accepted legacy trial1 store. Pinned Python3.12 image `fb1118…`, ordinary runc, networknone, nonroot, readonly root, capdropALL/no-new-privileges,256MiB memory=swap,64PIDs,1CPU, bounded tmpfs. Mounts were exactly frozen sourceRO, trusted probe/case filesRO and the two copied storesRW; no model config, keys, socket or project execution tree.

Eight format2 answers and two real format1 accepted answers replayed identically except age_seconds. Both format2 failure diagnostics resolved and refused replay. All original and copied record hashes remained identical, excluding only each store's root `.lock`; candidate hashes unchanged. Container removed with confirmed absence. Total0.574s. [Result and hash maps](qa/replay/result.json), [actual container facts](qa/replay/container.json), [cleanup](qa/replay/cleanup.json).

## Decision

The new extractor and durable bounded repair/failure mechanisms work in this trial, but one structural repair is insufficient for the literal ten-of-ten answer gate. Do not install/promote this failed cohort as accepted, retry it as unseen, or turn semantic correctness into citation acceptance. Preserve it as a regression for a separately specified and independently tested next change. Whole-span references still have the previously measured4096-byte limitation; these failures alone do not justify silently adopting that alternative or normalizing frozen source text. FullStage4 search/public-browser acceptance remains separate.
