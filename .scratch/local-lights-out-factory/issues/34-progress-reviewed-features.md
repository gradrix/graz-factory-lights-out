# Progress reviewed features through accepted bases

Type: task
Status: resolved

## Requirement

Execute a reviewed task graph sequentially against immutable cumulative snapshots.
Revalidate every provider acceptance and finding before reuse, bind downstream work
to exact accepted evidence, and retain independent combined gates. Resume from
ledger/artifacts without trusting a mutable progress summary. Preserve original
request/proposal/review bindings and omitted source; do not erase task dependencies.
Test stale bases, failed providers, findings, changed contracts, recovery, and final
integration failure. Trial the local model on a complete bounded feature and record
its failures honestly. Hierarchical planning remains an empirical qualification,
not an assumed capability from adding manager roles.

## Answer

Implemented `gflo.progression` and `run-feature`: deterministic sequential reviewed
graphs, immutable accepted-base progression, predecessor evidence/finding checks,
validation-only combined gates, and replay without mutable progress summaries.
Snapshot workers use an explicit provenance profile; legacy profiles still reject
unsupported dependency artifacts. Direct consumer Controller reuse also rechecks
ancestor findings. No Git promotion or larger sandbox capability was added.

Snapshot planning now takes repository references and bounded context with explicit
coverage. Consumers may reference paths provided by ancestors; missing files still
block preparation. Original request/proposal/review identities are retained through
progression. Tests cover interruption, failed providers/final gates, stale external
source, changed review, late findings, direct consumer reuse, unsupported dependencies,
CLI execution, unchanged candidate lifting, and bounded snapshot planning.

The live model planned four tasks; three complete executions accepted 12/12 tasks
in 12 attempts and passed independent combined gates. The ambiguous-product probe
failed by rereading; the first clarification interface exposed envelope failures.
Planning v3 with clarification-only output and explicit envelope returned blocking
questions. A v3 three-task plan also executed successfully. All failed/successful
stages are in [results](../feature-progression-results.json), with a portable
[fixture](../feature-progression-fixture.json). Host suite: 353 passed, eight optional
skips, 25 subtests. Ruff and mypy passed.

Next qualification is diverse products and interface/selection failures before
recursive manager delegation. Indexing, larger isolated workspaces, native promotion,
and automated environment/product decisions remain future work, not demonstrated
capabilities. No inference was made that more manager agents alone solve model limits.
