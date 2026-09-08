# Stage 0–1 implementation

Authorized first scope: target verification and one durable task-to-evidence loop ending at the twelve-task diagnostic live pilot. The planning decision is [resolved](issues/12-plan-the-staged-implementation-and-validation.md); later stages remain evidence-dependent.

- [Verify the RTX 5090 execution target](issues/13-verify-rtx-5090-execution-target.md) — resolved for the fixed Python broker and conservative serving profiles.
- [Build the durable Work ledger](issues/14-build-durable-work-ledger.md) — resolved: typed contracts, immutable history, fenced leases, evidence-bound acceptance and CLI recovery.
- [Publish and reconcile immutable artifacts](issues/15-publish-and-reconcile-artifacts.md) — resolved: atomic publication, verified byte references and non-destructive crash reconciliation.
- [Build the execution broker and trusted gates](issues/16-build-execution-broker-and-gates.md) — resolved: bounded containers, separate clean process gates, qualified controls and recovery.
- [Compose bounded Worker views and model turns](issues/17-compose-worker-views-and-model-turns.md) — resolved: bounded provenance, typed proposals, local transport and passing real coding smoke.
- [Connect the durable task-to-evidence loop](issues/18-connect-durable-task-to-evidence-loop.md) — resolved: prepared CLI runs, bounded tools/retries, recovery and live acceptance.
- [Run the twelve-task live pilot](issues/19-run-twelve-task-live-pilot.md) — resolved: 12/12 on eager and graphs; [results](pilot-results.md).
- [Investigate slow local decode](issues/20-investigate-slow-local-decode.md) — open: approximately 10 output tokens/second; decode dominates the measured request.

Target verification and deterministic ledger work can progress independently. Dependencies govern build order; real-model and isolation gates cannot be replaced by mocked results.

## Current implementation checkpoint

The prepared durable loop is complete. The default suite passes 162 tests and 23 subtests; eight optional broker tests were qualified earlier. The live CLI run accepted a local-model repair through three trusted cases, and resume preserved identical history. [The twelve-task pilot](issues/19-run-twelve-task-live-pilot.md) is unblocked. A bounded [decode-performance investigation](issues/20-investigate-slow-local-decode.md) is also ready: replay ruled out client overhead/queueing as the main cause. See [loop verification](loop-verification-results.json).

The working default remains **vLLM**, with the qualified 16K service running on the RTX 5090. Neither engine was optimally tuned; the [bounded tuning review](serving-tuning-review.md) defers optimization until representative Worker turns exist. [Comparison and evidence](serving-comparison.md) preserve the SGLang alternative and remaining coding/isolation limits.

Latest: the twelve-task pilot is complete. Graph-enabled vLLM is running for development, with approximately 5x lower median generation latency on this workload. Follow the handoff for its explicit profile; earlier eager-profile statements above are historical. Task 20 retains recovery qualification and further bottleneck diagnosis.

## Stage 2 entry — 2026-09-08

Graph serving lifecycle qualification passed; [task 20](issues/20-investigate-slow-local-decode.md) is resolved within its bounded scope. [Cumulative Attempt reporting](issues/21-report-cumulative-attempt-cost.md) is implemented and verified against live pilot evidence. Next: [integrity/recovery campaign](issues/22-expand-integrity-and-recovery-campaign.md), then the predeclared held-out atom campaign. Stage 3 integration remains dependent on this evidence.

Stage 2 recovery increment: active model-request death/recovery/resume passed with retained failed history and unknown cost. [The frozen coverage matrix](integrity-matrix-v1.md) exposes outstanding disk admission and other variation gaps. Next implement isolated disk-reserve admission/fault handling; do not advance Stage 3 on this single result.

Storage admission now exists as an explicit runtime reserve setting. Bounded storage faults and resume checks pass; SQLite automatic rollback error masking was fixed. Commit/fsync exhaustion and remaining integrity variations are next. No full Stage 2 exit claim.
