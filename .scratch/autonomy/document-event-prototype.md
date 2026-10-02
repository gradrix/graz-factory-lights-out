# Document parser event-limit experiment

2026-10-02. **Private prototype only.** Issue: [07-document-reliability](issues/07-document-reliability.md). Browser unit 06 remains the sole maintained-product mutation. No `gflo/`, maintained tests or runtime documentation was edited; no model, rig or shared-service operation was performed.

## Result

The approved official asyncio page contains **11,442 parser events**, exceeding the accepted 10,000-event cap. In a private experiment changing only `EVENT_LIMIT` to 40,000, it extracted completely into **440 spans / 37,712 UTF-8 text bytes**. Three fresh offline containers produced the identical extracted-span hash. This identifies a concrete admission-limit problem rather than a missing-package, memory or five-second-timeout failure.

A 40,000-event candidate is supported for a later versioned repair trial: the measured page and paired hostile boundary inputs remained far below the existing time/memory limits. **40,000 is not shown to be the smallest necessary value or sufficient for arbitrary pages.** The observed page needs at least 11,442; 40,000 provides additional admission room. No automatic promotion or broader document/model reliability claim follows.

## Source and unchanged envelope

Fetched exactly `https://docs.python.org/3.12/library/asyncio-task.html` once through accepted commit `2049361`'s approved-document helper, public IPv4/original-host TLS, no redirects, framed length/hash checks and retention policy. Fetch completed in 0.705 s. Response was identity HTML with declared/actual **156,345 bytes**, no restrictive cache directive or Set-Cookie; accepted protocol and full executor/HTTP facts are retained in [acquisition.json](document-event-prototype/acquisition.json).

Raw body SHA-256: `b395cf62082c34beeebfdc8b7a5a34f997411f6499fa14cf66425bcd20ff1381`. This is a floating Python3.12 documentation snapshot, not an exact runtime-patch guarantee. The original failed acquisition diagnostic remains [unchanged](../.sflo/05-autonomy-documents/research-cohort/asyncio-acquisition-diagnostic.json).

Every extraction ran with the accepted pinned Python3.12.13 image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`: network none, runc, nonroot, read-only root/mounts, dropped ALL capabilities/no-new-privileges, 256 MiB memory and equal swap limit, one CPU, 64 PIDs, 8 MiB shm and 16 MiB tmpfs. Guardian work deadline remained **5 seconds**, with its existing separate cleanup grace. Actual inspect facts are retained for every run. No project, credential, socket or device mount was supplied.

Body2MiB, text128KiB, depth64 and blocks2048 limits were unchanged. The copied extractor bytes are identical to accepted source SHA-256 `5201f7b93b1ff6d650d4a035873663f7451112e441e084d303b2e2d0147fdca3`; the wrapper sets the event constant in its private process and records counters. Maintained extractor hashes before/after match in [source-unchanged.json](document-event-prototype/source-unchanged.json).

## Measurements

| Input / event cap | Outcome | Observed events | Extraction wall time | Peak Python RSS |
| --- | --- | ---: | ---: | ---: |
| Official page /10,000, three runs | Rejected at event limit | 10,001 before refusal | 0.040–0.043 s | maximum23,332 KiB |
| Same page /40,000, three runs | Complete | 11,442 | 0.046–0.048 s | maximum23,376 KiB |
| Comment-heavy exact10,000 /10,000 | Complete, one visible span | 10,000 | 0.018 s | 22,996 KiB |
| Same construction +1 /10,000 | Rejected | 10,001 | 0.020 s | 23,124 KiB |
| Comment-heavy exact40,000 /40,000 | Complete, one visible span | 40,000 | 0.090 s | 23,288 KiB |
| Same construction +1 /40,000 | Rejected | 40,001 | 0.080 s | 23,216 KiB |
| Depth64 /65 at40,000 | Exact cap passes; +1 rejects | 129 /65 | under0.001 s | maximum23,168 KiB |
| Visible text131,072 /131,073 bytes at40,000 | Exact cap passes; +1 rejects | 3 /2 | under0.001 s | maximum23,144 KiB |
| Blocks2,048 /2,049 at40,000 | Exact cap passes; +1 rejects | 6,144 /6,147 | 0.020 /0.019 s | maximum23,332 KiB |

All **16 fresh-container measurements** matched their expected result. Official-page maximum nesting depth was20; pre-normalization visible text was41,424 bytes. Complete spans hash: `14d4153f4ce19c76b10bf2f1acbcad5c284d655c0d5b7ebcae1dfefeb1f4177e`. All three40,000-page runs match. Guardian end-to-end times for those page runs were0.403–0.503 s, including container/cleanup overhead.

Peak RSS is `resource.getrusage(RUSAGE_SELF).ru_maxrss` for the instrumented Python process, including its imports/input, **not container cgroup peak memory** or total host impact. The wrapper observes parser events/depth and adds modest overhead; this is not a throughput benchmark. Maximum measured RSS across the matrix was23,376 KiB (about22.8 MiB). The most expensive measured extraction took0.090 s. No claim is made that this matrix exhausts parser-complexity attacks; body, depth, text, process memory and guardian deadlines remain essential independent limits.

Every owned measurement container was confirmed absent using a successful daemon list query; final prototype-label query returned none. Failed baseline trials are measurements, not successful extraction or source-backed model answers.

## Reproduction and next decision

[probe.py](document-event-prototype/probe.py) reconstructs accepted source from `2049361`, fetches only the approved URL when its private body is absent, and runs [measure.py](document-event-prototype/measure.py). [results.json](document-event-prototype/results.json) contains all observations, elapsed times, source identities, exact executor facts and cleanup results. Raw frozen body and private reconstructed source remain at `.gflo/document-event-prototype/`; no duplicate source tree is tracked. Later runs write separate timestamped result directories. A fresh fetch can produce a different source version and must retain its own hash/provenance.

```sh
python3 .scratch/autonomy/document-event-prototype/probe.py
```

Requires the existing pinned local image; the script does not pull. Recommend a later separately versioned change that evaluates40,000 events while preserving all other bounds, renews affected extractor/receipt identity and repeats independent qualification. This experiment does not repair quote-copy errors, establish semantic answer quality, resolve the cohort oracle overconstraint, or accept full Stage4.
