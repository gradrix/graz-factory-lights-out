# Resumed independent semantic QA

**Verdict: full-contract acceptance remains incomplete for frozen cohort B.** Fresh independent inspection completes tasks 05–12 and rechecks repaired task02. Seven of tasks 05–12 have no identified contract gap; task09 remains a stopped, correctly rejected delivery. The separate task02 repair now satisfies the previously missed test/documentation obligations. It does not rewrite frozen task02's original outcome.

| Task | Frozen run | Functional oracle | Generated suite | Semantic result |
|---|---|---|---|---|
| 05 | `3a580376311a` | PASS | 22/22 | Escapes, strict keys, first equals, rejection and input preservation checked. |
| 06 | `df03c8b4fc28` | PASS | 17/17 | Normalization, whole-segment ancestry, totals and sorting checked. |
| 07 | `fb1fb7b64726` | PASS | 11/11 | Create-only, version comparison, nested independence and preserved read checked. |
| 08 | `751bc03d4c4b` | PASS | 16/16 | Requested order, duplicate validation and falsey successes checked. |
| 09 | `fa94c69430ad` | FAIL | 10/10 | FAIL: revision remains 1/2; generated tests encode this wrong requirement. Frozen acceptance rejects it. |
| 10 | `ef27abbc21eb` | PASS | 14/14 | Weighted eviction, replacement, failed oversized put and get promotion checked. |
| 11 | `c38088d51d73` | PASS | 20/20 | Exact nested numeric equality, boolean distinction and huge sparse sequence supplemental probes pass. |
| 12 | `aefc008cb097` | PASS | 14/14 | UTF-8 code-point boundaries, repeated/end/invalid offsets checked. |
| 02-repair | `repair` | PASS | 35/35 | PASS: docs added; retry regression expects 21; accepted inputs retain intended behavior. |
| 03 | `3c48308dd1cc` | PASS | 27/27 | Ordinary checks pass; valid extreme exponent produces MemoryError before cap. |

## Findings and limits

- **Task03, noncritical functional robustness defect:** `domain.py:34` computes an unbounded power before applying the cap. `attempt=10**30`, `max_attempts=10**30+1`, `base=1`, `cap=10`, transient outcome is contract-valid and should return delay/at 10. A bounded arithmetic control passes; candidate raises `MemoryError` under 128 MiB. Thus this is a real full-contract miss despite normal-path tests passing. No evidence supports elevating it to critical production impact; inputs are extreme and this utility has no stated exposed deployment. Sandbox exit 1 is the observed reproduction, not an unexpected verification failure.
- **Task09, failed completion:** migration output retains revision 1/2 and README explicitly teaches that behavior. Original contract explicitly requires revision 3. Fresh original acceptance fails at line 37; all 10 generated tests passing demonstrates their inadequate contract coverage. This was never an accepted candidate, so it is not an accepted false positive.
- **Task11, fixture limitation:** private reference compares data with Python equality (`True == 1`), while final candidate distinguishes booleans and numbers recursively and equates 1/1.0 without lossy conversion. Fresh supplemental probes pass, including nested booleans and large distinct numeric values. Reference mismatch is supported by source plus preserved `event-equality-probe.json`; reference execution was not repeated here. “JSON equality” is underspecified enough that future fixtures should define it expressly. Do not penalize the candidate for correcting the reference's type conflation or silently change the frozen score. Unused canonical-form computation and inaccurate helper docstring are maintenance residue, with no demonstrated output defect.
- APIs, preserved actions, CLI success/error behavior, docs and no input mutation were inspected against original contracts. Tasks 08/10/11 return some shared nested values: their contracts prohibit mutation during calls, not subsequent output aliasing; this is not a defect. Task07/09 explicitly require independence and were assessed accordingly. Out-of-contract type validation additions are unnecessary but do not establish a valid-input failure.

## Evidence and frozen identity

Run `python3 .scratch/.sflo/03-autonomy-review/qa-semantic-resumed-run.py` from the repository. This host script only orchestrates Docker and hashes files; generated code runs only inside offline, read-only containers with no GPU, dropped capabilities, non-root user, 256 MiB memory, one CPU, 64 PIDs and bounded timeouts. Existing Python image: `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`. Both original `/acceptance/check.py` and `unittest discover -s tests -v` were executed. Complete commands, stdout/stderr, supplemental probes and per-file candidate SHA256 identities: `qa-semantic-resumed-results.json`; source fixture hashes: `qa-semantic-resumed-fixture-hashes.json`. No maintained files or frozen outputs changed. No account limit encountered.

Workspace identities below are SHA256 of sorted JSON filename-to-content-SHA256 mappings, excluding bytecode. Runtime identities from earlier target receipts remain separate; this recheck used the locally available pinned image above.

- 05 `3518f889a01d0f2253bb954fb96d50aa1eccf64a6d84fdd4d1200e73cfdc27b7`
- 06 `4ee6a11446e9b0b16f846cac5295312a73b086dba8e0e575f800b023ea57f241`
- 07 `965b9e8563538d9c96f511eb8f5e7dd219b2ac07c9538630a95dbc768692356e`
- 08 `e149fe559ca1dbe572bca8957c265235e58524bdd605fb862980e9923445074a`
- 09 `c2a5878b6ebba6a70d1225d43adee57bfb50876b0ec4bca90420c2286f3d8752`
- 10 `fdab3bf841c6da9751b7810029c4b8e44106cc182893e8cdc6d5bb54a45da20c`
- 11 `67ddd3fdab3775f52c7a878ee6385214c2881c73ed8d6b0bec6e0529bb7a3f8e`
- 12 `37acad7fe700eb49656bf2a53e3f759e1a61c774ddf996fe633b223aefbd7fba`
- 02-repair `ef27c01e6a2854604af3a8d629ae48279b774439ef9d3510588aae1b6fed6f05`
- 03 `3732ded9860ded49d42ae5b500a3e0e79b08af5878b2bceb71be4b550c0252a4`

Tasks 01/04 and original frozen task02 rely on the prior independent report; they were not re-executed here. This completes the missing semantic review scope, not broader factory or stage graduation.
