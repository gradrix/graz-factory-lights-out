# Atomic context and code structures for a local software Factory

Research date: 2026-09-02  
Question: What evidence supports decomposing agent work and generated software into small contract-bound units, navigating repositories through maps/graphs/trees, retrieving minimal authoritative context, and detecting architectural drift without loading the whole repository into the model?

## Executive conclusion

The proposed architecture is feasible as an **engineering hypothesis worth prototyping**, but the evidence does not support a claim that arbitrary end-to-end product generation can already be made reliable merely by splitting prompts into small pieces.

The strongest supported pattern is a hybrid:

1. keep source, executable tests, compiler/build facts, explicit contracts, and versioned structural manifests authoritative;
2. derive several typed graphs from those artifacts;
3. issue a model one narrow state transition at a time with a small, inspectable context slice;
4. allow explicit context expansion rather than silently filling a long window;
5. accept a transition only through deterministic checks; and
6. invalidate derived context and downstream work through recorded dependency edges whenever an input changes.

This is materially stronger than either extreme: sending the entire repository, or trusting summaries/vector search as truth. It also does **not** imply that Product modules should be as tiny as Work atoms. Excessive product fragmentation increases the number of contracts and coordination edges. Work atoms should be small execution transactions; Product modules should instead be cohesive units with narrow public interfaces and enforceable dependency boundaries.

## What primary evidence supports

### 1. Bounded interfaces improve agent operation, but task decomposition is not itself a correctness proof

