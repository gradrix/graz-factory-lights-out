# Independent security recheck: archive slice

Date: 2026-10-02. Skill: security-check. Frozen repaired candidate: `0c9c7c8fffdc6d16f316a3650cd28a78ab265095`. Frozen `gflo/artifacts.py` SHA-256: `53f94a54cdc948a752ab757c7f4bf943319073d71d82a601844a7d3825516b48`.

## Outcome

**Pass for this narrow archive slice.** The directory amplification finding from candidate `20f93a3` is repaired. No remaining actionable security defect was found within the assessed boundary. This permits progress to integration; it grants no complete Stage 3 or environment-preparer acceptance.

## Coverage

Completed the scoped recheck under Python 3.10.12 against a private extraction of the repaired commit. The original candidate, exploit and findings remain available in `security-artifact-slice.md` and `security-artifact-probes/`.

All **66 independent probes passed**, including all 27 hash-verified corpus cases and the earlier hostile-header, canonical-path, transport/expanded/path-limit, validate-before-extract, destination-protection, and controlled cleanup probes. All **five frozen maintained artifact tests passed**. No unfinished `test_environment.py` code was imported or run.

The original single-header, 228-byte-path exploit is now rejected with `Environment archive filesystem entry limit exceeded` after exactly **512 bytes and one read**, with no staging destination created. Five added checks established:

- Two sibling files followed by an explicit parent-directory header succeed at exactly three permitted filesystem nodes; the shared/explicit parent is not counted twice.
- A nested file creating three filesystem nodes succeeds at a cap of three.
- That nested file is rejected at a cap of two, before staging exists.
- Two distinct two-node branches are rejected at a cap of three, including when the second branch follows a valid first file.
- An instrumented over-node-limit header declaring a body is rejected after one header read; no body read or extraction is attempted.

Inspection confirms the union of normalized explicit paths and implicit ancestors is charged before any body read or extraction. The existing separate explicit-header check remains in place. The node limit includes descendant objects; the fresh staging root and temporary spool are fixed additional objects.

## Boundaries

This assessment assumes a trusted controller stream implementation, controller-selected limits/destination, and controller-owned staging parent without concurrent untrusted writers. It establishes bounded uncompressed archive validation and fresh extraction under those assumptions. Receipt integrity, preparer/publication integration, deadlines/cancellation/owner death, actual host quotas, failed-cleanup reconciliation, and target runtime qualification remain outside this slice and require their own evidence. No containers, network fetches, model/GPU calls, rig operations, or maintained-file edits were performed.

## Retrievable evidence

The published evidence consists of this report, `security-artifact-recheck/probe.py`, and `security-artifact-recheck/results.json`. The JSON preserves the original assessment's candidate identity, source hash, runtime and observations; rerunning the probe does not overwrite it.

The probe reconstructs the exact reviewed commit `0c9c7c8fffdc6d16f316a3650cd28a78ab265095` with `git show` into the ignored repository-local directory `.gflo/security-artifact/0c9c7c8fffdc6d16f316a3650cd28a78ab265095/`. It imports the helper and reads the corpus from that reconstruction, then runs the frozen maintained artifact tests there. Only trusted files from the fixed commit are reconstructed. Git history containing that commit and Python 3.10 or later are required; no network fetch is performed.

The earlier private `gflo/`, `tests/`, and `evaluations/` copies beside the probe remain local inspection evidence. They are not publication inputs or reproduction dependencies and should not be tracked. New per-probe observations go to `.gflo/security-artifact/0c9c7c8fffdc6d16f316a3650cd28a78ab265095/rerun-results.json`.

Reproduce from a clean checkout with the candidate in its Git history:

```sh
python3 .scratch/.sflo/04-autonomy-environments/security-artifact-recheck/probe.py
```

The script also runs the frozen maintained artifact tests and returns failure if any probe or unit test fails.
