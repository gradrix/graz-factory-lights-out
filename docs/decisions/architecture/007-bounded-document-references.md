# Bounded references instead of copied document quotes

Status: chosen for implementation; acceptance pending. Decision maker: agent,2026-10-04, under continuing incremental local-factory authorization.

The actual ten-question trial of exact quotes plus one structural repair produced8 accepted answers and2 persistent punctuation failures. Independent review found correct requested facts in both failed cases, but the model repeated straight punctuation where the source used curly characters. All attempts remain failures under their original contract. See [trial QA](../../../.scratch/.sflo/07-autonomy-document-reliability/qa-rig-documents.md).

Supersede the new-answer format choice in [validation repair](006-document-validation-repair.md). Keep its bounded lifecycle, durable attempts and extractor change. Introduce format3: model-selected source span IDs, exact whole-span citations supplied by the controller, with explicit encoded field/count/aggregate bounds before expansion. The current sources need at most1117 encoded bytes per span; a2048-byte selected-span bound covers them. Long selected spans fail explicitly; segmentation is deferred until a real need earns its complexity.

The previous reference prototype exposed unbounded expansion and long-span failures. The [successor contract](../../../.scratch/.sflo/07-autonomy-document-references/contract.md) addresses these directly with at most8claims/16reference occurrences,48KiB canonical answer,12KiB metadata and the unchanged64KiB receipt ceiling. Existing format1/2 readers and exact reconstruction remain immutable. No historical outputs are rewritten or rescored.

Selecting the right passage and making supported claims remain model tasks. The controller guarantees only the source identity and exact bytes; independent complete-answer semantics remain required. Acceptance needs ten repeated diagnostic questions plus three frozen fresh questions on the actual rig and offline cross-version replay. No accepted reliability rate or broad research capability is inferred before that evidence exists.
