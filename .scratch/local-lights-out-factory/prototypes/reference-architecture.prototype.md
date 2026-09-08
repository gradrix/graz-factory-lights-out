# GFLO reference architecture — discussion prototype

Status: proposed, not validated. Companion: [clickable lifecycle simulation](factory-lifecycle.prototype.html).

Question: can independently understandable worker views produce a coordinated provider/consumer change while trusted factory code retains acceptance and recovery authority?

This is a design artifact, not the production implementation or evidence that the local model can perform the jobs. The HTML file opens directly in a browser with no installation, network access, or persistence. Its buttons simulate events normally driven automatically. It intentionally models a prepared graph; arbitrary plan generation is a later experiment.

## Ownership and deployment

```text
Trusted single-host control plane
  Orchestrator -- transactional transitions --> WorkLedger (SQLite)
       |                                          |
       +--> ProductGraph / context composition <---+ artifact references
       +--> ArtifactStore (immutable manifests and blobs)
       +--> InferenceGateway --> one local GPU model server
       +--> WorkerRuntime --> ExecutionBroker --> disposable attempt container
       +--> GateRunner ------> ExecutionBroker --> isolated test execution
                                  |
                            observed outputs
                                  v
                    trusted evidence collection --> WorkLedger
```

These are logical modules, not eight microservices or eight prompts. The first implementation uses one controller process with supervised external model/test execution. Only the broker holds container-management authority. Worker-controlled test programs are not trusted evidence collectors. The controller collects execution facts and validates required checks; stdout alone cannot authorize acceptance. The model server does not hold the ledger or publish commits.

## Durable records versus worker context

Illustrative field sketches, not frozen serialization schemas:

| Record | Required responsibility |
| --- | --- |
| Work atom | Objective and requirement refs; graph revision; input and contract refs; capability and policy refs; allowed outputs; prerequisite/acceptance refs |
| Attempt | Atom and attempt identity; lease/fencing token; pinned base; context manifests used; observations; candidate refs; outcome |
| Context manifest | Immutable selected artifact refs/digests; provenance and authority; role; omissions; retrieval reasons; tokenizer/profile identity; input and reserved output budget |
| Candidate manifest | Producer attempt; base and input digests; declared patch/output refs; proposed contract revision; affected scope |
| Gate evidence | Exact candidate, test and environment identities; required/discovered/executed/skipped checks; pass/fail/inconclusive; logs and diagnostic refs |
| Acceptance record | Unique applicable atom/result; satisfied preconditions; immutable evidence refs; integration status, if applicable |

The developer view projects only the task, relevant source, direct interfaces, permitted actions, and compact failure evidence. QA starts from the requirements and candidate facts without developer reasoning. A typed missing-context request creates a new immutable manifest; the controller does not silently append an unbounded chat. Architecture and quality reports stay outside the prompt until a specific finding is relevant.

## Provider migration walkthrough

Containment is `project → parser`, `project → cli`, and `project → reports → export`. Both `cli` and `reports/export` depend on `parser`, regardless of depth.

The example changes `parse(text) → integer` into `parse(text) → ParseResult(value, errors)`. The contract must specify error behavior before code work; a new type name alone is insufficient. This example assumes no compatible expansion path was selected and uses one coordinated local integration.

1. Pin base B and old/new contract revisions; materialize the prepared work graph.
2. A QA task derives acceptance examples independently. The provider developer sees parser code and its contracts, not consumer internals.
3. Validate and accept the provider candidate as eligible for integration. Do not publish the breaking provider alone to canonical code.
4. Each consumer worker receives its own source/tests plus the exact provider candidate interface. Build its workspace from that pinned candidate and base, not an unspecified latest version.
5. Validate each consumer candidate, then compose one integrated candidate from the pinned outputs.
6. Check direct/reverse dependencies, contract conformance, required quality rules, and whole-product scenarios against that exact candidate. Incomplete impact coverage requires broader tests.
7. Publish durable artifacts/evidence; the ledger conditionally accepts the integration only if base and graph preconditions still hold. Local Git publication and ledger acceptance are not one cross-system ACID transaction: use a recorded integration intent, expected-old-revision ref update, and restart reconciliation. A mismatched ref/result is unresolved work, not verified completion.

