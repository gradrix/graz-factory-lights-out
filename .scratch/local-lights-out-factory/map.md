# Local Lights-Out Software Factory

Label: wayfinder:map

## Destination

Produce a research-backed feasibility verdict, architecture specification, and staged implementation plan for a Linux software Factory running Qwen3.8-27B on one RTX 5090 with 64 GB system RAM. The design must attempt autonomous end-to-end product creation, fall back safely to bounded Work atoms, and generate modular products whose structure remains comprehensible through authoritative graphs and small retrieved contexts.

## Notes

- Use the `research`, `grilling`, `domain-modeling`, and `prototype` skills as named by each ticket.
- Planning only: this map ends at an implementation-ready plan and validation strategy, not a production implementation.
- Optimize Work atoms and Product modules for the smallest context that preserves correctness; extra local inference time and token use are acceptable.
- Start validation with greenfield products, then controlled changes to existing repositories.
- The core is stack-neutral; technology support is explicit through Capability profiles.
- Source code, contracts, tests, and validated structural manifests are authoritative. Summaries and semantic indexes are navigation aids.
- Deterministic evidence is the primary approval authority. Isolated model reviews may add evidence but may not waive executable criteria.
- Autonomous recovery is bounded. Failed work is quarantined with evidence before escalation.
- The Factory may create local branches and commits. Publishing and deployment require human approval.
- Prefer primary sources, reproducible measurements, and explicit separation between vendor claims and independently observed results.
- Large greenfield and existing applications remain the target; internal modules do not require microservice deployment. Time and energy costs are acceptable, with correctness and recoverable progress taking priority over throughput. Future local models require fresh calibration.

## Decisions so far

- Implementation checkpoint: [the durable prepared-task loop](issues/18-connect-durable-task-to-evidence-loop.md) is complete, with live CLI acceptance and unchanged resume history. The twelve-task pilot is unblocked; [decode performance](issues/20-investigate-slow-local-decode.md) remains an open measured issue.

- Implementation checkpoint: [bounded Worker views/model turns](issues/17-compose-worker-views-and-model-turns.md) are complete. Two real local-model repair smokes passed trusted gates; automatic tool/retry/resume integration and the twelve-task pilot remain.

- Implementation checkpoint: [execution broker and trusted process gates](issues/16-build-execution-broker-and-gates.md) are implemented with live bounded-control/recovery evidence; [initial target qualification](issues/13-verify-rtx-5090-execution-target.md) is resolved for the fixed Python/serving profiles. Model worker views and loop integration precede the actual coding pilot.

- Implementation checkpoint: [immutable artifacts](issues/15-publish-and-reconcile-artifacts.md) now publish atomically, verify bytes before ledger transitions/acceptance, and preserve failed/orphaned evidence during read-only reconciliation. Broker and worker integration follow; this does not change the architecture decisions below.

- [Establish the single-GPU feasibility envelope](issues/01-establish-single-gpu-feasibility-envelope.md): Qwen3.8-27B is viable as one serialized NVFP4 inference worker, with 8K routine contexts, 16K justified contexts, and a provisional 32K ceiling pending exact-machine benchmarks.
- [Compare factory orchestration foundations](issues/02-compare-factory-orchestration-foundations.md): Primary-source comparison favors a minimal durable core informed by Gas City graph/reconciliation semantics and SFLO evidence-gate policy, with coding harnesses kept behind a replaceable boundary.
- [Research atomic context and code structures](issues/03-research-atomic-context-and-code-structures.md): Evidence supports separate Work and Product graphs, progressive authoritative retrieval, content-addressed invalidation, and deterministic conformance; minimal context and long-horizon modularity remain empirical hypotheses.
- [Define the autonomy and safety contract](issues/04-define-autonomy-and-safety-contract.md): A preauthorized Lights-out run has no routine human gates; automated isolation, deterministic evidence, ten-attempt atom circuit breakers, autonomous re-planning, broad sandboxed execution, and generational self-upgrades carry it to verified local completion or a terminal exception.
- [Choose the durable orchestration architecture](issues/05-choose-durable-orchestration-architecture.md): GFLO owns a reconciliation-driven Work ledger and deep orchestration modules, uses SFLO/Gas City only as design references, and must grow empirically from a thin real-Qwen walking skeleton rather than a one-shot implementation.
- [Define the Work atom and context contract](issues/06-define-work-atom-and-context-contract.md): Rich durable atom records project into minimal role-specific Worker views; adaptive 4K–32K Context policies, typed expansion, broad sandboxed tool discovery, evidence-derived retries, and ledger-owned acceptance keep weak-model work small and empirically tunable.

- [Define the Product graph and module contract](issues/07-define-product-graph-and-module-contract.md): Nested scopes with cross-scope dependency edges support compact steward views and coordinated provider/consumer migrations; large greenfield and maintenance workloads are targets, with scaling and future models calibrated experimentally.

- [Design verification and recovery gates](issues/08-design-verification-and-recovery-gates.md): Factory code owns evidence and acceptance; narrow model jobs support independent checks and autonomous repair, with small-model suitability to be measured before adding QA or hierarchy layers.

- [Select the implementation foundation](issues/09-select-the-implementation-foundation.md): Typed Python core, local SQLite/artifacts, isolated containers, and a GFLO-owned model loop start the experiment; product technologies remain profile-driven, with second-language and mixed-stack validation before support claims.

