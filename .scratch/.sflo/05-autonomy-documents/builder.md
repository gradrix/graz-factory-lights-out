# Approved-document slice builder handoff

## Candidate

Baseline `410a46277af9beb0643af7bee1544380f5f687fb`. Frozen contract SHA256 `89cafb32d3ea7e51898941e9607e115c6ed4ec282bf6927f4c5eceb518d347d7`.

`builder-candidate.json` binds all nine source/test/document paths and their SHA256s. Manifest SHA256: `fba3e2f5fe14c640818808b32242c617b7a2ed78c3b2fbb332e7080764b6f336`. No commits made. Parent-owned run/coordinator artifacts are not part of this mutation unit.

- `gflo/documents.py`: private bounded evidence store, supervised executors, atomic pending publication, hashes, provenance validation, bounded tool-free inference child, offline saved replay and explicit cleanup.
- `gflo/recipes/document.py`: fixed exact-approved HTTPS fetch, separate document retention policy, bounded framed body and controller revalidation.
- `gflo/recipes/document_extract.py`: offline inert UTF-8 HTML/plain extraction with independent parser/text bounds.
- `gflo/__main__.py`: documents acquire/inspect/answer/replay/cleanup public CLI.
- `gflo/worker.py`: optional response-byte cap, preserving existing unbounded-call behavior for existing clients.
- Three document test modules and `docs/document-evidence.md`.

Existing package helper and allowlists/mandatory lock checks are unchanged. No new runtime package, rig operation, model call, GPU operation, service change, browser or search implementation.

## Behavior-first checkpoints

Initial acquisition public-seam test failed without the module, then passed acquisition/inert spans/tamper detection. CLI offline replay and bounded response tests passed after their implementation. New-question test failed with unsupported keyword, then passed: `answer(..., question=...)` and `answer --question` bind a new controller question before inference using cached evidence; no fetch occurs. This is a new answer receipt, never replay mutation.

A concrete owner-death falsifier held a flock in an answer owner and killed that owner after its child began a stalled call. Before correction the child retained the lease. After correction Linux `PR_SET_PDEATHSIG(SIGKILL)`, the fork-to-registration parent-PID race check, and a child-side 120-second alarm terminate it and release the lease. Normal, oversized, failing and cancelled child calls are covered. The child alarm bounds total duration even if a network peer trickles bytes.

Tests exercise exact URL approval, retention restrictions, transport/framing/size/hash failures, redirects without body reads, inert HTML ordering, extraction bounds, fabricated citations, boolean span rejection, insufficient evidence, tool-call rejection, invalid question rejection before inference, failed publication preserving prior evidence, body/text/receipt tamper, links/modes, pending records, quotas without eviction, lease contention, explicit interrupted-work cleanup and the CLI path.

## Execution evidence

- Focused document suite: **27 tests passed**.
- Earlier complete `make coverage`: **112 tests passed, 85% branch-aware coverage** (documents module 86%, document fetch/extract helpers each90%). An initial incomplete test run was81%; retained as honest development history in `/tmp/gflo-doc-coverage.log`, not accepted evidence.
- Final complete `make coverage` after three additional focused tests: **115 tests passed, 86% branch-aware coverage**, exit0. Durable output: `builder-coverage.log`. `git diff --check` passed.
- Initial actual first-source acquisition: `builder-first-acquire.log`, evidence `fe407b52c6d14e2a67923f3fa09ccc1b6622c569c22ffe3cb0c88803622cdb8e`.
- Final-source implementation acquisition: `builder-acquire-v2.json`, evidence `ab25f431729bba8f13b1f18c0b3b03c6588b87c1436a2066f7ca4ba20eb03330`. Exact approved page succeeded without retention-policy relaxation or exceptions. HTTP body EOF is checked beyond declared Content-Length.
- Actual inspect receipts confirm image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, Python3.12.13, runc, UID1000:1000, read-only root, 256MiB memory/swap, one CPU,64PIDs, dropped capabilities/no-new-privileges, bridge fetch and network-none extraction, read-only fixed-input/helper mounts, no devices/GPU/socket/project mounts.
- `local-lifecycle.py` and `builder-local-lifecycle.json`: controlled stalled-fetch injection using the real document Docker envelope and guardian (substituted sleep command, not a real stalled remote server). Cancellation and controller SIGKILL each observed a running container and subsequently zero remaining containers/reusable records. Cancellation removed staging; owner death left private staging, then explicit cleanup removed it. This is actual local executor lifecycle evidence, with injected workload explicitly identified.

## Boundaries and pending independent acceptance

The first source is a historical floating Python3.12 series snapshot, not a guarantee of the runtime patch version. Displayed retrieval age/version are explicit. The supported and unsupported first questions still need the coordinated actual local-model/rig run and independent semantic assessment. Rig container/lifecycle verification is parent-owned and pending. Corpus/independent security and semantic QA are not substituted by builder tests.

Citations validate exact provenance, not entailment. SHA256 and permission checks detect modified records but cannot protect against an attacker controlling the controller account. The HTTP support intentionally requires an unambiguous Content-Length and EOF, UTF-8 plain/HTML, and supported retention policy; redirects, compressed/chunked bodies and unsupported policy fail explicitly. Work limits are15s fetch/5s extraction plus each guardian's explicit105s maximum cleanup grace. No implicit full-store eviction.

The complete Stage4 ten-answer/five-browser-journey gate remains pending. This candidate is only the first approved-document seam.
