# Orchestration foundations for a local lights-out software factory

Research snapshot: 2026-09-02. SFLO was inspected at commit
[`b05be71`](https://github.com/simonasrazm/simon-factory-lights-out/tree/b05be71c603f4af4af4619dd2bd78de118fb92f5);
Gas City at
[`6e441be`](https://github.com/gastownhall/gascity/tree/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780).
The conclusions below distinguish documented behavior from design inference.

## Decision

Do **not** make either SFLO or Gas City the first implementation's owning core.
Build a small purpose-specific, model-independent orchestration core, and adapt
the strongest contracts from both:

- from Gas City: materialized dependency graphs, durable work records independent
  of sessions, readiness through blocking edges, append-only events, bounded
  retries that create new attempts, reconciling disposable workers to durable
  work, declarative reusable workflow/capability packages, and runtime adapters;
- from SFLO: explicit artifact-producing stages, fail-closed stage sequencing,
  separate builder/reviewer/product-verifier roles, bounded review loops,
  per-run state directories, archived rejected artifacts, and a simple local
  Ollama integration to learn from—not to adopt unchanged;
- from OpenHands and SWE-agent: use or imitate a mature coding-agent execution
  harness (typed tools, workspace isolation, trajectory/persistence, context
  condensation) behind the worker boundary instead of rebuilding the entire
  action/observation loop inside the scheduler.

The first core should own only: `ProductSpec`, `ProductGraph`, `WorkAtom`,
dependencies, attempts, evidence, gate results, leases, events, and recovery.
Use SQLite in WAL mode plus immutable artifact files/content hashes as the
initial durable substrate. Run one inference-heavy worker at a time on the RTX
5090; allow deterministic checks and cheap non-inference operations to run in
parallel. Put SFLO-like product phases in versioned workflow profiles above the
core, not in its state machine.

This is a composition decision at the level of **ideas and interfaces**, not a
three-framework runtime stack. Embedding SFLO inside Gas City and then embedding
an agent framework inside both would multiply state authorities and recovery
semantics.

## Why neither project is the owning core

### SFLO: useful policy reference, wrong work granularity

SFLO is a compact Python implementation of a fixed gated product pipeline. Its
default stages are Discovery, Build, QA, Security, PM Verification, and Ship,
with QA/Security and PM rejection loops. Each stage must produce a Markdown
artifact before the scaffold advances. The project explicitly describes the
scaffold as the pipeline authority and bounds rejecting-gate and outer loops at
ten ([core protocol](https://github.com/simonasrazm/simon-factory-lights-out/blob/b05be71c603f4af4af4619dd2bd78de118fb92f5/sflo.md),
[default pipeline](https://github.com/simonasrazm/simon-factory-lights-out/blob/b05be71c603f4af4af4619dd2bd78de118fb92f5/pipeline.yaml)).

That is a valuable product-level quality policy, but the unit of scheduling is
still a whole role/gate. A single Developer invocation may be responsible for
the whole product tree. SFLO has a deterministic parser that derives a
deliverable dependency DAG and groups it into epics, but this is downstream of
an LLM-authored `SCOPE.md`, and the core pipeline is not a general durable
work-atom scheduler ([decomposition source](https://github.com/simonasrazm/simon-factory-lights-out/blob/b05be71c603f4af4af4619dd2bd78de118fb92f5/src/decompose.py)).
For a 27B local model, the missing abstraction is precisely the most important
one: a small, independently leased, independently validated unit with a context
budget and a durable attempt history.

The word “gate” also overstates how deterministic the default checks are. SFLO
does verify required artifact/deliverable-file existence and supports custom
validators, but its default QA, Security, PM, and Ship gates primarily parse
model-authored Markdown for grades, critical-count fields, verdicts, and
decisions. A model can therefore provide much of the evidence that releases its
own gate ([validator source](https://github.com/simonasrazm/simon-factory-lights-out/blob/b05be71c603f4af4af4619dd2bd78de118fb92f5/src/validate.py)).
For the proposed Factory, executable checks must author gate truth; model reports
may add findings but cannot certify success.

SFLO's durability is intentionally small and understandable. A factory has an
isolated directory with `state.json`, logs, locks, and gate artifacts. State is
written via temporary-file replacement; brief write locks and a process-lifetime
runner lock recover dead PIDs; a resumed run preserves gate states and retry
counters; rejected/stale artifacts are archived instead of deleted
([state source](https://github.com/simonasrazm/simon-factory-lights-out/blob/b05be71c603f4af4af4619dd2bd78de118fb92f5/src/state.py),
[runner source](https://github.com/simonasrazm/simon-factory-lights-out/blob/b05be71c603f4af4af4619dd2bd78de118fb92f5/src/runner.py),
[archive source](https://github.com/simonasrazm/simon-factory-lights-out/blob/b05be71c603f4af4af4619dd2bd78de118fb92f5/src/archive.py)).
That is good crash hygiene for one linear process, but not enough for leases,
atom-level idempotency, concurrent deterministic jobs, graph evolution,
quarantine, or recovery after a worker dies between code mutation and result
recording.

The runtime boundary is more reusable. SFLO has adapters for Codex, Claude
Code, Cursor, OpenClaw, and Ollama. The Ollama adapter exposes filesystem and
shell tools, uses either native or text-form tool calling, caps turns and total
time, detects three identical tool calls, and truncates selected tool results
([Ollama adapter](https://github.com/simonasrazm/simon-factory-lights-out/blob/b05be71c603f4af4af4619dd2bd78de118fb92f5/src/adapters/ollama.py)).
However, it retains an ever-growing message list for the entire gate, gives
workhorse roles broad shell access, has no VRAM admission control, and has no
explicit per-prompt context manifest or token budget. Its default configuration
is expressly tuned for OpenAI/Codex models, not Qwen, and its published
evaluation is a modest, non-independent task sample without systematic
end-to-end latency measurement
([evaluation limitations](https://github.com/simonasrazm/simon-factory-lights-out/blob/b05be71c603f4af4af4619dd2bd78de118fb92f5/docs/evaluation.md)).

**Adapt from SFLO:** stage artifact contracts, fail-closed transitions, bounded
repair/escalation, per-run isolation, archive-first debugging, pluggable role
instructions, and the adapter test cases. **Do not adopt:** whole-product gate
invocations, Markdown grades as authority, fixed role topology, shared mutable
working tree without atom leases, or unbudgeted conversation accumulation.

### Gas City: strongest substrate, too much initial machinery

Gas City is not a fixed factory. It is a Go orchestration-builder SDK whose core
primitives are configurable Agents, durable Beads, reusable Formula graphs,
Rigs, composable Packs, and append-only Events. Formulas materialize into work
records that outlive both the formula file and agent session; dependency edges
make blocked work invisible until prerequisites close; a controller reconciles
configured sessions with running sessions; sessions are disposable while work
remains durable
([system model](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/docs/getting-started/how-gas-city-works.md)).
This is much closer to the required architecture than SFLO.

Formula v2 is especially relevant. It compiles authored workflows into a flat
graph of independently routable work and orchestrator-owned control records.
It supports executable check loops, bounded retries with hard/soft exhaustion,
fan-out drains capped at 100 units, scope failure policy, and a workflow
finalizer. Retries append new attempt records rather than reopening history;
the logical step remains the stable dependency target
([Formula v2 specification](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/docs/reference/specs/formula-spec-v2.md)).
These semantics should be copied nearly verbatim into the Factory's WorkAtom
protocol.

The controller is a genuine reconciliation loop: it periodically rebuilds the
desired worker set, reconciles sessions, dispatches orders, detects config
fingerprint drift, restarts missing/drifted workers, captures crashed-session
output, drains gracefully, and uses a single-controller lock. The runtime
provider interface separates start/stop/interrupt/liveness/interaction from the
orchestrator and explicitly distinguishes “not found,” “initializing,” and
“runtime observation failed,” so an observation failure is not mistaken for
proof that all sessions disappeared
([controller architecture](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/engdocs/architecture/controller.md),
[runtime interface](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/internal/runtime/runtime.go)).
Those are excellent recovery patterns.

Gas City also separates harness, model, model-serving upstream, transport, and
runtime. It can point a Codex-compatible harness at an OpenAI-compatible local
endpoint such as vLLM, or define a custom harness, and can use local subprocess
sessions. Workspace/rig/agent concurrency caps can force a single active model
session
([agent configuration](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/docs/guides/configuring-an-agent.md),
[harness recipes](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/docs/guides/harness-recipes.md),
[configuration reference](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/docs/reference/config.md)).
It is therefore possible to run Gas City against a local Qwen service, but
“possible” is not the same as “the right minimal kernel.” Gas City manages
agent CLIs, not GPU inference scheduling, KV-cache pressure, or prompt-size
admission; those would still be ours.

Three facts argue against adopting Gas City wholesale for v0:

1. Its production multi-step formula path is currently coupled to the `bd`
   Beads backend; the in-memory and file stores intentionally implement a
   smaller model. The project documents that it lacks a general in-process
   parser for the main runtime and that step materialization is backend
   dependent
   ([formula architecture and limitations](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/engdocs/architecture/formulas.md)).
2. The standard installation requires tmux even when another session backend
   is used, while the production `bd` route adds Dolt and `flock`; the README
   explicitly offers a file store only as the lighter alternative
   ([requirements](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/README.md)).
3. Its scope is a fleet/multi-project operations platform: packs, imports,
   remote runtimes, API/dashboard, mail, orders, supervisors, multiple stores,
   pool scaling, and compatibility surfaces. That is valuable mature
   machinery, but it creates a large operational and conceptual surface before
   the central hypothesis—whether one small local model can reliably complete
   tiny contract-bound atoms—has been proved.

Gas City also makes an important safety boundary explicit: configured commands
and imported packs are trusted operator code, not a sandbox; bead text and
other external content are untrusted data and must not be interpolated into
shell commands
([trust-boundary specification](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/docs/reference/trust-boundaries.md)).
The Factory needs an additional isolation boundary for generated code and model
tools, not merely the command hygiene of an orchestration SDK.

**Adapt from Gas City:** its domain vocabulary and graph/retry/reconciliation
semantics. **Defer or omit:** Dolt/Beads, tmux-first lifecycle, fleet scaling,
mail, registry, remote control plane, multi-city support, and generalized pack
distribution. Keep an adapter seam so a later milestone can either export
WorkAtoms to Gas City or replace the small scheduler if Gas City's operational
benefits become necessary.

## Directly relevant complements

### OpenHands: candidate worker harness, not factory scheduler

The OpenHands Software Agent SDK supplies the pieces below the WorkAtom boundary:
a provider-neutral LLM interface, typed tools/actions/observations, local or
Docker workspaces, agent lifecycle, context condensation, and conversation
persistence. Persisted conversations contain base state plus individually
numbered event files; the same API can move from a local to an isolated remote
workspace
([SDK architecture](https://docs.openhands.dev/sdk/arch/sdk),
[persistence contract](https://docs.openhands.dev/sdk/guides/convo-persistence),
[agent-server isolation](https://docs.openhands.dev/sdk/guides/agent-server/overview)).
Its official docs explicitly include Qwen and other open models and identify the
SDK as MIT-licensed ([SDK overview](https://docs.openhands.dev/sdk/index)).

This can save substantial work if local-Qwen tool behavior benchmarks well.
However, a persisted Conversation is still one agent task/trajectory, not the
Factory's product graph, leases, deterministic gate authority, or unattended
cross-task reconciliation. Wrap it as `WorkerRuntime`; never make conversation
state the product/workflow source of truth.

### SWE-agent: useful bounded-loop and replay evidence

SWE-agent's current source persists the action/observation trajectory during
execution, saves the exact config needed to repeat an instance, has format and
context-window failure classes, supports retry/reviewer loops, and terminates
after repeated timeouts
([agent loop source](https://github.com/SWE-agent/SWE-agent/blob/3ea751c087f32b16e039a2233dd6eefecef325d5/sweagent/agent/agents.py),
[trajectory format](https://github.com/SWE-agent/SWE-agent/blob/3ea751c087f32b16e039a2233dd6eefecef325d5/docs/usage/trajectories.md)).
Its Agent-Computer Interface philosophy and concise tool surface are useful for
a small model. Like OpenHands, it is an execution harness/experiment runner,
not a durable multi-atom factory. Treat its trajectory and retry mechanisms as
worker-level evidence, not workflow state.

## Comparison

| Concern | SFLO | Gas City | Recommended local core |
|---|---|---|---|
| Owning unit | Whole role/gate artifact | Durable bead/graph step | Small WorkAtom with declared context and evidence |
| Workflow | Mostly fixed sequential stages and loops | Declarative materialized DAG, fan-out, control records | Small typed DAG; product phases supplied by profiles |
| Durable truth | Per-factory JSON + artifacts | Bead store + events + session records | SQLite ledger + content-addressed artifacts + event journal |
| Recovery | Resume gate; keep partial files; three spawn retries; bounded review loops | Reconciliation, persistent work, disposable sessions, crash capture, bounded retry records | Lease expiry, attempt append, workspace recovery/quarantine, reconciliation |
| Gates | Artifact shape and model-authored grades by default; custom validators possible | Formula checks and dependency/finalizer semantics; product policy supplied by pack | Deterministic commands/scenarios are authoritative; model reviews advisory |
| Routing | Scout selects role agents; gate order | Ready-work queries, dependencies, formulas, pools, rigs | Capability matching + dependency readiness; inference concurrency = 1 initially |
| Runtime coupling | Explicit adapters including Ollama; defaults tuned to Codex models | Strong session/harness/upstream/runtime separation; not a GPU scheduler | OpenAI-compatible inference adapter + replaceable worker harness |
| Modular reuse | Agents, skills, pipeline config, custom gates | Packs, formulas, providers, stores, typed domain interfaces | Capability profiles + workflow templates + versioned schemas |
| Isolation | Working directory/tool policy; not a code sandbox by default | Runtime-pluggable, but configured commands are explicitly trusted | Per-attempt git worktree plus container/namespace policy |
| Fit on one 5090 | Runs sequentially but prompts can be gate-sized and history grows | Can cap sessions at one, but fleet substrate is operationally large | Designed around one inference admission token and many cheap checks |

## Contracts to carry into the architecture plan

1. **One durable authority.** A worker conversation, git branch, report, or
   process is evidence—not scheduler truth. Only the ledger transitions atom
   state.
2. **Materialize before execution.** Compile a workflow/profile into immutable
   atom records and dependency edges before workers see it. Record the workflow
   version and input hashes.
3. **Lease; do not “assign forever.”** A runnable atom is atomically leased to
   an attempt. Lost heartbeat/worker causes lease expiry and reconciliation;
   history is never rewritten.
4. **Append attempts.** Repair and transient retry create a new attempt with a
   reason and budget debit. The stable atom ID remains the downstream edge
   target.
5. **Separate failure classes.** Distinguish inference/runtime failure,
   malformed worker result, deterministic validation failure, architecture
   conflict, and exhausted recovery. Never let free-form model text choose the
   retry class without mechanical corroboration.
6. **Evidence-owned gates.** A gate references command, environment digest,
   exit status, structured results, artifact hashes, and timestamps. An LLM
   review is another evidence item, never the sole pass bit.
7. **Context is an artifact.** Each attempt receives a hashed ContextManifest:
   task contract, relevant product-graph neighborhood, exact source excerpts,
   applicable capability rules, prior failure evidence, and hard token budget.
   The model must not inherit an unbounded conversation.
8. **Inference admission is global.** Start with one active Qwen generation.
   Deterministic validators, indexing, and workspace preparation may overlap;
   a later benchmark may admit limited short-context batching.
9. **Workspace state is explicit.** Each attempt works in an isolated git
   worktree/container. On success, a merge/integration atom incorporates it;
   on ambiguity or exhaustion, quarantine the workspace with full evidence.
10. **Reconcile from observation.** A supervisor compares desired/runnable
    atoms, leases, processes, and workspaces with observed state. Observation
    failure must be represented as unknown, never “absent.”
11. **Profiles, not built-in roles.** “PM,” “developer,” and “security” belong
    in a capability/workflow profile. The kernel knows capabilities, inputs,
    outputs, dependencies, and gates.
12. **Version every reusable behavior.** Capability profile, tool schema,
    workflow formula, prompt template, validator, model/server configuration,
    and product-graph schema versions are part of attempt provenance.

## Minimum implementation boundary

The first executable architecture should be deliberately smaller than both
projects:

```text
factoryd
  SQLite ledger + event journal
  DAG/readiness + lease/retry/reconciliation
  inference admission controller (capacity 1)
  artifact store
  workspace manager (git worktree + optional container)
  deterministic gate runner
  WorkerRuntime interface

profiles/
  greenfield-service workflow
  capability profiles for one or two prescribed stacks
  validators and product-module rules

worker adapter
  OpenHands SDK, SWE-agent-derived ACI, or a thin local harness
  -> OpenAI-compatible local Qwen endpoint
```

Do not implement a dashboard, multi-host execution, pack registry, mail system,
or broad stack catalogue before the atom protocol passes unattended recovery
tests. Preserve an event/export API and provider interfaces so those can be
added without migrating the domain model.

## Maturity and licensing

Both target projects are MIT-licensed
([SFLO license](https://github.com/simonasrazm/simon-factory-lights-out/blob/b05be71c603f4af4af4619dd2bd78de118fb92f5/LICENSE),
[Gas City license](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/LICENSE)),
so their code and designs are legally reusable subject to preservation of the
license notice. At this snapshot SFLO has no GitHub release and is a small,
young repository; its own evaluation warns against universal claims. Gas City
has tagged releases (latest observed: v1.4.1), a very large test and code
surface, detailed architecture documents, and active operational fixes
([releases](https://github.com/gastownhall/gascity/releases),
[changelog](https://github.com/gastownhall/gascity/blob/6e441be0ae8b95a691f4c26fd1ba4b9eb5ed1780/CHANGELOG.md)).
That makes Gas City the stronger semantic reference and a credible future
integration target, but its breadth and ongoing churn strengthen—not weaken—the
case for proving the local-model hypothesis behind a smaller stable boundary.

## Validation questions for later tickets

- Can Qwen reliably emit the proposed typed WorkerResult and tool calls at the
  selected quantization/context sizes? Documentary inspection cannot answer
  this.
- Does OpenHands, SWE-agent, or a thinner harness yield the best completion and
  recovery rate under identical WorkAtoms? Benchmark all behind one interface.
- Which Gas City Formula v2 concepts can be adopted without reproducing its
  backend-specific complexity? At minimum: stable logical step, appended
  attempts, dependency readiness, check/retry distinction, finalizer, and
  bounded fan-out.
- Can deterministic validators cover enough of product intent to permit true
  lights-out completion, or must some product classes stop at a human approval
  gate? This is an evaluation result, not an orchestration assumption.
