# Format3 document references: prefreeze security plan

2026-10-04. Skill: security-check. **Outcome: no blocking boundary omission found in the chosen contract/ADR. Coverage: brief read-only review; no candidate qualification or new tests.** Builder retains sole maintained mutation ownership.

Reviewed [contract.md](contract.md), SHA-256 **`4e1077bd1e2ef48f4a76375e79eb5c42dd9ce6ca0719ca6418474fe5e5ffd106`**, [ADR007](../../../docs/decisions/architecture/007-bounded-document-references.md), the preceding [reference option](../../autonomy/document-reference-boundary.md), and the original format2 security evidence. No model, rig, service or maintained-source operation was performed.

## Fixed authority and concrete implementation cautions

The model selects integer span IDs from one frozen evidence record. Only the controller supplies evidence IDs and exact whole-span excerpt bytes. The model cannot introduce a second source, override excerpt text, reinterpret IDs as paths, truncate a quote or obtain tools. These constraints make copying deterministic; they do not prove the selected text entails the claim.

The contract explicitly fixes count/encoded-byte bounds, long-span failures, conservative capacity-unresolved abstention, format1/2 preservation, one repair and the prior publication/lifetime limits. I sent the builder these precision points:

1. **Define metadata accounting exactly.** Measure the canonical encoding of the complete receipt after removing only its canonical `answer` field; include both attempt summaries, config/profile, request/response hashes, errors and version metadata. Enforce≤12KiB before publication. Also check≤48KiB canonical answer and≤64KiB complete receipt independently. Apply these new limits only toformat3; older legal receipts must not acquire a retroactive12KiB rule.
2. **Preserve legacy errors as well as prompts.** Format2 resolution recomputes recorded validation/error metadata and request hashes. Its base/repair prompt bytes, profile, answer validator behavior and error strings must remain unchanged. Dispatch old readers explicitly; a default helper changed forformat3 must not leak intoformat2 replay or diagnostics. Format1 has its own existing interpretation. Unknown formats refuse rather than fall back.
3. **Validate before expansion.** Require exact returned fields, strict integer IDs (`bool` is invalid), positive in-range values,≤8claims,≤4references per claim and≤16total occurrences. Repeated references consume budget every time. Check selected span encoded/UTF8 size and claim encoded text before constructing canonical citations; source selection and excerpt construction then use only validated IDs. Final encoded bounds remain authoritative.
4. **Capacity is not semantic absence.** Any overlimit selected span is repairable structural invalidity, with the same single-repair allowance. With any ineligible source span, an insufficient-evidence response is also structural capacity-unresolved failure. Exhaustion saves a failed diagnostic, never a successful abstention. Supported answers may cite eligible spans without deleting long source context.

## Focused frozen-candidate assessment

| Boundary | Planned independent control |
| --- | --- |
| Selection/materialization | Known span positive and exact punctuation restoration; bool/zero/negative/out-of-range/noninteger IDs; extra excerpt/evidence fields; different source ID; canonical output inconsistent with raw IDs. |
| Expansion limits | Claim/ref count cap and+1; repeat the same reference across claims; escaped Unicode/control encoded-size cap and+1; selected overlong span; bounded canonical/metadata/final receipt checks. No expansion before invalid input refusal. |
| Long-source behavior | Eligible selection succeeds with unrelated long context. Long-only selected support and repair-to-abstention fail as capacity; all-eligible truly unsupported answer remains a valid insufficient-evidence result. |
| Version integrity | Actual preserved format1 andformat2 success/failure records resolve/replay with byte-identical original metadata and failure meaning. Tampered version/request/profile/response/canonical fields refuse even when rehashed. Format3 reconstruction is deterministic. |
| Existing lifecycle | Carry evidence only after exact source comparison. Recheck changed seams for repair eligibility, cancellation before second call/final commit, immutable failed diagnostics, prior-good preservation and no postcommit I/O. Broader child/guardian tests only if affected or a concrete remaining risk requires them. |

No broad prototype or new model trial follows from this plan. The frozen ten diagnostic repeats and three fresh questions, independent source alignment, complete semantic/citation review and target-rig cross-version offline replay remain separate explicit acceptance gates. A passing structural/security result cannot rescore the failed exact-quote trial or establish general document-answer reliability.
