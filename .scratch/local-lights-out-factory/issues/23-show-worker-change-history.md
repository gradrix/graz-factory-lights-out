# Show worker change history

Type: task
Status: resolved
Blocked by: 18, 21

## Scope

User-requested traceability increment: readable candidate diffs linked to retained
Attempts, failure reasons, model provenance and gate outcomes. Preserve unsuccessful
work; do not imply a candidate is an integrated Git revision.

## Answer

Implemented `gflo history ATOM_ID` with readable text and `--format json`. Each
candidate is compared with the original prepared source; failed/no-candidate Attempts
remain visible. Reads verify referenced artifact hashes and do not mutate history or
invoke models. No worker rationale is invented. Tests cover failed/successful diffs,
newline handling, no-candidate failures, terminal controls, corruption and repeated
read-only history. The command was exercised against the live in-flight-recovery
ledger and correctly displayed the interrupted Attempt followed by the accepted test
candidate. See [usage](../../../docs/controller.md#worker-change-history).

This focused traceability addition does not resolve task 22's remaining integrity
matrix, or implement product Git integration/reverts.
