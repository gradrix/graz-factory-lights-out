# Strengthen semantic gates after a discovered false acceptance

Type: task
Status: claimed
Blocked by: 18, 24

## Evidence

Frozen campaign run `heldout-v1-r1-dedupe-last` was accepted by its original gates.
Prospective supplemental probes found that repeated different IDs shift indices in
its list-removal algorithm, causing it to remove the wrong record. Expected final
IDs b,c,a became a,c,a. Raw retained evidence:
`.gflo/evidence/heldout-v1-qualified/semantic-review-r1/`.

This is a discovered false acceptance. It blocks progression even if the original
numerical completion targets are met. Preserve the original acceptance, candidate,
gates and campaign score; add the contradictory evidence without rewriting history.

## Scope

After frozen scoring finishes, build a separate regression gate with multiple
interleaved duplicate IDs and verify it rejects the retained bad candidate and accepts
the known-good reference. Qualify broader input partitions for future prepared tasks.
Any repaired candidate needs a new Work atom and new passing evidence. Do not silently
replace the previously accepted candidate or call this seen fixture held-out again.

Before automatic downstream scheduling or product promotion, add durable contradictory
evidence handling that prevents reuse of a known-bad accepted candidate while retaining
its historical acceptance. The current campaign's explicit progression block is not
that future runtime capability.

## Progress

Full review confirmed two false acceptances: deduplication and version-sort tie stability.
New regression gates reject both retained bad candidates and accept references. Added
AcceptanceFinding, immutable post-acceptance events, guarded replay/integration reuse,
evidence audit and reader-version protection. Both actual campaign findings are recorded;
a pre-finding ledger/artifact snapshot remains available. Enabled suite: 253 tests plus
25 subtests, no skips.

Deduplication repaired on Attempt 2. Version sorting exhausted ten repair attempts and
a separately counted clarified three-attempt replacement contract. No additional retries
or manual candidate replacement were performed. Stronger gates prevented false acceptance
throughout these follow-ups. Task remains claimed for broader semantic qualification;
next diagnose this persistent failure and explicit task-contract composition. See
[results](../heldout-results.md). Original campaign progression remains failed.

## Comments

2026-09-09: Resumed bounded diagnosis. Replayed the final clarified candidate in
a broker container: ["1.0.0", "1"] incorrectly reverses; each singleton passes.
Testing three rotated repetitions of baseline, explicit reasoning, and targeted
contract guidance, one attempt/turn each, with identical source/gates/token budgets.
The guidance arm is human-authored repair localization, not autonomous decomposition.
Evidence: `.gflo/evidence/version-sort-comparison-v1/`. Original scores unchanged.

2026-09-09 outcome: explicit reasoning with a 4K output reserve repaired 3/3;
baseline remained 0/3 at both budgets. All seven accepted treatment repairs passed
69 additional inputs. Profile remains opt-in; broader qualification is still open.
See [diagnosis and reproduction](../version-sort-diagnosis.md).
