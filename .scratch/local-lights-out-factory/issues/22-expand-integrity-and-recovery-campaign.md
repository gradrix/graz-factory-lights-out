# Expand Stage 2 integrity and recovery coverage

Type: task
Status: claimed
Blocked by: 20, 21

## Scope

Inventory existing fault tests against the accepted ten-category integrity contract
in [evaluation thresholds](10-set-feasibility-and-evaluation-thresholds.md).
Add missing fixtures and recovery paths in bounded increments. Start with model
server loss during a Work atom: retain transport failure, prevent acceptance,
recover service, resume with fenced evidence and verify the accepted output.
Include interrupted requests and missing token usage in cumulative reporting.

## Acceptance

Freeze a versioned matrix with at least five distinct variations for each required
category before claiming the integrity campaign passed. Existing idle graph-server
restart evidence alone does not satisfy Work-atom recovery. No false or duplicate
acceptance, lost accepted history or unauthorized writes. Preserve failed runs and
bounded recovery deadlines. Use isolated disk-reserve fixtures, never host exhaustion.
Every category must pass independently; document gaps instead of an aggregate pass.

After integrity work and context-policy fixes, freeze the forty-task, three-repeat
held-out atom campaign under the original 108/120 overall and 24/30 per-class targets.
Do not tune on scored cases. Dependency integration remains subsequent Stage 3 work.

## Progress — active-request recovery increment

Published [matrix v1](../integrity-matrix-v1.md) with five prospective variations in each of ten categories and explicit coverage gaps. Added the repeatable active-request engine-death harness. The live run observed one running request before SIGKILL, retained a retry-ready HTTP 500 failure with no candidate, automatically recovered serving, then invoked ordinary controller resume. The task accepted on Attempt 2 with independent gates; first-Attempt history and repeated accepted resume stayed identical. Unknown interrupted-token usage remains explicit. [Verification](../inflight-recovery-verification.json).

Task remains claimed: one model-server variation passed, not the fifty-variation campaign. Next bounded implementation is disk-reserve admission and isolated storage-failure fixtures, followed by the remaining recovery matrix. The held-out task campaign has not begun.

## Progress — storage admission and bounded faults

Added optional `--reserve-bytes`/`WorkLedger(reserve_bytes=...)`, database/artifact admission before dispatch/resume, and artifact payload checks before staging. Disabled by default for development; qualifying campaigns must declare a reserve. Isolated staging/link ENOSPC and bounded SQLite page-limit faults preserve history and recover. SQLITE_FULL revealed a real error-masking bug: the transaction wrapper now rolls back only while a transaction remains active. Fresh and interrupted low-space runs preserve history and resume after removal. Commit/fsync exhaustion and remaining matrix variations stay open; no full campaign pass claimed.

## Progress — commit and fsync windows

Added six deterministic recovery cases (three fsync windows, combined publication/cleanup error, pre-COMMIT failure, lost post-COMMIT acknowledgment). Commit fixtures use a real ledger with injected connection-boundary errors. Resume retains one acceptance and does not repeat completed model/gate work. Fixed cleanup errors masking the original artifact-publication failure; secondary cleanup errors are now exception notes. Full matrix qualification remains open. Next consolidate category receipts and extend model/gate interruption variations; do not treat these injections as physical power-loss tests.

## Progress — model/gate interruption subset

Five model protocol windows and five gate interruption windows pass, including evidence retention, stale lease fencing, bounded persistent failure and idempotent resumed acceptance. Added a frozen, repeatable 21-case subset runner with per-case JUnit receipts and source hashes; [verification](../recovery-subset-verification.json). Full suite: 191 tests, 25 subtests, eight optional Docker skips. Tests use deterministic protocol/interrupt injection, not five live process deaths. Full integrity campaign remains open. Next reconcile remaining matrix variations into explicit executable fixtures, especially actual gate/worker death and combined-input coverage, before held-out scoring.

## Progress — live execution death

Four live cases passed: candidate and validation execution under SIGKILL and handled SIGTERM. The injector verifies the exact fixture runs as PID 1 before signaling. Retained results prove exit 137/143 on the targeted container. Failed validation triggers a fresh Attempt; failed candidate smoke does not waive mandatory clean validation. Repeated resume preserves exactly one acceptance, artifacts audit clean, owned containers cleaned. Uses a scripted proposal to isolate execution recovery, not a new model-quality score. [Verification](../execution-death-verification.json). Earlier four injector runs are retained as failed qualifications. Full matrix remains open.

## Progress — abrupt controller process death

Five actual SIGKILL windows passed against real SQLite/artifacts and Docker: before validation launch, during a running case, between cases, before gate receipt commit and after it. Parent observed child exit -9 in each case. Resume retained original events, used the existing candidate without another proposal, reran incomplete validation or reused completed receipts, and produced exactly one acceptance. The first two windows left an owned container and reconciliation removed it. [Verification](../controller-death-verification.json). Scripted proposal, no inference-quality measurement; no unattended supervisor added. Next consolidate the original fifty-variation matrix against these receipts and identify only the genuinely uncovered cases.

## Progress — original matrix consolidation

Full suite with real Docker checks: 202 tests and 25 subtests passed, no skips. Added explicit later-case omission and empty/malformed plan rejection tests. [Coverage report](../integrity-coverage.md) maps all fifty rows to receipts: 39 covered, 10 partial, one unimplemented. This is a retrospective mapping, not a full campaign pass. Exact remaining fixtures are listed; combined-input integration stays open rather than being silently downgraded to a single-source freshness test. Next close evaluator-output/forged-success and remaining lifecycle windows, then address combined-input support.

## Progress — evaluator hardening and precise commit windows

Found and fixed a gate boundary gap: expected stdout from a mismatched execution could previously pass. Runner v2 now revalidates typed execution identity, qualified image, clean-container uniqueness within a gate, strict bounded outputs and duration; malformed reports produce retained inconclusive outcomes. Explicit forged success stdout fails. Recovery after malformed/wrong/replayed reports passes without false acceptance. Also qualified injected commit SQLITE_FULL and actual SIGKILL after candidate commit. Enabled suite: 218 tests + 25 subtests, no skips; recorded recovery subset now 22 cases. [Verification](../evaluator-hardening-verification.json). Coverage improves to 43 covered / six partial / one unimplemented; next remaining worker/model lifecycle and dependency/combined-input rows.

## Progress — lifecycle gaps, prepared integration and held-out freeze

Five final dispatch/model lifecycle windows passed with retained failures, ordinary
resume and idempotent acceptance. Prepared integration closes dependency/base rows:
real local-model provider/two-consumer output independently validates. Enabled suite:
234 tests + 25 subtests, no skips. [Verification](../prepared-integration-verification.json).
All fifty rows now have scoped accumulated evidence; a fresh same-build campaign is
not claimed. Forty corrected held-out tasks are frozen for three repetitions in
`.gflo/evidence/heldout-v1-qualified/`. No scoring policy changes during the run.

## Completed frozen scoring — progression criterion failed

Forty tasks × three repeats completed: 111 gate acceptances, 109 verified after additional
probes, nine exhausted runs, two discovered false acceptances. Every numerical class/overall
target passed, but zero-false-acceptance did not. Preserve the failed qualification; it
cannot be converted into success by subsequent repairs. [Full report](../heldout-results.md).
Tasks 25/26 implement follow-up feedback and finding safeguards. This ticket remains
claimed until the unresolved qualification requirements are addressed on appropriate
fresh evidence; no fresh same-build full fault campaign is claimed.
