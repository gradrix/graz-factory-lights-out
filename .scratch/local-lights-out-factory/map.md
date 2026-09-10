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

- [Issue 29](issues/29-trial-history-attempt-filter.md): supervised history filter
  trial passed 3/3, reviewed candidate `091654a` ready for human merge review.
- [Issue 30](issues/30-diagnose-memory-qualification-halts.md): diagnose repeated
  memory-probe OOM-flag halts without weakening resource enforcement.

- Owner authorized merges/pushes; history filter merged and pushed at `0d30d48`.
- [Issue 31](issues/31-draft-bounded-feature-plans.md) resolved: bounded draft planner
  trial produced four reviewed tasks, not execution authority. Setup now has one
  CPU bootstrap command. Next: trusted materialization and resource-probe diagnosis.

- Large repositories are an explicit architectural requirement. [ADR 0001](../../docs/adr/0001-repository-snapshots-and-bounded-task-inputs.md)
  separates repository snapshots from task bundles; [issue 32](issues/32-separate-repository-access-from-task-bundles.md)
  defines the first migration slice before generalized scheduling. Indexes remain
  derived, revision-bound data; no graph technology selected or scale claim made.

- [Issue 32](issues/32-separate-repository-access-from-task-bundles.md) resolved:
  snapshot/bundle access and CLI implemented; real 1.53-MB source selected within
  current broker budget. Next: snapshot-bound reviewed-plan preparation. See
  [results](repository-access-results.json); no large-build qualification claimed.

- [Issue 33](issues/33-prepare-snapshot-backed-reviewed-tasks.md) resolved: reviewed
  snapshot root tasks prepare existing RunPlans with trusted gates; candidate lifting
  preserves omitted source. Next: accepted-base progression and combined validation
  before recursive managers. Dependent tasks deliberately remain blocked.

- [Issue 34](issues/34-progress-reviewed-features.md) resolved: snapshot planning,
  sequential accepted-base progression, transitive snapshot-worker reuse checks,
  combined validation and replay. Local model: original four-task plan passed three
  executions; v3 three-task follow-up passed once. Ambiguity reread/protocol failures
  retained; explicit clarification output then passed the narrow escalation probe.
  See [results](feature-progression-results.json). Next: diverse-product/manager
  qualification and measured source-selection failures before recursive delegation.

- [Issue 35](issues/35-qualify-specialist-board.md): optional board implemented and
  compared on an unfamiliar product. Both plans passed; board cost 3.6 times the
  planning tokens without demonstrated improvement. Keep single default, stop
  immediately on specialist blockers, retain every failed trial before follow-ups.

- [Issue 36](issues/36-execute-features-under-pinned-policy.md): policy compilation
  removes per-task review assembly for preauthorized exact-file features. Live
  three-task build and replay passed; missing policy decisions halt. Continue
  navigation/product qualification before more orchestration.

- [Issue 37](issues/37-index-python-definitions.md): snapshot-bound Python definitions
  and unchanged-file analysis reuse implemented. Five navigation probes on GFLO
  passed; index coverage does not establish callers or model context sufficiency.

- [Issue 30](issues/30-diagnose-memory-qualification-halts.md): kernel counters proved
  an OOM despite Docker's false flag. Trusted supervisor proof replaces the unreliable
  qualification predicate; 100 complete qualifications passed, unrelated kills rejected.

- [Issue 38](issues/38-qualify-recursive-settings-feature.md): three recursive-settings
  builds passed nine tasks; 61 unmodified files survived each. Symbol queries were
  prepared, not autonomous. A real product target remains an owner decision.
- [Issue 39](issues/39-stabilize-reviewed-gate-order.md): canonical JSON exposed
  gate-order replay instability. New order is deterministic; historical contracts
  are replayed exactly after strict equality checks for all non-order content.

- [Issue 40](issues/40-qualify-ai-gamer-win-detection.md): real bug fix delivered as
  target draft PR; local implementation passed, reviewer supplied tests after worker
  failures. No end-to-end autonomous success claimed.
- [Issue 41](issues/41-preserve-opaque-snapshot-files.md): captured SQLite and other
  opaque blobs survive text changes; bounded text APIs still reject opaque inputs.
- [Issue 42](issues/42-separate-policy-planning-worker-profile.md): planning/worker
  profiles separated; standalone low reasoning supported but not a better default.

- [Issue 43](issues/43-expose-worker-turn-budget.md): remaining turns/output projected
  into tokenized worker instructions. Fresh trial proposed both candidates but still
  failed semantics; separate smaller test tasks are the next diagnostic.

- [Issue 44](issues/44-qualify-smaller-test-tasks.md): smaller tests accepted gaps and
  anti-diagonals, then potential failed/truncated. Rectangles and integration never
  ran. Semantic fixture repair remains a qualification blocker within these budgets.

