# Independent semantic QA: coding C-v2

**Verdict: qualification fails.** All twelve terminal task outputs and the ambiguity case were inspected independently. Raw controller result is **9/12 accepted**, below the 10/12 gate; ambiguity correctly returns `needs_input`. All nine accepted snapshots pass the published oracle and generated tests under verified Python 3.12.13. One accepted output has a confirmed documentation error (task10); task09 has a narrow instruction deviation. No accepted critical functional defect was found. Failed tasks remain failed; rechecks do not rewrite frozen outcomes or establish Stage 2 graduation.

## Frozen scope and runtime qualification

- Reported batch controller/runtime commit: `c17821c`; frozen C-v2 manifest: `560c3e5645ed2d9ea91404e05aa4ddb2f4c9b1eb01f8629a98ec6e6ae738938b`.
- Original rig verification used image `sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578`, identified as **Python 3.11.15**, contrary to task contracts requiring 3.12+. Original reference-validation receipt `.gflo/coding-qualification-c-v2/private/validation.json` explicitly records the same version/image; type-mutation validation uses that image too. Those original checks cannot be described as Python 3.12 validation.
- Independent rechecks used local image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, directly verified as **Python 3.12.13**. These provide separate candidate evidence, not retroactive correction of the frozen target environment.
- Every captured original acceptance file matches its published `evaluations/coding-c` counterpart by SHA256. Per-file and combined workspace identities are in [coding-c-evidence/identities.json](coding-c-evidence/identities.json).

| Task | Run | Raw status / attempts | Passing generated tests on 3.12 | Independent semantic result |
|---|---|---|---|---|
| 01-seat-allocation | `cc965a7d716d` | accepted / 1 | 5 | PASS: exact quotas, tie order, zero-total handling; exhaustive small-input probe passes. |
| 02-grid-distance | `2914f77232b0` | accepted / 1 | 4 | PASS: blocked/same/unreachable endpoints and shortest orthogonal distance. |
| 03-bit-fields | `43b7647311b0` | exhausted / 3 | — | FAIL: default discovery finds zero tests; explicit -s tests passes 3. |
| 04-polynomial | `7e948830a4a9` | accepted / 1 | 3 | PASS: exact polynomial and derivative, empty/constant/max boundaries. |
| 05-paragraph-wrap | `df444f4008b1` | accepted / 1 | 5 | PASS: literal-newline paragraphs, Unicode whitespace, greedy long-word handling. |
| 06-luhn-check | `fbb865b3744f` | exhausted / 3 | — | FAIL: two wrong generated assertions; README check digit also wrong. |
| 07-monthly-calendar | `8e64a711a6ca` | accepted / 1 | 8 | PASS: independent monthly clamp, leap/year boundary and before-start omission. |
| 08-resource-matching | `353c1b95e636` | interrupted / 3 | — | FAIL: missing API action/tests/docs; augmenting-path loop does not terminate. |
| 09-duration-language | `dbc86949d658` | accepted / 1 | 3 | Functional PASS; unnecessary guaranteed-type/length validation deviates from instruction. |
| 10-approval-ballots | `7a6dd457c3fb` | accepted / 2 | 4 | Functional PASS; README tie-order example wrong. |
| 11-run-length-codec | `9785dca7d431` | accepted / 1 | 5 | PASS: maximal runs, positive counts, decoded-length boundary and atomic failure. |
| 12-form-query | `4f1f0bb04c57` | accepted / 2 | 23 | PASS: strict byte/UTF-8 parsing; additional escape/rejection probes pass. |
| ambiguous | `da2fc7d2e36b` | needs_input / 1 | — | PASS: asks owner to select unresolved appointment policy; source remains baseline. |

## Confirmed findings

**Task03: test discovery failure, correctly rejected.** The final candidate implements the requested pack/unpack behavior and passes its three tests with `discover -s tests`; default `python -m unittest discover` finds zero because the tests directory lacks `__init__.py`. Default discovery is explicitly required. All three original attempts retain candidate `9bf105498bc2780ad476b0cf669e88b2fd15c7e5af14602263e6f39bcb529520`; this is failed autonomous repair, not an oracle mismatch. Original acceptance independently fails the minimum-test requirement. See [03-bit-fields-extra.json](coding-c-evidence/03-bit-fields-extra.json).

