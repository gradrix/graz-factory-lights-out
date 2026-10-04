# Pre-exposure findings

No real inference is admitted. Draft findings require a frozen successor and recheck.

- **P09-PROMPT — resolved at37b7f1d, draft executable_review_prototype.py.** Initial SYSTEM concatenates the maintained text-only review prompt, retaining “Do not execute tools or modify files,” before granting run permission. Replace the contradictory tool prohibition explicitly while retaining read-only authority. No claim that prior static-review quality qualifies the new prompt.
- **P09-MODES — resolved at37b7f1d, draft verify_manifest.** File modes are checked, but frozen directory/source-root modes are not yet enforced. Public fixture modes include0664/0775; Git does not preserve the complete map. Validate every manifest mode; a new checkout must fail closed on mismatch. Any trusted restoration belongs before admission, never during review.
- **P09-START — resolved at37b7f1d, independent security draft review.** A creation/inspect receipt can exist even if Docker fails to start the command. That must not count as the required executed probe. Require positive command-start evidence in addition to creation identity, bounded output and confirmed cleanup. New control must discriminate failed startup from actual in-container execution; prior helper creation evidence is not sufficient alone.

- **P09-UID — resolved at37b7f1d.** Controlled UID0 now refuses before command debit/guardian dispatch. This was a draft admission gap, not a live rig incident.

Final31combined controls and independent actualrig syntheticreadback close these pre-exposure findings; see security.md and qa-harness.md. MechanismSHAede30d388c75b1c69c683dbd4c61cae408afc73cd5d35f84c1748d0ab281ecaa.
