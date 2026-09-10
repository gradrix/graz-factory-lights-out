# Add bounded development checks, repair edits, verified data and review escalation

Type: task
Status: resolved

## Authorized scope

Owner requests every proposed repair option except changing the model. Keep the
current model/deployment and finite per-attempt context/output/turn limits.

## Requirements

Opt-in worker protocol: run a pinned sandbox development check before final
submission, return retained feedback within the attempt, and support exact unique
text replacements bound to current file hashes. Preserve original source identity,
scope, omitted files, independent final gates and historical plan digests. Never
convert development success into acceptance. Retain draft/check evidence and report
exhausted work as a review handoff with accepted predecessors and failure context.

Provide deterministic, independently verified domain test data through ordinary
read-only bounded execution/context inputs; demonstrate TicTacToe draws/wins without
claiming unaided discovery. Re-run retained failure with the same model and original
independent checks. Keep failures and distinguish repair-only from fixture-assisted
qualification. Publish maintained documentation and portable fixtures/results.

## Answer

Implemented the opt-in `vllm-python-worker-repair-v1` protocol on the same model and
deployment. Existing files require hash-bound unique non-overlapping text edits
(maximum 16 replacements / 8192 bytes); candidate text creates new files. Controller
runs the first pinned gate case for development feedback within existing turns,
retains drafts/checks and repairs across bounded retry, then runs independent final
gates. Historical plan fields/digests and default worker behavior are preserved.

Added trusted-oracle verified example records and an independent TicTacToe adapter,
read-only fixture inputs, CLI review packets and automatic exhausted policy-build
handoffs. Recovery, missing-draft audits, stale/ambiguous/overlapping/out-of-scope
repairs and development-pass/final-fail behavior are covered by regression tests.

Live evidence is mixed and retained. Repair-only passed three tasks then halted.
Assisted planning failed twice with malformed JSON; Codex adapted the prior reviewed
plan. Its four tasks passed gates, but review found square-only “rectangle” tests.
An acceptance finding now blocks that reuse. Added non-square runtime coverage
checks; the first one-file correction trial truncated twice. Requiring small edits
then passed the same task in one response: 6212 prompt / 1695 completion tokens,
28.80 seconds. Twenty generated tests pass, original implementation produces four
assertion failures, and always-True/False potential mutants are rejected. Non-square
coverage and original winner oracle pass. Ninety-one other files, including the
implementation and verified data, survived; accepted replay added no worker calls.

This is supervised reviewed-plan/data-assisted success, not end-to-end autonomous
planning or an unseen benchmark. See [results](../development-repair-results.json).
All fixtures reconstruct from the pinned baseline via the portable helper; raw
runtime evidence remains ignored in `.gflo/evidence/`.

Final validation: 423 tests and 25 subtests passed with Docker checks enabled;
ruff and mypy passed. The model weights and serving deployment were unchanged.
