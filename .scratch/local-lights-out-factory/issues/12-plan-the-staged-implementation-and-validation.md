# Plan the staged implementation and validation

Type: grilling
Status: resolved
Assignee: codex
Blocked by: 10, 11

## Question

What implementation sequence, vertical slices, Capability-profile rollout, benchmark cadence, operational checkpoints, and stop/go criteria form an implementation-ready plan from the reference architecture to a credible unattended local Factory?

## Comments

### Proposed staged implementation plan

Pending user discussion. This plan operationalizes the accepted architecture, not a commitment to implement all layers before testing. Numerical campaign criteria remain authoritative in [Set feasibility and evaluation thresholds](10-set-feasibility-and-evaluation-thresholds.md); references below do not replace or relax them. Later stages are conditional on evidence, not routine human approvals inside a preauthorized run.

#### Stage 0 — Verify the actual execution target

Inventory the real GPU host, memory, disk, driver, container resource enforcement, available model service and exact checkpoint/tokenizer/runtime identity. Probe the configured inference endpoint and supported structured-result behavior with one request at a time; verify real token accounting and start with a conservative supported context profile. Do not silently treat this checkout machine as the GPU host or a model name as a verified checkpoint. Reuse an existing service only after capability checks. Record the endpoint without credentials and retain detailed environment provenance privately where appropriate.

Exit evidence: model loads and answers representative bounded requests; required sandbox restrictions and host-survival controls are demonstrably enforced; the profile is reproducibly identified. Failure revises serving, quantization, context or environment configuration before claiming worker competence. Infrastructure-only unit work can proceed if hardware is unavailable, but cannot satisfy any real-model gate. Missing host location/access is a concrete implementation prerequisite, not a reason for speculative installations on the wrong machine.

#### Stage 1 — One durable task-to-evidence loop and the twelve-task pilot

Build a Python package with CLI submission/status/resume; validated versioned atom/result records; a SQLite ledger; immutable artifact storage; the thin model client; disposable worker/test environments; and a trusted gate runner. Implement only the lifecycle needed to execute a prepared task, collect a candidate, validate it, accept or retry, and recover after interruption. Keep model/test operations outside ledger transactions. Include idempotent conditional acceptance and an explicit history of failures from the outset.

Implementation order inside this slice: record/transition tests; artifact publication/reconciliation; broker and evidence capture; bounded worker-view composition and inference; then the complete live loop. Deterministic doubles test implementation mechanics but never stand in for local-model measurements. Start product fixtures with straightforward local edits; add only the tools needed for those edits, with shell/network abilities still governed by the accepted execution contract. Workers cannot mutate validators or canonical factory state. Do not pre-build all logical modules as separate services or generic extension APIs.

Run the accepted twelve-task pilot as soon as the loop operates. Measure coding, repair, consumer migration, and requirements-derived tests using a few logical worker profiles sharing the GPU serially. Change prompt schemas, context selection, or task granularity based on concrete failures. The pilot is diagnostic, not a benchmark pass-rate claim.

Exit evidence: traceable live attempts from input through candidate and trusted outcome; automatic retry/restart demonstrated; no known acceptance-authority violation; a documented failure taxonomy from the pilot. Do not add planning layers to rescue a fundamentally unusable coding loop. The first implementation handoff should stop expanding features at this measurement point, while allowing focused fixes and repeated pilot runs within scope.

#### Stage 2 — Calibrate workers and harden recovery

Implement the remaining applicable fault fixtures and recovery paths, precise context manifests, typed expansion, compact diagnostic views, and reporting of cumulative retry/replan cost. Calibrate supported context tiers and specialization against the simple worker baseline. Run the held-out atom campaign and independent QA comparison with the accepted thresholds. Add quality collection through the Python profile: mandatory configured checks plus advisory complexity/coverage/CRAP findings where evidence is available. A missing required analyzer stays inconclusive.

