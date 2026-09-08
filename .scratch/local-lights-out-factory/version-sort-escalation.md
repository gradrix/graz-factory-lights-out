# Retained semantic-repair exception

The local model repeatedly sorts unpadded numeric component lists. This violates the
prepared requirement that missing components are zero and numerical ties preserve
input order. The strengthened gate rejects it. The original false acceptance is
challenged and cannot be reused through the controller or prepared integration.

Evidence and budgets:

- Original scored task: `heldout-v1-r2-version-sort`, one of two discovered false
  acceptances in the frozen campaign. Historical score remains failed qualification.
- `semantic-repairs-v1`: new regression gate; version-sort repair exhausted ten Attempts.
- `version-sort-clarified-v1`: separately counted replacement contract with a public
  tie example and additional private gate; exhausted all three Attempts.
- No manual product edit, cloud fallback or cleared finding.

Readable diagnostics fixed a different seeded failure, but did not solve this semantic
case. Next diagnostic candidates are reasoning-enabled local inference and improved
repair context/task decomposition, under prospectively recorded bounded profiles.
These are hypotheses; no benefit has been measured yet. Do not silently restart the
same exhausted task or describe this fixture as unseen.
