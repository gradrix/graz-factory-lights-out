# Unit 09 actual trial: independent accounting and lifetime audit

**Outcome: PASS for accounting, evidence integrity and recorded isolation/lifetime. The four-case discriminator failed its completion gate: one valid review, three incomplete reviews.** A completed review is distinct from a correct classification or a passing candidate.

Frozen prototype `37b7f1d1416d5497ca38291b47b364882d2d44ef`, driver SHA256 `ede30d388c75b1c69c683dbd4c61cae408afc73cd5d35f84c1748d0ab281ecaa`. Admission SHA256 `60881da16b029f2336d82ac6defa8d7f7aeab957c4494c9d1d58bfee2df4747d`; artifact manifest SHA256 `48726e1f0149ee9a9b08f96a4bb0f6ba6e759dbe7df98cf8e9e8cee449564e4f`.

## Terminal accounting

| Case | Requests | Commands | Work seconds | Cleanup seconds | Terminal outcome |
|---|---:|---:|---:|---:|---|
| case-01 | 5 | 6 | 74.444 | 1.331 | Incomplete: fenced JSON + prose |
| case-02 | 2 | 2 | 92.358 | 1.271 | Incomplete: length-limited tool completion |
| case-03 | 6 | 8 | 89.756 | 1.359 | Incomplete: prose instead of JSON |
| case-04 | 7 | 9 | 107.430 | 1.382 | Completed valid repair verdict |

Exactly **20 charged requests and 25 attested commands** reconcile among ledgers, reservation journals, numbered directories, captured requests/responses and reconstructed conversation transitions. Every request returned HTTP 200 with complete raw capture and a matching decoded response. HTTP success did not imply a valid review. No extra transport directory, hidden repair request or replay appears in this admitted controller trajectory. Each case remained below eight requests, twelve commands and 300 work seconds; none ended through request-budget exhaustion. Remaining request credits were 3, 6, 2 and 1.

Cases 1 and 3 ended with `JSONDecodeError`, and neither has a verdict artifact. Their terminal content is respectively Markdown-fenced JSON plus prose and a prose summary; this audit does not salvage either. Case 2 returned `finish_reason=length` with two proposed tool calls; both were refused before dispatch. Those proposals are not included among the 25 actual commands. Case 4 alone persisted a schema-valid `repair` verdict matching its terminal response and nine attested commands. Internal `accepted` denotes completed review, not candidate acceptance. Independent semantic QA owns the finding’s correctness.

## Usage and elapsed time

All 20 responses contain explicit usage: **217,393 prompt tokens, 17,212 completion tokens, 234,605 total tokens**, including **180,235 explicitly reported cached prompt tokens**. Cached tokens are a subset of prompt tokens, not additional usage. No usage record is missing. Per-case totals and request latency min/median/max are in [the JSON audit](trial-accounting.json).

Recorded sums: 363.988 work seconds, 5.345 cleanup seconds, 351.473 request elapsed seconds and 10.736 command elapsed seconds. These are sums of their respective reported measurements, not an inferred end-to-end wall duration or model-only generation speed. Raw requests were at most 63,129 bytes and responses at most 12,163 bytes, within their 4 MiB/1 MiB caps. Profile stayed flash-next-coder, medium reasoning, temperature 0, 4096 output tokens and 1024 thinking tokens, with only the fixed run tool.

## Execution, inputs and cleanup

All 25 creation receipts match the pinned image and fixed nonroot `1000:1000`, runc, network-none, read-only root, cap-drop ALL, no-new-privileges, 1 GiB memory/swap, 2 CPU, 128 PIDs, 16 MiB shared memory and 128 MiB temporary-space settings. Each has exactly two read-only bind mounts: its own `/candidate` and approved stdlib dependencies `/opt/deps`. No host workspace, socket, credential or GPU/device mount is present. Arguments disable Docker logging; this is recorded argument evidence, not separate LogConfig readback.

Every command has a matching controller nonce at the start of captured stdout, matching raw/ledger hashes, and an exact-name confirmed-absence receipt. The output returned in each later model request was independently reconstructed, including nonce removal, truncation and tool role; it matches the stored conversation. All commands finished without recorded timeout or output-limit events. Two case-1 probes exited nonzero (2 and 1); their failures remain evidence and were not rewritten as success. Remaining commands exited zero.

All four input file sets, bytes, recorded permission modes and copied modes match the frozen public fixture. Public objective hashes match exactly. The system instruction and tool schema match the frozen source, including its documented-path adaptation sentence. No private fixture expectations appear in the initial objective/files payload. The full conversation preserves source and output as untrusted data.

All four parent results record owned client group absence, confirmed command cleanup and fresh same-identity idle. Each case has two preflight and two final idle observations separated by at least one second per pair. All 16 observations retain the admitted container/image/start identity and the single idle slot with context 98304/Q4 caches; no restart or identity change is recorded. Every cleanup completed within its shared 150-second allowance. No uncertainty fence remains in the copied case outputs.

## Reproduction and limits

[Read-only script](trial-accounting.py): `python3 .scratch/.sflo/09-autonomy-executable-review/trial-accounting.py`. It verifies all **325 manifest entries**, exact included file set, unchanged before/after artifact hashes, root/per-case result consistency, admission gate hashes and all 37 bound prototype files. Raw evidence is `.gflo/executable-review-trial-1/`; compact results are [trial-accounting.json](trial-accounting.json).

This audit reads persisted evidence and frozen trusted-controller logic only. It does not execute candidates, contact the rig/model, query current daemon state or independently capture network traffic. It proves no additional calls in the recorded admitted trajectory, not absence of unrelated serving clients. The failed quality gate remains failed; no retry, parser salvage, reconstructed verdict or new promotion is authorized by this accounting result.
