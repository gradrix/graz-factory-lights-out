# Serving profile QA

**Verdict: supported as a bounded 96K/Q4 operational trial; not broad benchmark or coding certification.** Read-only review using s-qa, with no model calls or service changes. Candidate `ops/model.py` SHA-256: `d8e5a9de083b7a8ba8cc15cf7c8b97322e3038b9ff50b523470e1f66a1607c9f`. Input and documentation hashes are retained in `qa-serving-profile-evidence.json`.

| Check | Observed result |
| --- | --- |
| Full 128K/64K/96K restart commands | Exactly one differing argument value: `-c` = 131072/65536/98304. Q4 K/V, image, model path, runtime, Docker flags and other model arguments match. |
| Request/control identity | Same reconstructed request hash; 16,947 prompt tokens and 256 generated tokens for every sample. Container IDs match their respective restart receipts. |
| Warm medians, excluding first request | 128K: **16.52284**; 64K: **74.92489**; 96K: **73.94915** tokens/s. Two warm samples per profile. All reported values and diagnostic pass/fail flags agree. |
| Retrieval | Reconstructed request hash matches; all three values exactly correct across 81,441 prompt tokens, 96.71811 seconds. Decode rate on this different, longer request is 35.86371 tokens/s. |
| CLI/default policy | Default 98304; default Q4 at 96K/128K and Q8 at 64K. Explicit q4_0/q8_0 override reaches both cache flags. |
| User-facing docs | Model-profile, operations and roadmap describe 96K as a trial, retain prior failures, and limit retrieval/throughput claims appropriately. |

The 96K setting delivered **4.476×** the 128K warmed decode rate on the fixed 16.9K-token request in this sequence. Identical-request 128K restart remained slow; reducing allocation while holding launch arguments fixed restored speed at both 64K and 96K. This supports the allocation choice under the observed conditions. **VRAM/WDDM residency pressure remains an explanation, not a measured mechanism:** receipts contain no residency/page-fault trace, and cited VRAM observations occurred in different utilization phases. Sequential short trials do not control all host-load variation.

96K is a reasonable trial choice: it retains essentially the observed 64K short-probe speed while accommodating the recorded 81K retrieval input. It is the largest allocation tested here with that speed, not an established optimum. Two warm samples, one repetitive generation request and one three-value retrieval do not establish sustained coding throughput, reliability throughout 96K, concurrency or general quality. The 50-token/s diagnostic threshold is not a universal pass criterion; the larger retrieval request itself decoded below it.

## Documentation and evidence follow-ups

- `.scratch/autonomy/issues/05-serving-throughput.md` remains labeled “measurements queued,” says the service still reports 131072, and says retrieval is running. Its later findings/current trial should replace those stale present-tense status claims. Historical ADR002 and pilot results can remain explicitly historical.
- `96k-retrieval.json` lacks container ID, image and serving-context fields. Its correct output and request identity are independently verified; attaching it to the 96K allocation relies on the surrounding experiment record. Future retrieval receipts should capture serving identity like the timing probe.
- To reproduce the measured **64K/Q4** comparison, use `--context 65536 --cache-type q4_0`; the operations example without the override selects the separately retained 64K/Q8 profile. The prose correctly explains this distinction.

Evidence reproduction: `python3 .scratch/.sflo/04-autonomy-environments/qa-serving-profile-check.py`. It reads local receipts and the stored remote restart-128K receipt via SSH, recomputes request hashes and medians, compares complete command lists, and inspects cache policy without invoking service operations. The captured original restart receipt remains in `qa-serving-profile-evidence.json`. No active API/model task was touched.