- [Set feasibility and evaluation thresholds](issues/10-set-feasibility-and-evaluation-thresholds.md): Versioned local-model campaigns measure completion, small-context fit, acceptance integrity, recovery, and scale; profile-owned quality checks include calibrated CRAP hotspots without weakening mandatory correctness.

- [Prototype the reference architecture](issues/11-prototype-the-reference-architecture.md): The walkthrough separates small worker views, checked candidates, and integrated completion; tests drive scheduler-owned diagnosis/repair, with scope planning on demand and runtime behavior still unverified.

- [Plan the staged implementation and validation](issues/12-plan-the-staged-implementation-and-validation.md): Begin Stage 0 target verification and Stage 1 durable loop/twelve-task pilot; later layers require measured evidence. See [implementation work](implementation.md).

## Not yet specified



None blocking the planning handoff. Exact serving settings and later operational values are measured outputs of the staged implementation plan.

## Out of scope

- Autonomous publication or production deployment; the destination ends with locally validated code, local branches/commits, and an implementation-ready plan.
- Training a foundation model or depending on a proprietary cloud model for core Factory operation.
- Claiming support for a technology stack without an explicit Capability profile and validation evidence.

- 2026-09-08: [Twelve-task pilot](issues/19-run-twelve-task-live-pilot.md) resolved. Both vLLM serving modes accepted 12/12; graph mode reduced median generation latency about 5x. [Evidence and limits](pilot-results.md); prospective duplicate-read instruction clarified.

- 2026-09-08: Tasks [20](issues/20-investigate-slow-local-decode.md) and [21](issues/21-report-cumulative-attempt-cost.md) resolved: graph serving restart/crash recovery qualified and cumulative retry accounting implemented. Stage 2 fault/campaign expansion is [next](issues/22-expand-integrity-and-recovery-campaign.md).

- Active-request recovery variation passed under [task 22](issues/22-expand-integrity-and-recovery-campaign.md): retained transport failure, automatic serving recovery, verified second Attempt and idempotent acceptance. [Matrix](integrity-matrix-v1.md) keeps remaining campaign gaps explicit.

- Task 22 storage increment: configurable reserve admission and bounded ENOSPC/SQLite-full recovery implemented. Fixed redundant rollback error masking. [Verification](storage-verification.json): 173 tests and 25 subtests pass; remaining matrix gaps retained.

- [Task 23](issues/23-show-worker-change-history.md): worker candidate history now has readable diffs and JSON provenance, including failed Attempts. Product Git integration remains future work.

- Task 22 commit/fsync increment: deterministic publication sync and acceptance commit/acknowledgment failures recover without duplicate work; primary artifact errors now survive cleanup failures. Full campaign still open.

- Task 22: ten model/gate interruption variations added; [recorded 21-case deterministic subset](recovery-subset-verification.json) passes. Full integrity campaign explicitly remains incomplete.

- Task 22: [four live execution-death cases](execution-death-verification.json) passed with preserved failed evidence, independent gates, idempotent acceptance and cleanup. Earlier injector failures retained. Full campaign still open.

- Task 22: [five actual controller-SIGKILL windows](controller-death-verification.json) passed with original-candidate resume, preserved event history, single acceptance and cleanup. Next consolidate original matrix coverage against retained receipts.

- [Original integrity matrix consolidated](integrity-coverage.md): all 50 rows mapped; 39 covered/10 partial/one unimplemented. Enabled suite 202 tests + 25 subtests passed without skips. Remaining work is explicitly enumerated.

- [Evaluator hardening](evaluator-hardening-verification.json): v2 binds returned execution to exact candidate/case/image and rejects malformed/replayed output; explicit recovery cases pass. Coverage now 43/50 covered, six partial, one unimplemented. Enabled suite 218 + 25 subtests passes without skips.

- [Prepared integration](issues/24-validate-prepared-integration.md): exact-base accepted edits, bounded provider contracts, independent combined gates and reviewable history. Live provider/two-consumer fixture passed; no Git promotion claim.

- [Forty-task evaluation](heldout-results.md): 109/120 verified after review, but two false acceptances block progression. All raw failures and frozen source/ledger are retained.
- [Readable validation feedback](issues/25-improve-bounded-validation-feedback.md): bounded-python-v4; seen matched repair comparison 3/3 versus 1/3, no held-out rescore.
- [Semantic gates and Acceptance findings](issues/26-strengthen-semantic-gates.md): immutable later evidence blocks reuse; deduplication repaired, version-sort repair still exhausted its declared budgets. Next diagnose semantics and strengthen contracts/gates.

## 2026-09-09 — bounded repair diagnosis

Explicit reasoning plus a 4K output reserve repaired the seen version-sort task
3/3, with broader semantic checks passing. Default policy unchanged; qualify
escalation across tasks before scaling. [Evidence](version-sort-diagnosis.md).

## 2026-09-09 — escalation qualification

[Task 27](issues/27-qualify-bounded-reasoning-escalation.md) resolved: explicit
low-effort escalation qualified 23/24 runs with no discovered false acceptances.
The inventory API slice passed; proceeding to [stateful work](issues/28-qualify-stateful-inventory-build.md).

- Stateful campaign: one complete build, second blocked at final migration, third
  unscored. [Issue 28](issues/28-qualify-stateful-inventory-build.md) remains open;
  bounded repair diagnostics are the next investigation.

- [Issue 28](issues/28-qualify-stateful-inventory-build.md) resolved: fresh stateful
  campaign passed 3/3 builds, 30 tasks in 32 attempts; retained failure repaired
  3/3. Earlier failures unchanged. Next decision: real repository and feature.
