# Contradictory evidence after acceptance

Passing a finite gate set does not prove a program is correct. An Acceptance finding
records later contradictory evidence against an exact accepted atom contract and
candidate. The original acceptance, gate receipts and Attempt events stay intact.

The trusted control plane calls `WorkLedger.record_finding(AcceptanceFinding(...))`
with a previously published evidence artifact. The record binds `atom_id`,
`contract_digest`, `candidate_digest`, `evidence_digest` and a bounded nonempty reason.
Identical delivery returns the original event. Workers cannot submit findings through
the candidate/read-file protocol, and a model's unsupported claim is not independent
evidence of a defect.

`status` exposes `acceptance_findings` and `acceptance_challenged`. Historical status
remains `accepted`; it must not be interpreted as current permission to reuse a result.
`history` shows the later finding alongside the original accepted candidate and gates.
Controller acceptance replay and prepared integration recheck the ledger and reject
challenged results. An already accepted integration also rechecks its children on reuse.

On the first finding the ledger advances its minimum reader version to 3 atomically
with the event. Older version-2 controllers refuse new opens. Stop any already-running older
controller before applying the upgrade; the version marker cannot change code
already executing against an open connection. New readers continue
to support version-2 ledgers without findings. The finding artifact participates in
audit; losing its bytes does not clear the block.

Repair requires a new Work atom and independently passing evidence. This slice has
no dismiss/clear command. It does not retract already exported files, discover external
copies or propagate findings across separate ledgers. An integration's historical
status is not a recursively updated product-health dashboard; its entry point performs
the dependency checks before reuse.
