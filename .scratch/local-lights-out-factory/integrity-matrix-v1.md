# Integrity campaign matrix v1

Frozen scope: ten categories, five variations each. This is the prospective campaign
matrix, not a passing campaign result. Existing tests provide baseline evidence;
all fifty variations still need explicit campaign receipts and recovery assertions.
No category can pass by borrowing another category's aggregate count.

Common invariants: no false/duplicate acceptance, no lost accepted history, no
unauthorized writes. Transient faults require bounded recovery or an evidence-backed
terminal exception. Preserve every failed run. Default test lease windows are driven
by a controlled clock; live model request deadline is 120s and serving recovery 300s.
No destructive host resource exhaustion is permitted.

| Category | Five required variations | Existing evidence | Remaining qualification |
|---|---|---|---|
| Missing/skipped tests | absent receipt; failed receipt; inconclusive receipt; omitted mandatory case; empty/malformed gate report | `test_missing_or_nonpassing_gates_never_accept`, gate plan binding | Explicit case/report bypass fixtures and five campaign receipts |
| Forged success | candidate prints PASS; wrong validator digest; wrong candidate digest; wrong attempt receipt; edited artifact bytes | ledger mismatched receipt and artifact corruption tests; trusted stdout comparison | Named five-variation campaign with recovery |
| Stale inputs | source digest; input revision; changed dependency; stale model response; combined candidate base | worker freshness, ledger preconditions/dependencies | Combined-base fixture requires integration support; no scope claim yet |
| Duplicate/expired delivery | duplicate claim; duplicate receipt; duplicate accept; late result after expiry; expired final retry | ledger concurrency, expiry and idempotence tests | Freeze five receipts and assert recovery/history in each |
| Worker death | before request; during read expansion; during candidate execution; after candidate publication; before gate dispatch | controller interruption and live broker interruption tests | Distinguish worker, controller and broker death explicitly |
| Model-server death | before models lookup; during tokenize; active prefill/decode request; between read/edit turns; repeated failure exhausts budget | transport timeout tests; idle serving recovery; new active request harness | Execute all five and account for unknown tokens |
| Gate-runner death | before launch; during case; after case before receipt; between mandatory cases; after receipt before acceptance | broker interruption, validating resume, inconclusive gates | Five explicit death/recovery receipts |
| Controller restart | artifact staging; publication before ledger bind; candidate commit; gate receipt commit; acceptance commit | artifact subprocess crash and controller process-death tests | Consolidate five windows with resume invariants |
| Disk reserve | admission below reserve; staging ENOSPC; publish/link ENOSPC; ledger commit ENOSPC; low reserve on resume | Configurable admission; isolated staging/link ENOSPC; SQLite page-cap rollback/reopen; fresh/interrupted resume | Deterministic commit-boundary/fsync injections added; complete campaign receipts and physical-I/O limits remain explicit |
| Authority escape | path traversal; prohibited file edit; symlink escape; host/socket access; forged control receipt | worker scope tests, artifact nonregular files, live broker isolation, forged lease gate test | Five named isolated campaign receipts |

The matrix is deliberately explicit about unsupported combined-base integration and
remaining storage-fault windows. These gaps prevent claiming the full integrity campaign.
Do not silently drop them to advance the held-out or integrated-change support claim.

## Active-request increment

`scripts/check_inflight_recovery.py` freezes its plan before scoring, waits for the
server's active-request metric, then kills the owned internal engine. A transport
failure must retain an unaccepted Attempt with no candidate. After automatic serving
recovery, the harness invokes the ordinary controller resume path. Passing requires
trusted gates, unchanged first-Attempt history, idempotent repeated resume, and no
missing/corrupt referenced artifact. This is one variation, not five independent cases
or a production supervisor. The generated workload remains a development fixture.

## Storage increment

Configurable reserve admission is implemented with zero as the development default.
`tests/test_storage.py` covers available-space boundary/pending bytes, low reserve
before staging, staging/link ENOSPC and SQLite automatic rollback/reopen using a
bounded database page cap. Controller tests cover fresh and interrupted low-space
resume without new model work/history mutation. A real SQLITE_FULL fixture exposed
and fixed a redundant rollback that masked the original error. The SQLite fixture
forces allocation failure during a transaction, not specifically during COMMIT; the
commit variation remains open. This is not a full storage-category pass.

## Commit and sync increment

Six new deterministic cases cover file fsync, publication-directory fsync, cleanup-directory fsync, combined link/cleanup errors, pre-acceptance-COMMIT failure and lost post-COMMIT acknowledgment. Real SQLite state and immutable artifacts are retained; commit errors are injected at the Python connection boundary, not inside a custom SQLite VFS. Reopen/resume produces exactly one acceptance with no repeated model/gate work. Publication retry succeeds after sync faults are removed. A cleanup-error masking bug was fixed by retaining the primary exception with a secondary cleanup note. These tests do not establish physical power-loss durability or complete all fifty campaign variations.

## Recorded deterministic subset

[Subset verification](recovery-subset-verification.json) records 21 passing cases: five model-protocol failure windows, five gate-controller interruption windows, two acceptance commit windows and nine storage checks. `scripts/run_recovery_checks.py --output NEW_DIRECTORY` freezes identities before execution and records JUnit receipts, failures/skips, timing and exact case counts. Each group fails if a case is missing or skipped. This is a subset report, not the original fifty-variation campaign.

Model windows cover lookup, tokenization, generation, loss between read/edit turns and persistent failure exhausting the original budget. LocalModel evidence publication and parsing run against deterministic protocol replies; no live server dies in these five cases. Gate windows cover before launch, loss of an execution result, between mandatory cases, before receipt and after receipt. KeyboardInterrupt injects controller-side loss; actual container process-death coverage remains distinct. Resume uses the original candidate, reruns incomplete gate cases and reuses durable complete receipts.

## Live execution-process death

[Four live cases](execution-death-verification.json) cover candidate/validation commands killed with SIGKILL or explicit handled SIGTERM. The broker execs the fixture as PID 1; exact command identity and exit codes are checked. Candidate smoke remains advisory and can be followed by passing mandatory validation in the same Attempt. Validation death fails its gate and requires a fresh Attempt. Scripted proposals isolate this experiment from LLM behavior. These four executions do not fill all worker/gate lifecycle windows or qualify arbitrary signal handlers.

## Actual controller process death during validation

[Five live SIGKILL windows](controller-death-verification.json) now exercise the coordinating process disappearing before launch, during a running validation command, between cases, before receipt commit and after receipt commit. These supplement the previous injected KeyboardInterrupt checks. No model regeneration or duplicate acceptance occurred on resume; original event prefixes stayed identical. Created/running leftovers in the first two windows were recorded before broker reconciliation and absent afterward. This establishes those five windows with a scripted candidate; full category/campaign promotion still requires consolidating all original matrix rows.