## Failure and quality paths

### Accepted simplification: checks first, planning on demand

The user accepted test-driven recovery as the default. Ordinary changes run local, known-consumer, and appropriate integrated checks. Unexpected failures create small diagnosis tasks, then evidence-supported repair tasks. The scheduler owns their identity, dependency ordering, attempt accounting, deduplication, and integration; workers return findings/proposals rather than recursively spawning unmanaged agents.

Failure location is evidence, not ownership of the cause. A failing export test can expose a parser bug, a consumer bug, a stale contract, or an evaluation failure. Diagnose before adapting a consumer to broken provider behavior. Route mechanically established cases directly; ambiguous cases get bounded model diagnosis with a reproduction requirement. Repair tasks retain the originating objective and cumulative history when a new graph revision is needed.

Maintain horizontal dependency edges and vertical requirement/evidence projections in code. Do not invoke a steward at every ancestor on every change. Recompute affected projections and run parent-contract checks; unchanged outward contracts may contain the impact when the available evidence supports that conclusion. Unknown impact triggers broader checks or investigation. Passing tests alone do not certify missing coverage or unchanged unstated requirements.

Known intentional breaking changes still use the coordinated migration walkthrough above. Scope planning is reserved for ambiguous requirements, changes spanning contracts that need a joint decision, or repeated failed local recovery. A top-level requirement change may need such planning immediately; tests cannot invent its intended semantics. No additional human approval stage is introduced.

- Failed required check: preserve failed attempt; route directly only when evidence establishes the repair target, otherwise create focused diagnosis before repair.
- Missing/skipped required check: inconclusive; repair the evaluation path rather than invent a product failure or pass.
- Stale base/provider: fence off stale results and revalidate/rebase affected work; old passing evidence remains historical.
- Crash after artifact publication: reconcile references and attempt state; orphan artifacts are not accepted results. Never infer success merely because a file exists.
- Crash after Git update: compare the durable integration intent, actual ref and candidate evidence before resuming the pending transition.
- Ten attempts exhausted or repeated signature breaker: quarantine the atom and autonomously change strategy/decomposition; append a graph revision with cumulative history. The demo's replacement-graph button is illustrative and does not implement the strategy-evidence check.
- Advisory CRAP/complexity hotspot: create focused quality work; do not hide it or treat the score as a correctness oracle. A profile-designated mandatory quality violation blocks acceptance. Required follow-up work must finish before claiming full intent completion; optional debt remains explicitly reported.
- Unsupported tool/profile: separate capability-discovery work in the allowed environment, followed by validation; no silent promotion to supported status.

## What the clickable simulation omits

No real SQLite, filesystem durability, hashes, leases/time passage, Git, LLM, Docker, graph extraction, context token counting, benchmark evaluator, hidden tests, self-upgrade, or security enforcement. Simulated successful checks are supplied by buttons. The prototype must never be used to claim these mechanisms passed a test. It also serializes work for readability rather than modeling the future CPU-side parallelism.

## Evidence-led growth

First implement one durable task-to-evidence loop and run the accepted small real-model pilot. Then measure separate developer/repair and QA workers, interruption recovery, and this prepared provider migration. Add graph discovery and hierarchical planning only after the simpler baseline supplies useful evidence; compare added layers on the same tasks. Later stages include maintenance, a second product language, mixed-stack contracts, scale and unattended duration, and candidate Generation N+1 validation. The exact staged plan remains the next decision.

## Discussion checkpoint

The user accepted a lightweight dependency graph with tests and dynamic repair as the default, and planning only when needed. The interactive demo adds a simulated consumer failure diagnosed as a provider defect. It does not yet prove real failure localization or automatic vertical impact containment; those remain measured implementation experiments. Candidate acceptance remains distinct from integrated product acceptance.