- [Issue 45](issues/45-add-bounded-development-repair.md): same-model development
  checks, bounded exact edits, verified example data and exhausted-work review packets.
  Retained planning/protocol/coverage failures; a finding blocks the square-only test
  acceptance. Reviewed/data-assisted correction passed one repair response and final
  checks, preserving all other files. End-to-end unattended planning remains unproven.

- [Issue 46](issues/46-qualify-leds-config-repair.md): second-domain parser fix and six
  local-model tests merged into leds-service PR 10. No factory specialization or model
  change. Review caught default-valued test weakness; finding blocks old reuse and
  reviewed local repair passes reference/baseline/mutant checks. Qualification remains
  supervised; next work is prospective test adequacy and broader repeated features.

- [Issue 47](issues/47-add-reusable-test-adequacy-gates.md): generic pytest gate rejects
  supplied faulty variants only through real assertion failures; errors/skips do not
  qualify. Retained weak tests rejected and same-instruction local repair passes.
  Trusted variant selection remains necessary; no automatic fault-discovery claim.

- [Issue 48](issues/48-qualify-generated-fault-variants.md): bounded AST fault generation
  and sandboxed reference qualification replace handwritten variants for supported
  operators. Six parser faults detect the prior weak suite; error-producing variants
  and numeric unchanged/crashing controls are excluded. Trusted oracle remains needed.

- [Issue 49](issues/49-qualify-prospective-color-feature.md): prospective color feature
  succeeded on a separately recorded build after reference cases were split to expose
  mutation crashes. Local planning/implementation retried; all 11 local tests passed
  first response. Original failure retained. Reference preparation still needs review.

- [Issue 50](issues/50-align-repair-system-protocol.md): fixed contradictory legacy
  system message for repair workers. Same-policy color build passes; malformed hash
  still causes retry. Default protocol and enforcement unchanged; no reliability-rate
  claim from one trial. Investigate bound edit handles and planner source references.

- [Issue 51](issues/51-add-turn-bound-repair-handles.md): short per-turn repair targets
  resolve to full source/contract/file identities. Seen color trial passes without
  protocol errors, with semantic retry still required. Legacy checks preserved.

- [Issue 52](issues/52-clarify-planner-input-output-paths.md): full-metadata allowed-path
  state and explicit input/output rules prevent ambiguity about new task outputs.
  Retained bad plan still rejected with precise feedback; fresh seen plan valid first
  response. Broader end-to-end qualifications remain needed.

- [Issue 53](issues/53-qualify-sparse-mode-selection.md): negative stateful feature trial.
  Planner embeds wrong algorithm despite correct requirements; worker makes five
  unchanged repairs and quarantines. No protocol errors or target changes.
- [Issue 54](issues/54-prioritize-requirements-over-plan-advice.md): requirement-priority
  prompt did not fix semantic anchoring; reverted after separate failed trial. Next
  separate interface declarations from planner implementation advice structurally.

- [Issue 55](issues/55-separate-contracts-and-stop-stalled-repairs.md): typed declarations,
  original dependency requirements, direct planning and durable review stops. Mode,
  color and parser qualifications pass; retained repeats show remaining question
  grounding gaps. 469 tests/25 subtests pass; all 28 target tests pass together.
- [Issue 56](issues/56-ground-planning-questions-in-requirements.md): next bounded design
  and qualification for questions already answered by the immutable request, while
  preserving genuine missing-policy stops.

- [Issue 56](issues/56-ground-planning-questions-in-requirements.md) resolved: bounded
  exact-quote review recovers the retained questions without suppressing two real
  policy gaps. Whole-feature qualification and 480 tests pass; semantic judgment
  remains model-dependent.
- [Issue 57](issues/57-edit-bounded-windows-in-large-files.md) next: source-window edits.
  Index lookup works on 10,002 lines; existing whole-file worker exceeds context.

- Issue 57 resolved: bounded worker windows qualified on a 10,002-line synthetic file
  and the real repository reader. [Evidence and failures](window-qualification/README.md).
  Next boundary: whole-file planning and the 256 KiB execution bundle.

- Issue 58 implemented and initially qualified: bounded planning can read a large-file
  function and complete a feature, but repeated trials expose navigation and output
  reliability gaps. [All trials](window-feature-qualification/README.md).
- Next: issue 59 compares behavior-scoped test tasks (user suggestion); issue 60 targets
  planner read/coverage recovery. Neither permits overlapping mutable file ownership.

- Issue 59 resolved: three equal-budget pairs found no advantage from splitting test
  workers, 53% higher token use, and an assigned-coverage finding now blocking one
  split contribution. [Campaign and audit](test-decomposition/README.md).
- Keep one bounded test worker by default for this workload. Next: issue 60 planner
  recovery; issues 61/62 track new-file draft repair and integration provenance.
