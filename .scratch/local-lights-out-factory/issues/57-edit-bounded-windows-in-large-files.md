# Edit bounded source windows in large files

Type: task
Status: resolved

## Evidence

The user wants large files to work within small worker context. The existing repository
index/read interface found a two-line function at lines 5001–5002 of a 10,002-line,
207,814-byte Python file. The existing whole-file worker projection tokenized to
128,684 tokens against a 16,384-token deployment limit and correctly refused inference.
See large-file-context-results.json. This is a real worker-input limitation, not evidence
that the model needs to remember the entire repository or that indexing is absent.

## Scope

Add an opt-in worker protocol for bounded revision-bound source windows, integrating
existing repository/symbol reads. Bind edit handles to the full original file digest,
contract and visible range. Preserve unseen bytes exactly; reject stale handles and
edits outside granted visible ranges. Keep independent validation on the complete
candidate and explicit coverage/omission records. Preserve old worker and replay semantics.

Qualify a meaningful edit in the recorded 10,002-line file under the existing context
budget, with checks for the new behavior, unchanged unrelated bytes, imports/callers,
stale source and insufficient context. Add another real-file qualification before
claiming broad large-file capability. Do not raise model context or load whole files
into prompts. SourceBundle's 256 KiB execution limit is a separate later migration
constraint; do not claim arbitrary file-size support from this first windowed trial.

No model/deployment change or human product-policy decision is required for this task.

## Answer

Implemented opt-in windows-v1 across model, controller and prepared-task context.
Full-source/contract/range bindings preserve unseen text; bounded symbol navigation and
explicit omissions use the existing repository reader. Legacy records remain unchanged.
Seven focused tests cover range/scope/staleness, CRLF, large source, oversized lines,
model wire evidence, controller gates/replay and prepared execution context.
See [qualification](../window-qualification/README.md) for both successful GPU trials,
all fixture failures, challenged acceptance, responses and reproduction recipes.
Large-file planning and larger execution inputs remain follow-up work.