The SWE-agent work found that an agent-computer interface materially affected software-engineering performance. Its published interface deliberately limits the file viewer to 100 lines, makes repository search output succinct, and runs a linter during edits rather than letting syntactically invalid edits proceed. The authors report 12.5% pass@1 on the original SWE-bench evaluation and emphasize that the interface changes agent behavior and performance ([paper](https://arxiv.org/abs/2405.15793), [official ACI documentation](https://github.com/SWE-agent/SWE-agent/blob/main/docs/background/aci.md)).

Agentless demonstrates a different bounded flow: localization, repair, and patch validation are separate phases; the LLM does not freely choose an unbounded action sequence. Its localization narrows hierarchically from files to code elements to fine edit locations ([paper](https://arxiv.org/abs/2407.01489), [official implementation](https://github.com/OpenAutoCoder/Agentless)). This supports using separate, typed Work atoms for locating, planning, editing, and validating rather than one general “build the feature” conversation.

These systems are mostly evaluated on issue repair, not autonomous product construction. Their evidence supports narrow interfaces and staged localization; it does not establish that arbitrary requirements can always be decomposed correctly or that independently generated pieces will compose.

### 2. More context is not automatically better

“Lost in the Middle” shows that long-context models can be sensitive to where relevant evidence appears and that a nominal context window does not demonstrate robust use of all positions ([paper](https://arxiv.org/abs/2307.03172)). This is not a coding-specific result, but it directly invalidates the assumption that fitting the repository in the advertised window is sufficient.

Coding-specific retrieval studies point the same way:

- RepoCoder improved repository-level completion over in-file baselines by more than 10% in its evaluated settings by iterating retrieval and generation, while also finding that later iterations can regress and that stopping remains difficult ([paper and limitations](https://arxiv.org/abs/2303.12570)).
- Repoformer reports that many routinely retrieved code contexts are unhelpful or harmful and that selective retrieval produced up to 70% serving speedup without reducing performance in its evaluated completion benchmarks ([paper](https://arxiv.org/abs/2403.10059), [Amazon Science PDF](https://assets.amazon.science/72/9f/e02b3c6645a694854f92d2588fcf/repoformer-selective-retrieval-for-repository-level-code-completion.pdf)).

The supported conclusion is not “always use RAG.” It is: retrieve selectively, expose provenance, test retrieval policies on the actual model and workload, and make stopping/expansion explicit.

### 3. Compact repository maps can be built from structure and ranked to a token budget

Aider is a working primary-source example. It extracts definitions and references with Tree-sitter queries, builds a file dependency multigraph, biases ranking toward mentioned files/identifiers, uses PageRank, renders the highest-ranked definitions, and searches for a representation near a configured token budget ([repository-map documentation](https://aider.chat/docs/repomap.html), [implementation](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py)). Its implementation caches per-file tags against modification time and includes file/identifier inputs in map cache keys.

Tree-sitter itself supplies incremental concrete syntax trees and remains useful even with syntax errors, making it a practical cross-language fallback for structural extraction ([official documentation](https://tree-sitter.github.io/)). It is syntactic, however; name matches are not equivalent to compiler-resolved dependencies.

For semantic navigation, the Language Server Protocol standardizes operations such as definitions, references, and workspace symbols ([LSP specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)). SCIP provides a serializable code-intelligence schema with canonical documents, occurrences, symbols, definitions/references, diagnostics, and symbol relationships. Sourcegraph recommends generating it from a compiler frontend or language server after semantic analysis and snapshot-testing indexers for determinism ([SCIP indexer guide](https://sourcegraph.com/docs/code-navigation/writing-an-indexer), [SCIP protobuf schema](https://github.com/scip-code/scip/blob/main/scip.proto)).

Therefore a stack-neutral Factory can define one graph API while Capability profiles choose the best extractor in this order: compiler/build graph, language-native semantic index, LSP/SCIP, then Tree-sitter/text fallback. The confidence and supported edge kinds must remain visible; a fallback graph must not masquerade as semantic truth.

### 4. Dependency-recorded incremental invalidation is a proven systems pattern

Bazel Skyframe models computation as immutable keyed values produced only through declared dependencies. This creates a data-flow DAG, enables parallel evaluation, and invalidates the reverse transitive closure of changed inputs. Change pruning can retain downstream nodes when a recomputed value is unchanged. Bazel explicitly warns that reading undeclared inputs yields incorrect incremental builds ([Skyframe documentation](https://bazel.build/reference/skyframe)).

That pattern transfers cleanly to derived Factory artifacts: a context slice, map, plan, validation result, or prior Work-atom output is reusable only if every input dependency and policy/tool version in its key remains unchanged. The evidence is for incremental build systems, not directly for LLM context management; applying it to prompts is a design hypothesis grounded in that mature mechanism.

### 5. Module boundaries and architectural constraints can be executable

Bazel target visibility makes a package-level public/private boundary part of build analysis: an undeclared or disallowed dependency fails before execution. Its guidance recommends explicit public interfaces and private-by-default targets ([visibility documentation](https://bazel.build/concepts/visibility)). Bzlmod strict dependencies similarly prevent modules from accidentally using repositories that are merely transitively available ([Bzlmod documentation](https://bazel.build/external/module)).

ArchUnit demonstrates architecture-as-test for Java bytecode. It can encode layered architectures, cycles, dependency rules, and other structural constraints. Its `FreezingArchRule` records an existing violation baseline and fails only on new violations while shrinking that baseline as violations are removed ([official user guide](https://www.archunit.org/userguide/html/000_Index.html)). This is evidence that architectural drift can be made deterministic for supported stacks, not that ArchUnit itself is stack-neutral.

The generalizable mechanism is to compile a versioned Product graph policy into stack-specific checks. The Capability profile must fail closed when it lacks an extractor or rule adapter for a claimed constraint.

### 6. Current coding capability is promising, while long-horizon structural reliability remains unproven

The Qwen3.8-27B model card reports a native 262,144-token context and vendor results including 61.7 on SWE-bench Pro, 42.3 on NL2Repo-Bench, and 42.2 on DeepSWE 1.1. These coding results used a Claude Code harness; the SWE-bench Pro and DeepSWE runs used a 256K context. QwenSWEBench is in-house and used an eight-hour timeout and 32,768 generated-token maximum ([official model card](https://huggingface.co/Qwen/Qwen3.8-27B)). These results show meaningful coding-agent capability, but they do not isolate local quantization, small-context operation, arbitrary greenfield products, or unattended multi-day reliability.

One independently published, reproducible-project result reports 331/500 (66.2%) SWE-bench Verified on a single RTX 5090 using a W4A4 checkpoint, NVFP4 KV cache, LMCache tiers, 262K context, four parallel tasks, and an R2E-Gym scaffold. It is a single operator's result rather than a peer-reviewed benchmark, but its configuration and verdict count make it useful feasibility evidence ([results and harness details](https://github.com/adrienbrault/qwen3.8-27b-rtx5090/blob/main/bench/RESULTS.md)). It supports “bounded repository repair is locally possible,” not “lights-out product creation is solved.”

Model specialization and scaffolding also matter: SWE-smith trained a 32B Qwen2.5-Coder-derived model on successful agent trajectories and reported 40.2% pass@1 on SWE-bench Verified ([NeurIPS paper](https://proceedings.neurips.cc/paper_files/paper/2025/hash/8b86cf5ace600c48fd188efbb8dedec8-Abstract-Datasets_and_Benchmarks_Track.html)). The associated 7B model card describes a model trained on 5,000 trajectories and compatible with SWE-agent ([model card](https://huggingface.co/SWE-bench/SWE-agent-LM-7B)). This is evidence that smaller models can perform nontrivial agent work when aligned to a fixed interface, while also showing that general model size alone does not predict Factory reliability.

Most importantly, SlopCodeBench evaluates repeated extension under evolving specifications. Its reported results found no agent solving a complete problem across the tested models; structural erosion increased in 80% of trajectories and verbosity in 89.8%, with agent code 2.2 times more verbose than the comparison repositories ([paper](https://arxiv.org/abs/2603.24755)). This is recent preprint evidence, not settled consensus, but it directly warns against using passing current tests as the sole definition of success. Longitudinal architecture and complexity gates are required.

## Design hypotheses for the Factory

Everything in this section is a proposed architecture derived from the evidence above. It is not established by those sources and must be validated locally.

### A. Separate the execution graph from the product graph

Use two graph types with different granularity:

- A **Work graph** is a DAG of restartable state transitions. A Work atom has one primary objective, bounded write scope, immutable input references, declared outputs, deterministic acceptance checks, and a retry/escalation budget.
- A **Product graph** describes the generated system: modules, public contracts, allowed dependency edges, runtime interfaces, tests, and requirement/evidence links.

A Work atom may inspect or change one Product module, but the two are not one-to-one. A cross-module contract update may need several sequential Work atoms; one cohesive module may be implemented through many atoms. This prevents “small prompt” from degenerating into a codebase of hundreds of incoherent micro-modules.

### B. Make a Context manifest an auditable input artifact

Each model invocation should receive a generated, persisted Context manifest containing:

1. the exact Work-atom objective and completion schema;
2. source revision/tree digest and clean/dirty-state identity;
3. writable paths and prohibited paths;
4. applicable requirement IDs and acceptance checks;
5. target Product-module contract and allowed dependency edges;
6. exact source spans/files included, each with content digest and retrieval reason;
7. public contracts of direct dependencies and affected reverse dependencies;
8. the smallest relevant tests, diagnostics, and prior failed-attempt evidence;
9. Capability-profile/toolchain versions; and
10. a token count by section plus an omitted-candidates inventory.

The prompt should clearly label authoritative excerpts versus generated summaries. A summary may identify where to look, but any implementation decision based on it should trigger retrieval of the underlying source or contract.

### C. Use progressive, graph-first retrieval

Proposed retrieval order:

1. begin with the atom contract, target module, acceptance criteria, and current deterministic diagnostics;
2. traverse explicitly declared Product-graph edges for direct dependency contracts;
3. resolve mentioned symbols through the semantic index and include definition/signature plus relevant call sites;
4. use lexical/structural search for tests, analogous implementations, configuration, and errors;
5. use semantic/vector ranking only as a candidate generator;
6. render the selected graph neighborhood to a strict initial token budget; and
7. permit the model to request named files/symbols or one-hop graph expansion through a typed tool call.

Every expansion becomes a recorded event and produces a new Context-manifest revision. This preserves auditability and enables measurement of which omitted evidence caused failure.

An initial experimental default of 8K–16K input tokens is reasonable for narrow atoms, with 32K as an explicit expanded tier and larger windows reserved for localization/recovery experiments. These numbers are hypotheses, not evidence-backed universal thresholds; benchmark them against correctness and retrieval recall on Qwen3.8-27B.

### D. Treat context sufficiency and minimality as measured properties, not proofs

There is no reviewed source found that can prove a prompt contains all and only the information required for an arbitrary software change. The practical contract should therefore use observable surrogates:

- **Structural coverage:** all declared direct dependencies, referenced public symbols, applicable policies, and selected test ownership edges are represented.
- **Provenance coverage:** every non-instruction context item resolves to a source revision and digest.
- **Retrieval recall:** on seeded tasks where relevant files/symbols are known, measure whether they appear before the first edit.
- **Context precision:** measure the fraction of included source items subsequently read, cited, modified, or implicated by diagnostics.
- **Expansion rate:** measure how often the initial context requires expansion and whether expansion rescues the task.
- **Ablation:** remove each context class and measure delta in success, repair count, and architecture violations.
- **Counterfactual stale-context test:** deliberately provide a stale derived view while current source remains available; the system must detect the mismatch before editing.

Call a Context policy acceptable only against a workload/profile-specific threshold. Never stamp an individual arbitrary prompt “proven sufficient.”

### E. Invalidate derived knowledge through content-addressed dependency keys

Each derived artifact should be keyed by at least:

`source tree + included path digests + Product graph version + Work atom version + Capability profile + toolchain lock + extractor version + retrieval policy + prompt template + model/quantization/runtime profile`.

On a source or contract change:

1. recompute structural/semantic facts for touched files;
2. invalidate the reverse transitive closure in the Product and Work provenance graphs;
3. recompute affected maps, summaries, contexts, and validation evidence;
4. use change pruning only when the recomputed canonical value/digest is identical; and
5. cancel or rebase queued atoms whose preconditions no longer match.

File modification time alone is insufficient for durable correctness; use content digests and source revisions. The Aider mtime cache is a useful interactive implementation example, while the stronger Factory contract should follow Skyframe's declared-input principle.

### F. Define an enforceable Product-module contract

Each module should declare:

- stable module ID, purpose, and owned domain concepts;
- source roots and generated-code roots;
- public entry points/signatures or external schemas;
- private implementation boundary;
- allowed outgoing dependencies and forbidden layers;
- required module tests and cross-module contract tests;
- data ownership and side-effect boundaries;
- runtime/resource assumptions where relevant;
- size/complexity budgets; and
- a semantic-version or compatibility policy for its public contract.

Do not set one universal line-count limit. Profiles should initially flag, then empirically tune, thresholds such as maximum files per module, public symbols, dependency fan-out, cycle count, cognitive complexity concentration, and source tokens required to render the module's public surface. Split only where cohesion remains clear and the split reduces context without creating excessive cross-module edges.

### G. Compile architecture policy into deterministic conformance checks

For every accepted change, derive the observed graph from source/build facts and compare it with the declared Product graph. At minimum fail on:

- undeclared or forbidden dependency edges;
- dependency cycles where the profile requires a DAG;
- imports across private boundaries;
- public API/schema drift without an approved contract change;
- orphan modules, entry points, or tests;
- module size/complexity budget violations;
- tests no longer mapped to requirements or modules; and
- a graph extractor that failed, is stale, or lacks coverage for the changed language.

Capability profiles should provide adapters for compile/build, test selection, semantic indexing, architecture rules, and graph extraction. Examples include Bazel visibility/strict-deps and ArchUnit; other stacks require equivalent native tools or a documented fallback. The core should consume normalized evidence records, not pretend one parser has equal semantic fidelity for every language.

### H. Make long-horizon quality a first-class evaluation axis

An unattended-factory benchmark should include sequential requirement changes and restart/recovery, not only fresh one-shot products. Track:

- product acceptance pass rate at every checkpoint;
- architecture violations and graph drift;
- public-surface growth and dependency fan-out;
- complexity concentration and duplication/verbosity trends;
- context tokens and model turns per accepted atom;
- stale-context incidents;
- autonomous recovery and quarantine rates; and
- percentage of products completing end-to-end with no human intervention.

This directly tests the failure mode reported by SlopCodeBench and is necessary before claiming lights-out reliability.

## Recommended decision inputs for later Wayfinder tickets

### For “Define the Work atom and context contract”

Adopt an immutable input/output envelope, content-digested Context manifest, one bounded writable scope, deterministic completion checks, explicit context expansion, and provenance-key invalidation. Keep the initial context deliberately small, but optimize its size by measured success/recall rather than a fixed aesthetic limit.

### For “Define the Product graph and module contract”

Adopt a versioned declared Product graph plus a separately derived observed graph. Require cohesive modules with explicit public/private boundaries, allowlisted dependencies, local and contract tests, and profile-specific complexity budgets. Do not equate module count with quality.

### For verification and feasibility decisions

Treat current Qwen and local RTX 5090 results as evidence that bounded coding work is plausible. Treat arbitrary end-to-end construction and multi-day unattended structural stability as unproven. The implementation plan needs a gated prototype that can falsify the atomic-context hypothesis through retrieval ablations, stale-context injection, dependency-change invalidation tests, and sequential product-extension workloads.

## Open questions requiring prototype evidence

1. What initial/expanded context budgets maximize Qwen3.8-27B success per wall-clock hour under the chosen quantization?
2. Does graph-first retrieval outperform lexical search, Aider-style maps, and vector retrieval on the Factory's greenfield and existing-repository workloads?
3. What atom granularity minimizes failed composition and repeated context loading?
4. Which module-complexity limits predict later extension success rather than merely shrinking files?
5. How much semantic-index coverage can each first Capability profile guarantee, and what must fail closed?
6. Can stale-context and changed-precondition detection prevent every queued atom from acting on invalid inputs?
7. Do deterministic architecture gates stop the longitudinal erosion seen in current agent benchmarks without blocking legitimate refactors?

## Source quality and limitations

- Standards, official documentation, source code, and peer-reviewed/preprint papers were preferred; no general web summaries are used as evidence.
- Aider is implementation evidence, not a controlled proof that PageRank maps are optimal.
- Qwen benchmark results are vendor-reported and mostly use a 256K context plus a Claude Code harness. They do not measure the proposed small-context Factory.
- The single-RTX-5090 Qwen result is independently reproducible in principle but remains one repository/operator's report.
- Most retrieval and agent studies evaluate completion or bug repair, not arbitrary greenfield construction.
- SlopCodeBench is a recent preprint, but its measured failure mode is directly relevant enough to include as a prototype requirement.
- No source found establishes a universal way to prove minimal sufficient context or a universal cross-language architecture-conformance graph. Those remain explicit hypotheses and Capability-profile responsibilities.
