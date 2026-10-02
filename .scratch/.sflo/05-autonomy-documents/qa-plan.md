# Independent QA inputs: document evidence first slice

**Prepared, not executed against a candidate.** Applied s-qa planning scope. Frozen synthetic corpus `.gflo/document-qualification`, manifest SHA256 `b64057c86cc893f1ab9cc665e4f8daa2f7a06231d1cffa07eeaa0ab13d6bb4b3`. Manifest binds the contract digest and every corpus file; self-check verifies all hashes, six raw cases and positive/negative UTF8 encoding controls. No acceptance claim.

## Small corpus

- `cases.json`: benign HTML/plain separator facts, Unicode/entity preservation, excluded comments/scripts/style/template, hostile fake system/tool/URL instructions retained as inert visible text, empty extraction, malformed UTF8 and unsupported JSON media type.
- `answer-controls.json`: supported separator answer; unavailable future release date; invented evidence ID/span/excerpt; fabricated model URL; correctly quoted but unsupported claim; hostile text cannot grant authority. The latter separates provenance validation from independent entailment review.
- `replay-controls.json`: restart with fetch/model clients that fail on invocation; same saved answer and citations, historical timestamp/version/age; explicit errors for missing/corrupt/pending evidence. Explicit re-answer remains separate.
- `limits-plan.json`: generate bounded disposable edge pairs after interface freeze, rather than store giant fixtures.

Synthetic facts do not stand in for the real approved Python documentation snapshot. Live qualification must retain exact retrieval/version and hashes and test the contract's answerable/unsupported questions. No exact prose keywords or unspecified whitespace/block grouping imposed.

## Interface coordination

Builder supplied approval `{url,source_version,question,expected_sha256?}`, one-based spans, and answer `{status,claims,reason}` with citations `{evidence_id,span,excerpt}`. Supported answers require claims/citations and empty reason; insufficient answers require empty claims and nonempty reason. Bind future adapters to the actual frozen candidate. Use resolved IDs/spans rather than predicted fixture IDs; preserve semantic controls unchanged. No model-trial private answers inspected.

## Candidate QA sequence

1. Validate benign acquire→resolve→answer→restart/replay at public CLI/module seams. Run actual offline extraction container on benign and hostile raw bodies; prove deterministic spans and zero asset execution. Verify exact image/runtime/network/resource/mount facts independently.
2. Pair each rejection with a conforming control: URL/path approval, mixed/private DNS, TLS mismatch, redirects/non200, length/frame/encoding/hash and retention/Set-Cookie policies. Use in-memory transport doubles for external failures; record where actual container execution resumes.
3. Interrupt actual fetch and offline extraction separately, then inject cancellation at publication; kill only an owned controller. Confirm exact owned container removal, no reusable partial record, prior-good hashes unchanged, and recovery. Repeat cleanup/publication failure through the new document path rather than assume environment evidence suffices.
4. Independently tamper disposable body, text, receipt and answer; try missing/invented IDs, pending marker and linked file replacement. Verify rejection on resolve and offline replay. Exercise record/byte caps with explicit full-store refusal and no implicit eviction; verify reserved headroom.
5. Mock one answer request to inspect no tools, frozen question/evidence, configured output/thinking/time bounds and no fallback. Run structural citation controls, then separately assess logical support. Network/model-disabled replay must invoke neither client and preserve stored answer content while displaying current age.
6. After functional/security candidate freeze, independently assess actual rig facts and first fresh local answer/citations. Historical failures stay recorded; first-slice success does not close the full ten-answer/five-browser-journey Stage4 gate.

## Limits and provenance

No product modifications, fetches, service changes, models or GPU calls were made. Corpus is compact and schema-neutral where implementation choices are not contract requirements. Actual parser event/depth/block counting must be identified before generating edge cases; do not invent stricter counting policy or retroactively relax budgets. Freeze/version any required corpus correction before affected model qualification.
