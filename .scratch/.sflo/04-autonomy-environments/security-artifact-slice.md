# Independent security assessment: archive slice

Date: 2026-10-02. Skill: security-check. Candidate: `20f93a3fe2abec8d56f3dc2c918983ed59421af4` (frozen private extraction; maintained files untouched).

## Outcome

**Repair required:** one reproduced resource-exhaustion weakness in the archive entry budget. No path escape, overwrite, unsupported-entry extraction, early extraction, or configured transport/expanded-byte limit bypass was observed in the other scoped probes. This verdict covers the archive helper only and grants no Stage 3 acceptance.

## Coverage

Completed the narrow local archive assessment on Python 3.10.12: inspected the frozen helper, its four tests, the accepted contract, ADR 004, the security boundary report, and the corpus definitions. All four frozen unit tests passed. The independent probe recorded 61 successful observations: 27 hash-verified corpus cases, 19 additional hostile header/trailer/path cases, seven boundary/valid controls, instrumented declared-size rejection, five destination protection cases, controlled extraction failure cleanup, and the reproduced directory amplification. A successful defect-reproduction observation is evidence of the finding, not acceptance of the candidate.

Every normal probe monitored destination absence on each input read, including final EOF. Hostile-case checks required absent staging, no leftover spool name, and an unchanged sibling sentinel. Positive controls checked extracted bytes, no links, private root mode, and normalized file modes. One-byte fragmented input passed. Inclusive entry/path/expanded/transport caps passed together; one-byte overflow and multibyte path overflow were rejected. Huge declared ordinary and base-256 sizes were rejected without body materialization; the separate instrumented 129 MiB declaration permitted only a single header read. Additional cases covered invalid checksum, UTF-8 and numeric fields; negative sizes; wrong USTAR version; global PAX and unknown types; prefix-based absolute/traversal names; nonzero padding; malformed trailers; concatenated archives; and trailing nonzero data.

Preexisting file, directory, symlink, dangling symlink, and symlink ancestor destinations were refused before reading the stream, with contents/links preserved. An injected `fsync` failure removed the newly extracted staging tree. These checks assume a trusted controller stream implementation and controller-owned parent directory with no concurrent untrusted filesystem writer, as required by the design.

Coverage outside this slice remains **incomplete and unassessed**: receipt integrity/resolution/publication, stream deadlines/cancellation/owner death, actual disk quotas, failed cleanup reconciliation, preparer isolation, network fetch, executor integration, target runtime/container/GPU behavior, and final environment qualification. No model, container, network, rig, or GPU calls were made. This is not a claim about those later boundaries.

## Finding: implicit directories bypass the entry budget

- **Severity:** medium; **confidence:** high, reproduced.
- **Affected code:** `gflo/artifacts.py:69` counts explicit headers; lines 88–98 collect ancestor paths without charging them to a filesystem-object budget; lines 114 and 116 create those directories during extraction.
- **Attacker control:** an otherwise valid USTAR archive returned by an untrusted assembly/package source.
- **Evidence:** `filesystem-node-amplification` in the retained probe accepted a single zero-byte regular-file entry with a canonical 228-byte path and only 1,536 transport bytes under `ArchiveLimits(entries=1)`. Extraction produced **112 filesystem nodes** (111 directories and one file), despite the one-entry budget. The filename used a six-character unique root plus 110 repeated one-character directory components and a file basename; the USTAR prefix/name split was valid.
- **Impact:** distinct root prefixes let an attacker repeat this pattern within the default 16,384-header budget, potentially creating over a million filesystem objects while using zero declared file bytes and modest transport. This consumes host inodes/directory metadata and extraction/cleanup time outside the intended entry budget. The probe created only 112 temporary nodes; default-limit exhaustion was not attempted.
- **Smallest repair:** before extraction, enforce a controller-owned bound over the union of all explicit paths and their implicit ancestors. Either give that bound its own clear name or explicitly define `entries` to include implicit filesystem objects. Repeated shared ancestors must count once, and later explicit directory headers must not double-count a previously implicit directory. Preserve the early explicit-header cap and reject the complete archive before destination creation.
- **Renewed checks required:** the exploit must reject before staging exists; a tree exactly at the node cap must pass; a shared-parent tree and a later explicit parent directory must not be overcounted. Rerun the retained hostile corpus and controls against the repaired frozen candidate.

## Retrievable evidence

The published evidence consists of this report, `security-artifact-probes/probe.py`, and `security-artifact-probes/results.json`. The JSON preserves the original assessment's candidate identity, source hash, runtime and observations; rerunning the probe does not overwrite it.

The probe reconstructs the exact reviewed commit `20f93a3fe2abec8d56f3dc2c918983ed59421af4` with `git show` into the ignored repository-local directory `.gflo/security-artifact/20f93a3fe2abec8d56f3dc2c918983ed59421af4/`. It imports the helper and reads the corpus from that reconstruction, then runs the frozen maintained artifact tests there. Only trusted files from the fixed commit are reconstructed. Git history containing that commit and Python 3.10 or later are required; no network fetch is performed.

The earlier private `gflo/`, `tests/`, and `evaluations/` copies beside the probe remain local inspection evidence. They are not publication inputs or reproduction dependencies and should not be tracked. New per-probe observations go to `.gflo/security-artifact/20f93a3fe2abec8d56f3dc2c918983ed59421af4/rerun-results.json`.

Reproduce from a clean checkout with the candidate in its Git history:

```sh
python3 .scratch/.sflo/04-autonomy-environments/security-artifact-probes/probe.py
```

The script also runs the frozen maintained artifact tests and returns failure if any probe or unit test fails.

The first run of the new amplification probe incorrectly split the USTAR prefix in the middle of a separator and was rejected as noncanonical. Correcting that test-only generator split to a component boundary produced the documented valid exploit; no product code was changed.
