# Actual rig document-answer semantic QA

**PASS for both frozen questions and saved offline replay.** Independently assessed candidate `20493612b62de19a5e4dbb713803abd8a9667b0b`, v2 manifest `9c01da103e9f145bfc426e4a4c3f02780b85a845594a4716d1437d36c413cb3c`. Manifest source hashes match that commit; trial contract matches `41c257bcb0a2ed955dffa047c75b0dcef3712a88eab8fb1bd0a8a3a516fc846e`. This is a first-slice answer/replay verdict, not full Stage4 acceptance.

## Independent semantic findings

| Answer | Assessment |
|---|---|
| Default and compact separators | Complete: gives `(', ', ': ')` for indent=None, `(',', ': ')` for non-None, and compact `(',', ':')`. Claims cite spans73/173, whose exact excerpts directly support these facts. “Eliminates whitespace” is supported in the separator-whitespace context of the question and cited documentation; it is not treated as a guarantee to erase string-content or indentation whitespace. |
| Extra version claim | Verified rather than ignored: spans77/174 explicitly identify Python3.4 as introducing the non-None-indent default change. Both exact excerpts match the saved extracted evidence. No unsupported additional claim found. |
| Future Python3.20.0 date | Correct `insufficient_evidence`, empty claims, no fabricated date/citation. The frozen page provides no Python3.20.0 release date. The reason accurately identifies the limited JSON-module documentation source. |

Six separator-answer citations have exact evidence-ID/span/excerpt matches and semantically support their associated claims. Display URL comes from receipt. Both answers retain historical-snapshot qualification, source-version label and retrieval time `2026-10-02T15:00:44.248940+00:00`; no present-day freshness or exact runtime-patch claim.

## Measured execution and replay

- One recorded attempt per question: supported **30.996s**, insufficient **14.849s**; complete harness **47.819s**. Response usage: 10,100 prompt/888 completion tokens and 10,096 prompt/262 completion tokens; both finish with `stop`.
- Reconstructed each exact request from frozen evidence/question using candidate code; hashes match request sidecars and answer receipts. Recorded limits: 2048 output tokens, medium reasoning/512 thinking budget, 120s request timeout, 65,536 response bytes, no tools. Raw responses match saved answer receipt response hashes.
- Serving ID/image/command digest match pre/post; model alias `flash-next-coder`, context98,304, Q4_0 K/V cache, parallel1. These are captured rig facts, not a new live inspection by this reviewer.
- Actual replay executor receipt shows Python3.12.13 pinned image, runc/network-none, nonroot, read-only root/source, bounded resources and only trusted gflo source plus owned store mounts. No config/key/GPU/socket mount. Replay exits0 in **0.501s**. Both answers/provenance match saved output except allowed current age; all five stored record-file hashes independently match the recorded before/after inventory, excluding the lease.

## Evidence and reproducibility

Durable compact trial artifacts: [rig-trial](rig-trial/), especially `separators-answer.json`, `unsupported_future_date-answer.json`, both request/response sidecars, `evidence.json`, `receipt.json`, `offline-replay.json` and executor/execution receipts. Full immutable record store remains `.gflo/document-rig-trial-1/store`.

Independent [verification script](qa-rig-documents/verify.py), [results](qa-rig-documents/results.json), [log](qa-rig-documents/verify.log):

```sh
python3 .scratch/.sflo/05-autonomy-documents/qa-rig-documents/verify.py
```

No new model, network or rig calls; no source/answer changes. This review verifies retained evidence and semantic support, not a repeat trial or unseen-question generalization. Failures from earlier candidates remain separate and unchanged.
