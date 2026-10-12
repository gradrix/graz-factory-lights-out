# Candidate 1 independent QA

Verdict: **repair required**. Frozen root `/tmp/gflo-review-candidate1`; identity `e46e8c0ea1f0494dc1bc36c8243541d5d49e6eb9d4a56c08bc20a48d19cab439`. All manifest file hashes matched. Scope: focused runner/sandbox QA against the frozen initial acceptance and fresh local core decisions. No maintained files or rig changed; no live model used.

| Condition | Evidence and result | Verdict |
|---|---|---|
| Repair from failure, retained work, bounded attempts, source preserved, patch export | Existing runner tests exercise all; nine total tests pass in 1.822s | Pass |
| Frozen acceptance tampering rejected | Existing test passes | Pass |
| Crash after published verification | Existing test recovers without repeating worker | Pass |
| Crash before attempt DB commit | Actual child process exits 77 immediately after attempt directory creation; resumed runner raises FileExistsError. Identical clean control accepts | Fail |
| Accepted candidate integrity | Clean accepted control returns accepted; edit accepted workspace app.py to broken content, resume still returns accepted | Fail |
| Practical isolation | Installed pinned image: outbound connection fails, host test secret absent, Docker socket absent, acceptance absent from worker mount, root filesystem write rejected | Pass |
| Verification mounts and command timeout | Existing real Docker test rejects workspace write and terminates timed command | Pass |
| Controller death cleanup | Actual SIGKILL leaves container writing workspace; explicit cleanup stops writer | Boundary / recovery ordering gap |

## Required repairs

1. **Resume cannot recover an early crash.** `runner.py`, attempt directory creation precedes the transaction recording its number. An abrupt exit leaves the next directory present with the old DB counter. Every resume repeats `mkdir` and fails before the exception handler. Make preparation resumable while preserving attempt history. This is confirmed using process death, not just a hand-created directory.
2. **Terminal acceptance can become stale.** `resume` returns accepted/exhausted before checking the saved candidate fingerprint. An operator can receive accepted status for workspace content that was never verified. Validate accepted artifact identity on resume or clearly return acceptance bound to immutable output. The probe proves clean-control acceptance and mutated-candidate acceptance; original source remains unchanged.

## Other observations

An orphan container survives abrupt controller death and keeps changing files. Production worker and verifier cleanup remove these containers, but the runner fingerprints the workspace for attempt input before worker cleanup. Move cleanup ahead of recovery inspection to avoid racing retained writers. No false acceptance from this race was demonstrated; final verifier cleanup is present.

The implementation has four direct modules and no framework hierarchy; its SQLite ledger, private Git snapshot and separate acceptance mount serve concrete requirements. No removal-worthy architecture found in this bounded review. Nine tests are thin coverage for crash transitions; focused fault injection adds more value than another abstraction. The frozen candidate contains no README or rollback guide despite the release contract, and this review does not establish measured coverage, live-model competence, doctor readiness or the three required live task scenarios. These remain release gates, not inferred passes.

## Reproduction

```sh
cd /tmp/gflo-review-candidate1
python3 -m unittest discover -s tests -v
python3 /tmp/gflo-qa-candidate1/probes.py
python3 /tmp/gflo-qa-candidate1/crash_probe.py
python3 /tmp/gflo-qa-candidate1/orphan_probe.py
```

Complete independent probe programs are saved at those paths. General probe output is `/tmp/gflo-qa-candidate1/results.txt`. Probe programs exit zero when they successfully reproduce the recorded observation, including required isolation rejections. The crash script prints `RECOVERY_ASSERTION_PASS False` for its clean control and `RECOVERY_ASSERTION_FAIL True` for the interrupted case. Docker image: `sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578`.
