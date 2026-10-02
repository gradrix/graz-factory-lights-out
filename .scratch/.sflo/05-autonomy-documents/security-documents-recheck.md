# Independent security recheck: document evidence repairs

2026-10-02. Skill: security-check. **Frozen candidate `2049361`**, manifest SHA-256 **`9c01da103e9f145bfc426e4a4c3f02780b85a845594a4716d1437d36c413cb3c`** ([retained manifest](security-documents-recheck/candidate.json)). Assessed `gflo/documents.py` SHA-256: `ac39b8dab36e52561f1e08206096ca6602cf874b7b8c65af31fbcfe4dbc1a169`.

## Outcome

**PASS within the documented first-document-slice security boundary.** Both independently reproduced findings, D1 failed-publication reuse and D2 missing cleanup-recovery fencing, are repaired. No new actionable defect was identified in this focused recheck. The original [REPAIR REQUIRED report](security-documents.md), candidate `dc60ee3`, probes and red results remain preserved.

## Coverage

All **27 independent repair probes passed** against the exact frozen source. All nine manifest file hashes match before and after assessment ([before](security-documents-recheck/hashes-before.json), [after](security-documents-recheck/hashes-after.json)). The probe was also run through reconstruction from `2049361`, confirming the retained source identities and reproduction path.

This reviewer used source/diff inspection, controlled executor results, temporary stores and actual disposable publishing-child SIGKILL. No containers, network requests, model calls, GPUs, shared-service changes or maintained-file edits were performed. Builder full-suite and actual local/rig container runs are separately attributed below.

### D1: private preparation and final atomic publication

Personally inspected the repair: staged validation, pending-marker removal, staging sync, cancellation/deadline checks and response preparation all precede the final staging-to-ID rename. That rename is now the visibility commit point. Successful callers set their staging reference to `None`, avoiding postcommit staging stat/cleanup; answers prepare replay output before committing.

Independent [probe/results](security-documents-recheck/results.json) establish:

- Normal acquisition succeeds and preserves prior good.
- The original postcommit sync/retirement fault locations are no longer reached. Instrumented controls refuse any sync on a published ID or retirement attempt.
- First and final staging-sync failure, pending-marker-unlink failure, staged-validation failure and final commit-rename failure leave no new public ID. Every prior published file hash remains unchanged and its receipt resolves.
- Final staging-sync failure plus recursive staging-cleanup failure leaves only private unusable scratch. New acquisition refuses until explicit cleanup; recovery then permits success.
- Cancellation becoming true at final staging sync prevents commit and preserves prior good.
- Instrumented postcommit filesystem reads/stat/cleanup are not reached. Answer publication similarly performs no postcommit evidence reread; saved replay remains valid.
- **Actual process death:** a forked publishing child receives SIGKILL immediately before final rename: no new public ID, private stage blocks new work until recovery. SIGKILL immediately after the actual rename leaves one complete resolvable record, as expected for an operation whose atomic commit has occurred. Prior good survives both cases.

The repaired guarantee is **atomic visibility for ordinary process failure**, not power-loss persistence of the final parent-directory rename. The final rename is deliberately not followed by fallible fsync. This limitation is explicit in the repaired documentation; these probes do not establish filesystem recovery after host power loss.

### D2: cleanup uncertainty is fenced before launch

Personally inspected the repair: an exclusive/no-follow `.cleanup-required` marker is installed before invoking the executor. Only a zero executor result removes it. The code no longer attempts to infer cleanup truth from a timeout/cancellation primary exit code or human diagnostic text.

Independent probes cover **seven uncertain outcomes in both fetch and extract phases**: exit 1, 124, 125 and 130; `RuntimeError`; `OSError`; and cleanup `TimeoutExpired`. For each, the marker exists when the controlled executor is invoked, remains after failure, and prevents retry before another executor call. Every prior published file hash remains identical and the prior receipt resolves. Injected explicit-cleanup failure retains the fence; successful controlled cleanup removes it and permits a conforming acquisition.

Consequently, even an ordinary helper rejection with successful actual container removal requires explicit cleanup. This is the documented conservative behavior because the unchanged guardian does not separately attest cleanup success on all error outcomes. It is not a new permission request or silent automatic retry.

## Carried-forward and external evidence

Only `gflo/documents.py`, its store tests and usage documentation changed from the original nine-file candidate. URL/DNS/TLS policy, framed fetch, offline extractor, answer request/child, worker byte bounds and CLI are byte-identical to the original assessed candidate. Earlier passing [security controls](security-documents/coverage-results.json), actual answer-owner SIGKILL and the unmodified [120.005-second fake-client deadline](security-documents/deadline-result.json) therefore remain applicable to those unchanged seams; they were not relabelled as new v2 executions.

The independent [functional QA report](qa-documents.md) remains relevant to unchanged fetch/extraction/answer/replay paths, with the documented recovery behavior superseded by this repair. The builder reports **119 tests and 86% branch-aware coverage** in [repair verification](builder-repair-v2.md); that full suite was not rerun by this reviewer.

I also read [actual rig lifecycle v2 results](rig-lifecycle-v2.json): cancellation and owner death observed an owned running container, then no remaining container or reusable record; both retained the marker, owner death retained private staging, and explicit cleanup left only `.lock`. This is implementation-owner measured real-Docker evidence, not my own independent run and not an actual daemon outage. My fault probes separately establish the controller's conservative response to simulated cleanup uncertainty.

## Limits and next gate

Controller-owned store/recipes/configuration and a trusted Docker daemon remain assumptions; no hostile concurrent privileged host writer is modeled. Bridge acquisition remains a trusted fixed-client boundary, not a general network firewall. Citation checks establish exact source provenance, not logical support or model honesty. Real model answers and insufficient-evidence behavior still require independent semantic evaluation; no inference was used for this verdict.

No real shared-daemon outage, hostile public-site campaign, container/kernel escape, dependency vulnerability audit, or power-loss durability was tested. These exclusions do not reopen D1/D2, but bound this verdict. Full Stage 4 research/browser acceptance remains separate and unaccepted by this report.

## Reproduction

[Probe](security-documents-recheck/probe.py) reconstructs trusted `2049361` with Git into ignored `.gflo/security-documents/9c01da10/`, verifies the frozen manifest and all nine source hashes, and runs only local controls. No duplicate source tree is required in tracked evidence. Linux/Python with fork and local Git history are required; only disposable child processes are signalled.

```sh
python3 .scratch/.sflo/05-autonomy-documents/security-documents-recheck/probe.py
```

The retained [results](security-documents-recheck/results.json) identify every check. A rerun writes that result file again; preserve its current copy if exact temporary identities matter.
