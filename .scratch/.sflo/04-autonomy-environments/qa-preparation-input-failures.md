# Preparation input-failure QA

**PASS for bounded input-failure scope**, candidate `25f75c3275739cc7cc2a4fc5a4e16580b81511d1`. Independent s-qa; no external network target contacted.

| Control/failure | Observed outcome |
|---|---|
| Valid acquisition control | Frozen local 16-wheel set, each checked against approved artifact hashes, feeds the real preparer. Real offline Docker assembly, smoke and publication succeed. |
| Missing artifact | Omit one file from acquisition stream: exact-set check rejects before assembly/publication. |
| Corrupt artifact | Replace one file body: artifact hash check rejects before assembly/publication. |
| Approved lock mismatch | In a disposable recipe copy, alter one hex digit of a valid-length requirements hash. Real offline pip reports expected versus actual SHA256 mismatch; preparation rejects. |
| Prior-good preservation | After each preparation failure, every published file hash is unchanged and the original receipt still resolves with its original hash. No additional reusable snapshot exists. |
| Fetch positive control | Exact-length, exact-hash body returned; connection closed. |
| DNS/connection timeout | Synthetic DNS timeout propagates before connection creation. Numeric connection timeout uses configured 10s socket timeout and closes raw socket. |
| Non-200/redirect/declared excess | 503, 302 and oversized Content-Length all reject before any body read; connections close. |
| Truncation/actual excess/hash | Short body versus declared length, undeclared oversized body and wrong digest all reject; connections close. |

Complete evidence: [probe](qa-preparation-input-failures/probe.py), [results](qa-preparation-input-failures/results.json), [log](qa-preparation-input-failures/probe.log). Initial malformed-length lock trial is separately preserved in `initial-malformed-lock-results.json`; final probe uses a syntactically valid 64-hex hash mismatch.

```sh
python3 .scratch/.sflo/04-autonomy-environments/qa-preparation-input-failures/probe.py
```

Acquisition is replaced only inside the disposable probe process with tar bytes from `.gflo/environment-locks/python-api/wheels`; offline assembly and publication remain actual product code. Recipe changes are confined to a private copied recipe directory. Fetch tests use in-memory response/socket/DNS doubles; the logged public numeric address is synthetic and was never contacted. DNS timeout evidence proves propagation, not an intrinsic deadline in getaddrinfo; real outer guardian deadline/cancellation behavior is covered by [lifecycle QA](qa-preparation-lifecycle.md).

This representative Python lock/assembly path complements prior successful Node preparation; no repeated Node fault matrix or external outage simulation. No maintained edits, protected fixture changes, model/GPU/rig calls, or Stage 3 acceptance claim.
