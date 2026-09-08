# Design verification and recovery gates

Type: grilling
Status: resolved
Assignee: codex
Blocked by: 01, 02, 03

## Question

How should deterministic checks, product scenarios, isolated model reviews, repair budgets, branch quarantine, regression control, and escalation combine into gates that resist self-approval and silent acceptance weakening?

## Comments

### Proposed verification and recovery contract — 2026-09-08

Pending human discussion under Wayfinder. Existing autonomy, retry, and worker-authority decisions remain binding.

1. **Acceptance specification.** Each atom and Change set references versioned requirements, mandatory checks, supported environments, and expected outcomes. An independent QA task derives checks from requirements before candidate evaluation where practical. Checks derived only from implementation behavior cannot define intended behavior. Hidden benchmark checks are maintained outside candidate-worker access; ordinary development tests remain available to developers.
2. **Evidence collection.** A trusted runner executes the candidate in a fresh isolated environment and records candidate/base digests, validator and test versions, environment identity, commands, discovered/executed/skipped test counts, outputs, and exit results. Neither candidate-written reports nor exit zero alone establish success. Collection must distinguish missing tests, crashes, skips, and legitimate empty suites; required checks cannot silently disappear. The runner's durable records are outside candidate write authority, while test/code execution remains untrusted.
3. **Gate results.** Each required check returns pass, fail, or inconclusive. Unavailable dependencies, incomplete extraction, timeouts, malformed evidence, and unresolved flakiness are inconclusive rather than proof of a product defect or a pass. Record the cause and repair the evaluation environment or gather more evidence automatically.
4. **Layered evaluation.** Run schema/scope checks and cheap build/static checks first, then local behavior and contract tests. Evaluate the integrated candidate with affected-consumer tests and product scenarios before integrating a Change set. Record a final product checkpoint against one exact candidate revision. Impact-based selection is allowed only within recorded coverage; broaden the suite when impact is uncertain. Scope checks alone cannot certify product behavior.
5. **Verification adequacy.** Include requirements-derived examples, negative cases, and relevant property/invariant tests. Use targeted mutation or fault injection to check whether important validators detect incorrect behavior. Stage-dependent adequacy thresholds belong in the evaluation ticket; neither coverage percentages nor mutation scores establish universal correctness. Reviewers sharing the same model may still share blind spots.
6. **Existing repositories.** Establish reproducible base-revision results before candidate comparison. Historical failures remain explicit debt and do not automatically become new regressions. Required behavior for the current task and new regressions block acceptance. A baseline exception cannot justify weakening the product's mandatory acceptance contract or relabelling a newly broken test as historical debt.
7. **Model findings.** Independent QA/review findings become evidence or targeted reproduction tasks. A confirmed defect blocks integration. Unresolved findings affecting mandatory criteria remain inconclusive and trigger investigation; unsupported opinions do not automatically veto progress. Model prose alone cannot change requirements or approve the candidate.
8. **Test evolution.** Preserve the acceptance/test version that judged each candidate. A legitimate requirement, contract, fixture, or test correction proceeds through a separate traceable atom using requirement evidence and independent validation. Atom workers cannot remove/skip expectations merely to pass. This supports intended behavior changes without freezing every historical test forever.
9. **Recovery routing.** Concrete build/type failures route to code repair; missing evidence to retrieval; stale inputs to rebase/revalidation; consumer breakage to coordinated migration; setup failures to infrastructure recovery; flaky checks to repeated diagnostic runs preserving every result. Unknown failures trigger bounded diagnosis, not a fabricated classification. Passing once after a failure does not erase that failure.
10. **Attempt and replan history.** Retain the accepted ten-attempt atom policy, repeated-signature breaker, and autonomous re-planning after exhaustion. Track cumulative failure signatures, strategies, evidence, and costs across replacement atoms so changing an ID does not disguise repetition. Optional run budgets may be disabled. No new human approval stage or mandatory global retry cap is introduced; an exhausted strategy prompts changed strategy, finer experiments, or capability discovery.
11. **Acceptance and recovery after acceptance.** Publish durable evidence before atomically accepting the applicable result. Integration verifies current preconditions; stale or partially integrated results cannot count as completed Change sets. A later discovered regression appends a defect and invalidates affected current completion claims without rewriting historical evidence. Automatically create repair/revert atoms; evaluate dependent changes before reverting a shared provider in isolation.
12. **Initial implementation experiment.** Exercise a provider with two consumers, including a nested consumer. Deliberately inject a breaking provider change, a missing/skipped test, forged success text, stale base input, and worker/runner interruption. Require actual failures to be visible, wrong candidates to remain unaccepted, and autonomous repair or diagnosis to resume. Compare a simple worker loop with added QA and hierarchy using real local-model measurements before expanding the mechanism.


### Constraint surfaced by “Define the Work atom and context contract”

QA/review Worker views must remain independent of developer reasoning by default. Worker output cannot author acceptance; only durable deterministic evidence and an atomic Work-ledger transition may do so. Recovery treatment must follow a mechanically supported failure classification rather than automatically adding context.

## Answer

Accepted on 2026-09-08 through the user's instruction to continue, conditional on small-model suitability. Adopt the twelve-point proposed contract above with the following explicit responsibility boundary. This resolves the design decision, not empirical feasibility.

Ordinary factory code owns evidence capture, digests, test discovery/counts, check execution, stale-input detection, dependency traversal, attempt accounting, and acceptance transitions. These mechanisms are not instructions that every Worker view must carry. Mechanically recognizable failures use deterministic routing; ambiguous failures create focused diagnostic work rather than an invented classification.

Model workers receive narrow semantic jobs: derive a test for one requirement, reproduce one suspected defect, patch a bounded implementation against its contract, or migrate one consumer to a pinned provider interface. Their views include the necessary contract, relevant implementation and direct dependency interfaces, and compact failure evidence with retrievable full artifacts. They do not need the factory's complete architecture, global history, or developer reasoning in a QA view. Small means the smallest coherent task, not an arbitrary token cut that hides necessary semantics.

Suitability remains a hypothesis: decomposition cannot guarantee that a weak model can solve a difficult algorithm, infer a missing requirement, or detect a shared blind spot. Start with a simple worker loop on the actual local model; measure test generation, repair, and provider/consumer migration separately. Compare added QA and hierarchy against that baseline before retaining them. Repeated failure should test missing context, task decomposition, and model capability rather than merely increase retries or add management layers. The evaluation ticket owns numerical thresholds.

No routine human approval gate is added. The factory attempts automatic diagnosis, repair, revalidation, and re-planning under the accepted autonomy contract; acceptance remains tied to durable executable evidence, not a worker's claim of success.