Exit evidence: the atom, integrity/recovery, and any claimed QA capability meet their respective criteria. Context targets remain diagnostic rather than reasons to discard necessary input. If a class fails, narrow its claim and repair its prompts/context/tools or decomposition; preserve unsuccessful campaigns. Revisit the chosen model or serving profile if failures are semantic capability failures rather than plumbing errors. No general manager hierarchy yet.

#### Stage 3 — Dependency-aware changes and dynamic repair

Implement explicit provider/consumer records, contract revisions, reverse-edge impact selection, and a prepared Change set for one provider/two consumers, one nested. Materialize diagnosis and repair tasks from unexpected test failures. Evidence must distinguish provider regression, consumer defect, stale inputs, and evaluator failure. Deduplicate work by objective/input/failure identity rather than allowing recursive unmanaged worker spawning.

Include known breaking migrations, compatible internal refactors, parent-contract checks that contain child changes, cross-subtree impacts, and incomplete extraction coverage that broadens verification. Vertical requirement/evidence projections update mechanically; semantic uncertainty may invoke a focused planning task, not all ancestors. Version candidate inputs; revalidate combined outputs. Implement the recorded Git integration intent and restart reconciliation so neither a branch update nor a passing local test alone counts as a completed product.

Exit evidence: accepted integrated-change criteria plus the above containment/localization fixtures, with old evidence preserved and no partial migration reported complete. Revise graph coverage, failure routing, contract granularity or integration protocol when fixtures falsify them. This establishes prepared-graph execution, not autonomous product planning.

#### Stage 4 — Existing code and a second product technology

Onboard existing fixture repositories incrementally, collecting source/build evidence and explicit baseline failures. Run the accepted maintenance campaign before claiming maintenance support. Then add one second-language Capability profile and the equivalent per-profile evaluation; follow with the mixed-language migration campaign. Select the second language at the stage entry from the intended product workload and available local-model evidence, recording the choice before scoring. This is an explicit future experiment choice, not implicit Python-only support or a speculative universal language plugin system.

Exit evidence: maintenance, second-language and mixed-language claims each meet their own criteria without rewriting core lifecycle semantics. Do not infer one from another. If core assumptions turn out language-specific, revise the offending interface before broadening language support. This stage may be split into independently scored increments to keep work bounded.

#### Stage 5 — Product planning, scope growth, and novel capabilities

Move from prepared Work graphs to an accepted Intent package and model-proposed bounded plans validated by the controller. Start with a flat planner and focused diagnosis. Exercise an intent change affecting several descendants and compare on-demand scope planning only where the flat/test-driven baseline has demonstrated limitations. Require executable requirement coverage and integrated completion; generated plans or attractive graph summaries alone do not pass.

Grow repository size, scope depth, and dependency coupling independently. Learn/retrieve tools or environment setup through separate isolated capability-discovery tasks with their own validation. Record context selection, discarded hypotheses, missing dependency coverage, and repeated rework. Reuse the accepted completion/integrity criteria on predeclared planning workloads; specify the workload size and deadlines before each campaign and report its exact tested envelope. This stage does not promise arbitrary huge applications.

Exit evidence: scoped end-to-end completion without supplied execution graphs and measured benefit for any retained planning layer. Below-target behavior revises hierarchy, task decomposition, retrieval or capability profiles, not automatic creation of more manager agents. A replacement model starts a fresh relevant calibration campaign.

#### Stage 6 — Unattended operational validation, then self-upgrade

Short restart/recovery exercises occur from Stage 1 onward. Run the accepted eight-hour shakeout and 72-hour scored workload once the relevant workload capabilities exist, retaining complete records of intervention, faults and unresolved objectives. Configure log/artifact retention with protection for live/accepted evidence, consistent ledger/artifact backups, restore rehearsal, disk-reserve admission, and process supervision before the long run. Tune throughput only after correctness; no throughput or electricity gate is added.

Use pilot measurements to size storage and retention, then freeze the operational profile and workload manifest before the scored run. Runtime tuning and exact operational values are experiment outputs, not guessed constants. Any corrective implementation change restarts the qualifying campaign without hiding its failed predecessor.

