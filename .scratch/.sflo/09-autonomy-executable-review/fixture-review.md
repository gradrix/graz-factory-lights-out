# Unit09 independent fixture freeze

**Four known review inputs frozen; identity checks pass.** Contract `1fe3c4763dd4e1ee6d3b280619dcbce4ac1814d7253dbbba5c1d8d6f47f959d1` and run/unit read before authoring. No candidate code execution, model calls or rig writes.

Manifest `05de766048d96216865b8e5d0c817166ac1635391a6ed496b9ce6c3b0b6bdb37` is at prototype `evaluations/executable-review/manifest.json`; identical compact copy `fixture-manifest.json` here. Public cases contain only exact source trees and the complete original A1–A6 public task objective, with neutral IDs. No historical review, protected oracle, diagnostic hints or expected classifications are public. Controller must mount each source subtree alone and use its objective; never mount the evaluation root/private directory or main coordination evidence.

| Order | Private provenance | Expected discriminator outcome |
|---|---|---|
| case-01 | Arm1 original | Grounded blocking A6 test-path finding |
| case-02 | Arm2 exact passing control | Pass without invented blocking rule |
| case-03 | Arm1 exact passing control | Pass without invented blocking rule |
| case-04 | Arm2 original | Grounded blocking A6 README-example finding |

Every original file's SHA256 and permission mode matches saved08 `qa-manifest-execution/results.json`; every control file hash matches its saved paired-control receipt and all modes match the original's unchanged modes. Controls were copied read-only from rig staging, not regenerated. Arm1 control changes only generated test helper interpreter/path; arm2 control changes only four README digest literals. Public source copies preserve those bytes/modes. Top-level manifest binds every public file hash and public entry mode, including directories.

The original full objective was read from frozen08 task.json, copied identically to each objective file with a final newline. Its source task hash, objective hash, paired receipt hashes and full source/control file/mode maps are in `fixture-binding.json` and prototype private/binding.json. Expected outcomes live only in prototype private/expectations.json and coordination evidence. Builder confirmed this separation and manifest schema.

No redundant execution was needed: exact original/control pairs already ran in four actual pinned offline containers during08, with original failures and corrected passes preserved. This reuse proves fixture identity and known behavior; it does not imply fresh-case or model-review reliability. New mechanism admission remains root's responsibility before any inference.
