# Define the Product graph and module contract

Type: grilling
Status: resolved
Assignee: codex
Blocked by: 03

## Question

What structural rules, contracts, dependency constraints, size budgets, graph representations, and conformance checks should make generated Product modules independently understandable while still composing into a functioning product?

## Comments

### Constraint surfaced by “Define the Work atom and context contract”

The Product graph must support purpose-specific Worker views, structural-coverage checks, direct and reverse dependency retrieval, typed one-hop expansion, and content-addressed invalidation without requiring an entire graph or repository summary in a prompt.

### Conversation checkpoint — 2026-09-08

Recovered from the user's explicit answers in this conversation. This ticket remains claimed: the cross-scope dependency proposal was discussed but its final recommendations have not yet received an answer. Do not repeat the already accepted questions or treat the pending proposal as resolved.

#### Accepted direction

- Product modules have cohesive responsibilities, narrow public Interfaces, owned source/data, declared dependencies, local tests, and explicit side effects. Prefer comprehension and cohesion over tiny files or arbitrary fragmentation.
- Maintain declared product structure and separately observed source/build facts. Keep module/scope structure, code-intelligence indexes, and build/package facts at different resolutions.
- Module contracts record identity, purpose, ownership, public/private Interface, allowed dependencies/callers, tests, requirement links, compatibility, runtime assumptions, and calibrated maintainability measures. Ordinary workers receive only relevant projections.
- Dependency conformance is private-by-default; prohibited cycles, undeclared edges, private access, incompatible unapproved contract drift, and missing required evidence prevent acceptance. Architecture approval inside preauthorization is automatic.
- Extraction has explicit coverage and provenance. Unknown or heuristic facts cannot certify a requirement they do not establish. Maintainability heuristics begin as measurements and only become gates after calibration.
- The product has a hierarchy of scopes plus explicit dependency edges crossing scopes at arbitrary depths. Each scope has its purpose, owned requirements, child contracts, input/output Interfaces, external dependencies, inherited policies, and aggregated evidence.
- Root and Scope stewards receive their local level, immediate children, and relevant lateral/upward contracts. Leaf workers receive task-specific source and diagnostics. A node owns durable facts; steward invocations are created when needed, with no permanent chat per node.
- Child-to-parent projection contains typed Interface changes, requirement/evidence status, dependency changes, risks, and unresolved contradictions. Free-form summaries remain navigation aids.
- Hierarchy depth and breadth are empirical policies. Split for context/cohesion and merge redundant pass-through scopes. Test increasingly deep projects, cross-scope changes, stale projections, and planning from compact root views on real Qwen.
- The Factory prepares worker environments. Prebuilt profile environments combine with reproducible project setup and sandboxed novel-tool installation. A separate capability-learning atom may promote a useful setup.
- Workers receive a concise Environment contract covering available tools, commands, writable paths, granted network capabilities, and limitations. Detailed image/setup provenance stays in durable records. Docker lifecycle and host/model-serving configuration remain outside ordinary worker context.
- Infrastructure setup failures use a separately recorded recovery path, rather than consuming semantic coding retries. Graph extractor internals are exposed only when relevant to diagnostics.

#### Pending: coordinated changes across scopes

The user's motivating case is one worker developing a library/client/wrapper while workers elsewhere consume it. Planning must anticipate those consumers; later provider changes must automatically create the necessary migration and QA work.

Proposed contract for confirmation:

1. Record each dependency by provider, consumer, consumed Interface/version, compatibility constraints, ownership, and associated tests. Cross-scope edges are independent of hierarchy depth.
2. Plan related provider and consumer changes as a versioned Change set. Define the proposed Interface and consumer expectations, then materialize provider, consumer, integration, and QA atoms with explicit ordering.
3. Detect a proposed Contract revision from source/schema changes plus tests. Internal refactors revalidate affected behavior without forcing consumer source edits. Additions permit optional adoption. Breaking or behavioral changes trigger consumer impact analysis; additions alone are not proof of behavioral compatibility.
4. The Orchestrator traverses reverse dependencies and creates compact impact records and migration atoms. Workers receive their old/new contract delta, the dependency path explaining impact, relevant tests, and expansion tools. No direct worker messaging or implicit read of latest is required.
5. Pin Attempts to immutable base/target revisions and input artifacts. Reconcile work when a consumed contract changes. Preserve accepted history, but revalidate the resulting candidate against the intended product revision.
6. Prefer expand-and-contract migration when old/new Interfaces can coexist. Otherwise integrate the provider and required consumers together after validating the complete candidate. Partial migration must not be reported as a completed Change set.
7. Run provider tests, compatibility checks, affected direct-consumer contract tests, transitive integration tests, critical product scenarios, and structural conformance. Selection uses observed dependency coverage; incomplete dynamic dependency coverage calls for broader tests, not a claim of complete impact knowledge.
8. Treat internal module cycles separately from scope hierarchy: grouping nodes does not remove a dependency cycle. Extract shared contracts, invert dependencies, or validate an explicitly permitted cycle. External package upgrades follow the same revision/migration mechanism using pinned package inputs.

Implementation remains staged: validate a small provider with two consumers, including a consumer in another nested scope, on the real local model before expanding the hierarchy or automation.

## Answer

### Resolution — 2026-09-08

Following the accepted hierarchy and environment decisions, discussion of cross-scope migrations, and the user's instruction to proceed with large-project ambition, adopt the accepted direction and eight-point coordinated-change contract recorded above. The historical pending marker in the checkpoint is superseded by this resolution.

The Product graph comprises nested scopes and explicit dependency edges across arbitrary depths. Declared contracts are compared with observed source/build facts. Scope stewards receive bounded projections and are invoked on demand. Provider revisions generate reverse-dependency impact records, consumer migration atoms, and QA work; immutable inputs and coordinated Change sets prevent partial migrations from masquerading as accepted products.

Large applications are a target for both greenfield development and maintenance. Product modules may be internal packages or subsystems in a modular monolith, shared libraries, or separately deployed services. Microservices are not required. Existing repositories are onboarded incrementally; unknown dependency coverage remains explicit, and existing code need not undergo a wholesale architectural rewrite before bounded tasks can run.

Time and electricity are acceptable operating costs. Optimize first for verified completion and recoverable progress; measure throughput, energy, and repeated work to understand scaling rather than impose a speed-first product ceiling. Extra attempts do not guarantee solvability: decomposition, inference capability, impact coverage, and test adequacy remain experimental limitations.

Keep model choice and context policy versioned. New local models may replace the initial Qwen target after calibration on the same tasks, with model/tokenizer/runtime provenance and regression evidence. Do not assume a model upgrade preserves tool behavior or prior calibration.

Validate first with one provider and two consumers, including a nested consumer. Exercise initial construction, repeated extension, a breaking contract migration, stale-input recovery, and maintenance of an unfamiliar existing project. Grow scope count, depth, and coupling only after each stage supplies evidence; revise partitioning and worker policies as necessary.