Only after a recoverable ordinary factory is demonstrated, add Generation N/N+1 candidate factory changes, copied-state tests, canaries, and the independent preauthorized promotion/rollback launcher. Test rejected candidates and rollback before enabling automatic promotion. Never allow a worker to modify the active controller or its own acceptance policy. Autonomous publication or production deployment of generated products remains outside the accepted scope.

#### Evidence and handoff contract

Each increment records the code revision and intentional working-tree state, environment/model identity, command/configuration, workload version, raw attempt/evidence artifacts, gate results, unresolved limitations, and next bounded action. Passing an early stage permits the next experiment, not a blanket support claim. Preauthorized execution can proceed without routine human checkpoints; missing authority, host safety failures, or unresolved intent contradictions still follow the existing terminal-exception contract.

Recommendation for the first implementation request: authorize Stage 0 and Stage 1 only, including focused repairs needed to run the live pilot. Do not implement the full roadmap in one pass. Once this planning decision is accepted, create concrete implementation tickets for that first slice and retain the later stages as evidence-dependent expansion work.

### Accepted checks-first dependency recovery

Start with graph-guided local/consumer/integration checks and scheduler-owned dynamic diagnosis/repair tasks, not a manager agent for each scope. Measure a failure reported in a consumer but caused by the provider, a genuinely consumer-local defect, and unknown-impact coverage requiring broader checks. Preserve existing criteria and versioned inputs; prevent consumer repairs from disguising provider regressions. Vertical requirement/evidence propagation is ordinary bookkeeping unless semantics require planning. Compare any later hierarchy to this simpler baseline. Intentional breaking contracts and top-level requirement changes may still need coordinated planning before edits.

### Implementation-foundation resolution

Use the accepted typed Python/SQLite/artifact/container/model-client foundation for the first measured slice, not as a requirement that generated products use Python. Sequence a second-language Capability-profile experiment after the Python baseline, followed by mixed-language contract migration and integrated checks. Keep core lifecycle semantics unchanged across profiles; revise any accidental language coupling exposed by these experiments. Select the second language when specifying that stage, not by silently treating examples from conversation as commitments.

### Product-graph resolution — 2026-09-08

Stage the first real-model experiment around a shared provider and two consumers, including a nested consumer. Include a breaking contract migration and maintenance of an unfamiliar existing project. Increase graph size/depth and coupling separately; do not require microservices. Preserve the long-term large-product destination while revising strategies from evidence. Include a repeatable calibration path for replacement local models.

### Constraint surfaced by “Choose the durable orchestration architecture”

The plan must be iterative and empirical. Start with the smallest durable end-to-end slice and a few logical workers on the actual RTX 5090/Qwen service; add layers only after stage-specific measurements pass. Every stage must name which assumptions it tests, its falsification thresholds, and which later design decisions may be revised from the result.

Include explicit calibration stages for Worker-view specialization, Context-policy tiers, retrieval/expansion behavior, Work-atom granularity, and autonomous capability discovery. Treat these as versioned policies learned from evidence rather than fixed constants.

## Answer

### Resolution — 2026-09-08

The user accepted proceeding after the recommendation to finish this decision and limit the first implementation effort to Stage 0 target verification and Stage 1 durable task-to-evidence execution plus the twelve-task real-model pilot. Adopt the staged plan above. Later stages remain conditional on measured evidence; this does not authorize implementing the whole roadmap now.

Start target checks on the available RTX 5090 and build deterministic controller mechanics alongside serving qualification. Preserve the SGLang/vLLM comparison, small Worker views, scheduler-owned evidence and diagnosis, profile-driven product technologies, and no automatic remote fallback. A successful infrastructure probe does not establish coding capability.

Implementation work is tracked separately in [the implementation index](../implementation.md). These are build tasks beyond the planning map's destination, not new Wayfinder decision tickets.
