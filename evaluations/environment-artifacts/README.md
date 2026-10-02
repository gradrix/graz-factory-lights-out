# Environment artifact acceptance corpus

Finite independent fixture inputs for the future Stage 3 public environment prepare/inspect seam. Grounded in ADR 004, the environment security boundary review, and the implementation handoff. This corpus implements no runtime feature and grants no Stage 3 acceptance. Stage 2 remains the implementation gate.

## Archive cases

`cases.json` defines 27 deterministic uncompressed USTAR byte streams: two ordinary controls and 25 rejection cases. Every case supplies transport, entry-count, expanded-byte and path-byte bounds, expected accept/reject result, reason and observable consequence. The manifest repeats these expectations and binds every artifact hash.

Coverage includes duplicate and normalized duplicate paths, file/ancestor conflicts in both orders, traversal, absolute paths, symbolic/hard links, arbitrary `.bin` symlinks, character/block devices, FIFO, sparse type and sparse PAX metadata, unsupported path/name overrides, entry-count and expanded-size overflow, huge declared output, transport overflow, truncated header/payload and a late bad entry following a valid one.

Default fixture limits are 32 KiB transported, eight entries, 4 KiB expanded and 100 path bytes. Cases may override a limit. These are trusted acceptance-test bounds, not new production limits or model-provided settings. A future implementation may exercise them through a narrow controller-owned test configuration. All regular-file declared lengths contribute to expanded bytes; all headers contribute to entry count. Incoming transport includes headers, padding and trailer. Equality with a cap is allowed.

Path identity is POSIX relative identity: `./package/x` and `package//x` alias `package/x`. A stricter implementation may reject noncanonical paths outright. Either response rejects the ambiguous duplicate fixtures. Only ordinary files/directories are accepted by this corpus. It does not qualify any PAX/GNU extension subset. An explicit future npm `.bin` omission policy needs its own qualified layout; an arbitrarily named `.bin` never authorizes skipping a link.

The 129 MiB declared-size case contains only one 512-byte header, so no huge file is stored or allocated. That stream is also incomplete; mere rejection cannot by itself prove early size enforcement, bounded memory, or a read deadline. Its consequence requires a future instrumented streaming test to show rejection without allocating or waiting for the declared body. The complete 4097-byte expanded-total case independently isolates aggregate size enforcement without truncation.

## Receipt and publication acceptance plans

`receipt-publication-scenarios.json` contains 13 concrete future public-seam scenarios: a valid immutable binding; byte/path/mode/link/receipt tampering; unsafe receipt paths; failed validation/publication; cancellation before publication and during transport; cleanup failure; and preexisting destination links. They specify preconditions, operations and observable outcomes, without assuming private helper names or inventing a generic fault-injection framework.

Start these scenarios from a receipt returned by the eventual public preparer. Receipt format and canonical tree serialization remain implementation choices consistent with the accepted contract. `valid-tree-records.json` supplies independent relative paths and content hashes, not a mandated tree-hash algorithm. Final safe modes/owners are controller-selected; meaningful execution-mode changes must invalidate a receipt. No scenario was executed during fixture preparation.

Failure means no runnable partial artifact, no outside or preexisting-destination write, and no alteration of the prior good receipt. Publication must be atomic, and cancelled/superseded attempts remain ineligible even after a delayed successful smoke result. Cleanup failure must remain explicit and prevent failed-attempt reuse until reconciled.

## Validation and limits

`private/generate.py` deterministically constructs the small archives. `private/validate_headers.py` reads raw bounded headers only, verifies checksums and inventories, checks intended truncation, and compares deterministic regeneration in a disposable directory. Neither uses extraction APIs, follows archive links, executes payloads or allocates by declared file size.

Header validation confirmed 27 inventories, 73,324 total archive bytes, and a largest archive of 7,168 bytes. It is fixture integrity evidence, not evidence that an implementation rejects the attacks. No maintained product files, rig, cohort D, containers or GPUs were touched. Public fetch restrictions, device/cgroup isolation, actual executor cleanup and profile/model success require their separate gates; this corpus covers archive/receipt inputs only.

The corpus is frozen by `manifest.json` and `MANIFEST.sha256`. Keep it outside target model contexts. After exposure, corrections require a new version preserving original fixtures and results.
