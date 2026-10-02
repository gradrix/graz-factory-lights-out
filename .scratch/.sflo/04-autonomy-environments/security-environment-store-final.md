# Independent security assessment: repaired environment store

Date: 2026-10-02. Skill: security-check. Frozen candidate: `edc7d7180d89599b83fe4fd507919e6e08b414b6`. Frozen `gflo/environment.py` SHA-256: `724822b9845090d0971312a765b9535a607de55d44788c664519026b226077ce`.

## Outcome

**Pass for the assessed store slice.** The failed-publication and failed-retirement findings are repaired. The pending marker prevents an interrupted or failed attempt from becoming reusable, including after the publishing process dies. No remaining actionable security defect was found within this scoped assessment. This allows integration work to proceed; it grants no complete environment-preparer or Stage 3 acceptance.

## Coverage

Completed the store-only assessment on Python 3.10.12 against exact files reconstructed from the frozen commit. All **68 independent probes** and **seven frozen maintained store tests** passed. The earlier findings and their evidence remain preserved in `security-environment-store.md` (`1506abf`) and `security-environment-store-recheck.md` (`6dd3556`).

Verified the final publication behavior:

- A root-directory-fsync failure after rename retires H. A concurrent separate resolver is refused while publication holds the exclusive lease; afterwards H is absent and G remains usable.
- A failure during final private verification also retires H.
- If directory synchronization and retirement rename both fail, H retains `pending`. A new store instance rejects H, and a new publication attempt producing the same H cannot reuse it. G stays unchanged.
- If recursive cleanup fails after retirement, only private staging remains. H cannot resolve; another preparation remains blocked while cleanup continues failing. Reconciliation succeeds after removing the fault.
- Failure to remove the final pending marker retires the candidate and leaves H non-runnable.
- Cancellation becoming true during final root synchronization is observed before marker removal. H is retired and G stays unchanged.
- **Actual process-death probe:** a forked publishing child receives `SIGKILL` immediately after post-rename root synchronization, before marker removal. The parent verifies the child died from signal 9, the publication lock was released, H still has its pending marker, a new resolver rejects H, a same-ID publication retry rejects it, and G remains usable. This probe exercises only the local store process; it starts no producer or executor.
- Successful publication removes the marker, resolves through a new store instance, and supports idempotent same-ID reuse. Concurrent shared readers remain compatible; an exclusive preparer cannot proceed while a shared lease is held.

All retained controls continue passing: exact receipt/runtime/path binding; eighteen independent tree/receipt/mode/hash tampering variants; six malformed identifiers; twenty-two archive rejection cases compatible with production limits; four earlier cancellation fences; failed/throwing/changing smoke checks; oversized receipt; pre-rename error; explicit cleanup failure; and preexisting destination symlink protection. Known-good receipt bytes and tree identity are checked after every applicable failure. The three corpus cases requiring smaller test-only transport/count/expanded limits remain covered by the separate archive assessment rather than this store seam, which uses production defaults.

## Frozen scenario coverage

| Scenario group | Store evidence | Remaining integration evidence |
| --- | --- | --- |
| Valid receipt, tree/receipt tampering, unsafe ID | Valid binding, all specified tampering dimensions, controlled receipt-ID resolution | Actual recipe execution and two fresh offline executions |
| Failed archive, publication failure, destination link | Known-good receipt retained; rejected/retired/pending candidates cannot resolve | Public preparer error propagation |
| Cancellation before publication | Five tested fences including final root synchronization | Live executor removal and cancellation propagation |
| Cancellation during transport / owner death | Cancellation observed after transport; actual store-owner SIGKILL before final commit | Interrupting blocked transport; producer and executor supervision |
| Cleanup failure blocks reuse | Private cleanup faults and failed retirement remain non-runnable; same-ID retry refuses pending H | Daemon/executor cleanup and operational reconciliation of pending final-ID artifacts |

The verification callback remains a trusted controller/preparer seam. These tests use controlled callbacks, including explicit failures and mutations; callback success is not evidence of real offline smoke execution. No model-facing callback API is part of this candidate.

## Limits and assumptions

Controller-owned storage and limits; no untrusted concurrent host filesystem writer. The pending marker's removal is the local publication commit point. Pending final-ID artifacts intentionally remain unusable until trusted reconciliation; this slice does not implement an operator-facing reconciliation workflow. Actual power-loss durability and filesystem recovery were not tested. The process-death test must not be interpreted as remote executor or daemon cleanup evidence. Fetch restrictions, runtime/device isolation, task binding, live transport deadlines and full preparer qualification remain outside this assessment.

No maintained-code edits, network calls, model calls, containers, rig operations or GPU work were performed.

## Retrievable evidence

Track only this report, `security-environment-store-final/probe.py`, and `security-environment-store-final/results.json`. The result JSON preserves the original candidate, source hash, Python version and every observation. The script reconstructs exact trusted files from Git into ignored `.gflo/security-environment-store/edc7d7180d89599b83fe4fd507919e6e08b414b6/`; no duplicate source/test/corpus trees need to be published. Reruns write separate `rerun-results.json` there and run the seven frozen maintained tests.

```sh
python3 .scratch/.sflo/04-autonomy-environments/security-environment-store-final/probe.py
```

Reproduction requires Linux with Python 3.10 or later, local Git history containing the frozen candidate, and permission to fork and signal the disposable child. It performs no network fetch. The script returns failure if any probe or maintained test fails.
