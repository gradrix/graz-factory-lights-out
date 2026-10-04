# Review evidence grounding: provisional route

Read-only diagnosis of successor case01; no implementation, candidate execution, model/rig calls, contract change or rescore. Final route waits for all four outcomes.

## Observed gap

Sources: `.gflo/executable-review-protocol-trial-1/case-01/{verdict.json,commands/02,commands/07}`, this run's `qa-trial-early.md`, frozen prototype `ops/executable_review_prototype.py`, maintained `gflo/review.py` and `gflo/document_references.py`.

The blocking test-cwd diagnosis is correct. Command02 invokes the original suite and prints `Ran 11 tests` followed by `FAILED (errors=1)`, with `/workspace` causing FileNotFoundError. Its shell pipeline ends in `tail`, so the recorded process exit is nevertheless zero. Command07 runs standalone CLI checks from `/candidate`: three printed equality comparisons are true, and a fourth prints the expected removed path. It does not invoke unittest or modify/rerun the full suite. The final statement that the corrected suite “reports11/11 passing” is therefore an unobserved result. These are successor artifacts; the predecessor's separate corrected-suite experiment cannot supply evidence for this review.

The bare-python complaint is also unsupported as a requirement violation: the approved runtime and command07 support it, and the objective prescribes `python -m unittest`. A genuine host portability consideration does not make it a defect under this objective. Source-location validation cannot decide this question. Severity calibration is another semantic judgment.

## Existing guarantees and missing seam

`review.validate` checks exact shape, bounded text, source path/line existence, severities and decision consistency. It does not bind evidence or repair prose to commands. The executable prototype adds actual-start attestation, bounded captured output, cleanup and unchanged candidate checks, but final prose remains model-authored. Its prompt already prohibits unexecuted-test claims and warns against inferring test success from shell exit: another warning alone is a weak intervention.

Qualified document format3 provides the relevant narrow pattern: model selects strict integer span IDs; the controller supplies exact unchanged excerpts, with catalog binding, occurrence limits and pre-expansion capacity checks. Legacy formats remain readable. It explicitly does not certify semantic entailment. Reuse that separation of responsibilities, not the document domain/schema or its exact size constants.

## Smallest useful next experiment

Keep one reviewer, the existing readonly execution boundary and budgets. Add a versioned final evidence protocol and deterministic execution inventory; no planner, verifier hierarchy or additional inference pass is necessary.

1. Assign stable controller command IDs and bounded output-segment IDs from retained evidence. Bind the catalog to candidate identity, command receipt and captured-byte hashes. Expose exact command, process exit, timeout, output-limited flag and start/cleanup facts. Label process outcome as such, never as “tests passed.”
2. Require observation references on execution-based findings. Model selects IDs; controller materializes exact excerpts. Keep reasoning/inference and proposed correction visibly separate from observations. Static findings may cite bound source excerpts and public requirements without pretending execution occurred.
3. Render “commands executed” from controller records, not a model summary. Label repairs as proposed by default. Do not offer a model-authored `verified repair` flag. A future verified-repair feature would need controller-bound tested-copy identity and explicit scope; an arbitrary shell command editing `/tmp` does not establish those facts merely by having a command ID.
4. Keep the existing decision/path/line/severity checks. A small new wire envelope can be validated and projected into the existing review representation, while retaining the new evidence record separately. Do not silently extend the old exact-key schema or reinterpret saved reviews. Freeze the precise schema and receipt bounds before any successor calls.

Choose bounded segments, not repeated entire tool outputs. Specify raw-byte/decoded-text mapping and invalid-UTF8 handling explicitly; do not silently normalize evidence. Refuse missing or oversized selections, preserve output truncation flags, and cap reference occurrences and canonical expanded bytes before expansion. Uncaptured output cannot be reconstructed or treated as negative evidence.

## What this proves—and does not

| Mechanism | Deterministic guarantee | Remaining judgment |
| --- | --- | --- |
| Command ID + bound receipt | This invocation was attested against this candidate/environment | Whether it tested the claimed behavior |
| Exact output segment | These captured bytes/text were present | Whether the text is truthful or entails the claim |
| Exit/timeout facts | Observed shell-process result | Pipeline/subprocess/test success; command02 demonstrates the distinction |
| Source/requirement reference | Referenced location exists in the bound input | Whether it violates the requirement; the python complaint demonstrates the distinction |
| Separate proposed repair | The report does not label the proposal as an observed rerun | Whether the correction works across all relevant cases |

IDs alone still allow citing the failing suite plus four CLI results to assert eleven passing tests. Exact excerpts expose that mismatch but cannot reject it by provenance alone. Arbitrary commands can also print a fabricated test summary; attested shell start is not a trusted test-runner attestation. Consequently this route improves auditability and removes fabricated execution inventories, but cannot deterministically enforce the complete evidence-truth gate for free-form claims. Independent semantic qualification remains necessary. If eliminating that uncertainty becomes mandatory, a later constrained controller-owned test runner is a different, larger boundary—not a small citation change.

## Finite qualification before promotion

Use paired conforming/defective saved-evidence controls: correct original-suite failure plus proposed cwd repair; four CLI observations incorrectly promoted to full-suite pass; exit-zero pipeline with failed suite; printed fake success; speculative out-of-objective portability claim. Structural controls should reject unknown/bool IDs, swapped catalog hashes, absent start/cleanup proof, invalid segments and expansion overflow. Semantic counterexamples should be explicitly expected to remain structurally valid where provenance is real, and must fail the independent truthfulness assessment. This avoids claiming that reference validation solved entailment.

Preserve this trial and its failures. A successor needs a new frozen prompt/wire/receipt contract, paired controls and fresh qualification; no changes to current verdicts or budgets are implied. Recommendation is provisional pending the remaining cases, especially whether they show the same evidence overstatement or a different failure mode.
