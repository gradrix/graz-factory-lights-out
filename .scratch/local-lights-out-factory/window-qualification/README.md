# Bounded worker window qualification (2026-09-10)

The opt-in windows-v1 profile used the pinned local model/deployment, with 12,288 total
contract tokens, 4,096 output tokens, two attempts and three turns per attempt.
Codex selected tasks, implemented the generic protocol and wrote the independent gates.
No candidate text was supplied manually. Both successful runs needed a read, an edit,
and a repair from development feedback about integer subclasses.

- large-v2: accepted the 10,002-line / 207,814-byte file edit, exercised 501 integer
  values through the function and read-only caller, rejected invalid types including
  integer subclasses, and preserved unrelated source. Largest prompt: 3,276 tokens
  versus the previous whole-file probe's 128,684. One attempt, three responses.
- repository-v4: accepted a change to the actual 568-line gflo/repository.py snapshot,
  enforcing built-in-int arguments before reads. Preserved text outside the method
  and all support files. Largest prompt: 4,814 tokens. One attempt, three responses.
  This qualification candidate has not been applied to the factory repository.
- Both accepted runs replayed without new ledger events or inference.

Failures are retained, not overwritten: large-v1 was accepted with an incomplete gate;
independent review found its integer-subclass bug and recorded an acceptance finding.
repository-v1 omitted storage.py and retained a contract review stop. repository-v2
compared AST dumps across Python runtime versions and quarantined a repeated draft.
repository-v3 was an erroneous fixture correction with malformed newline escaping and
retained a review stop. repository-v4 preserves raw source text instead of AST dumps.
The fixture mistakes demonstrate that independent checks themselves need review.

results.json contains ledger snapshots (including findings), response text, token use,
and evidence identities for every run. The Python files retain each exact launch recipe;
run from the repository root with its installed virtualenv and provisioned local model.
Before reproducing, replace the run name/output directory with a fresh unique name;
never reset a historical ledger. For exact real-file input use baseline commit 17b3ad0
in an isolated checkout and the implementation from this change. Raw artifact stores
remain under ignored .gflo/evidence and must be transferred for byte-exact replay.

This qualifies bounded worker edits, not large-product planning or arbitrary repository
execution: the planner still selects whole files and SourceBundle still caps execution
inputs at 256 KiB. The generic protocol contains no fixture-specific file names or fixes.