**Task06: wrong tests and documentation, correctly rejected.** Correct append output for `7992 781` is `79927810`; generated tests demand `79927812` and incorrectly call that latter number valid. A direct checksum control totals 40 for the correct number; implementation agrees. Both failing assertions persist across three identical candidate hashes `cc6a178e8d61d2a51c8754fab3c6269649bb977301515aecb07cca25b3a3ff89`. README also claims `4992 781` appends to `49927816`; actual/correct output is `49927817`. The algorithm itself has no identified contract failure. See [06-luhn-check-examples.json](coding-c-evidence/06-luhn-check-examples.json) and generated-test receipts.

**Task08: incomplete delivery and nonterminating algorithm, interrupted.** API never routes `match`; no tests/new README usage were delivered. Domain helper `maximum_matching` also loops on just `[['a','b'],['a']]`, whose maximum is 2. Path reversal overwrites `job_to_resource[previous]` before reading the old matched resource, then repeats the same edge. A fresh two-second bounded probe times out at the loop; independent brute-force control returns 2 and the candidate's disjoint case passes. This is a real algorithm failure in a never-accepted output. The exhaustive public-API probe stops at missing `match`; it does not establish algorithm coverage. See [08-resource-matching-algorithm.json](coding-c-evidence/08-resource-matching-algorithm.json).

**Task10: accepted documentation defect, noncritical.** README's executable example uses candidates `[a,b,c]` with a receiving two votes and b/c one each, but displays `[a,c,b]`. Required and implemented tie order is `[a,b,c]`. Exact-example probe confirms correct implementation and wrong documentation. This violates accurate new-usage delivery without a functional false positive. See [10-approval-ballots-readme.json](coding-c-evidence/10-approval-ballots-readme.json).

**Task09: minor instruction deviation.** The objective guarantees types/bounds and says not to invent validation. Code additionally rejects non-string and >100-character inputs and tests a 101-character rejection. No valid-input failure is demonstrated. Keep this separate from the three material completion failures and task10's misleading example.

## Coverage and boundaries

Read original objectives and inspected domain, API, CLI, README and generated tests for every terminal candidate. Checks cover original identity/unknown-action behavior, successful/error CLI behavior, mutation protection, requested algorithm semantics, meaningful normal/boundary/error regressions and documented usage. All nine accepted outputs pass default discovery with at least three meaningful methods. Tasks02/12 retain unnecessary action aliases; their generated tests mostly exercise aliases, while the original oracle verifies the required names. Task11's “runs stay separate” prose is imprecise for an expanded-list result; examples and implementation are correct. These observations do not establish additional functional defects.

Verifier-chosen probes include exhaustive small seat allocations, malformed percent/UTF-8 sequences and literal decoded separators, the Luhn arithmetic control, the task10 documented example, and task08's discriminating hang/control. Source examples and action contracts guided checks; no new input policy or post-return deep-copy requirement was invented. Ambiguous appointment case asks explicitly about membership versus arrival order and equal-time ties before implementation; captured source is unchanged from baseline. See [ambiguous-question.json](coding-c-evidence/ambiguous-question.json).

Original target verification/review receipts (including failed attempts), compact source patches, content hashes and fresh check outputs are under [coding-c-evidence](coding-c-evidence/). Private captures are `.gflo/semantic-c/<run>/`. Collectors copied only selected task/source/acceptance/review/verification data; no credentials, raw traces or configurations were exported. Commands are recorded in receipts; orchestration scripts are `qa-coding-c-collect.py` and `qa-coding-c-extra.py`, with the complete supplemental source at `coding-c-evidence/supplemental-probe.py`.

Generated code ran only inside offline Docker with read-only mounts/root filesystem, no GPU, non-root user, dropped capabilities, one CPU, 256 MiB memory, 64-PID limit and bounded subprocess/probe times. No maintained code, frozen candidate or fixture was edited. No account limit interrupted this audit. Subsequent known-case repair experiments are outside this report and cannot count as fresh qualification evidence.
