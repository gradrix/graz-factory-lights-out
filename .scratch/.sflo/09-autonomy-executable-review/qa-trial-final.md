# Independent final unit09 trial audit

**FAIL: one valid, correct classification out of four; three incomplete reviews.** The frozen four-correct-classification gate is not met. Human-readable conclusions are not substituted for runtime outcomes. No maintained reviewer promotion or fresh-case reliability claim follows.

| Case / expected | Actual outcome | Requests / commands | Work seconds |
|---|---|---:|---:|
| 01 original arm1 / repair | INCOMPLETE: fenced JSON plus prose, JSONDecodeError | 5 / 6 | 74.444 |
| 02 corrected arm2 / pass | INCOMPLETE: output limit, malformed tool completion | 2 / 2 | 92.358 |
| 03 corrected arm1 / pass | INCOMPLETE: prose before JSON, JSONDecodeError | 6 / 8 | 89.756 |
| 04 original arm2 / repair | Completed valid repair; independently correct blocking finding | 7 / 9 | 107.430 |

Total20 completion requests,25 attested commands,363.988 work seconds. All four saved parent receipts confirm cleanup and same-identity idle. Independently rechecked every candidate file hash and file/directory permission mode against saved input facts: all unchanged. Complete evidence root `.gflo/executable-review-trial-1/case-01..04`; no candidate execution, rig/model calls or edits during this audit.

## Case01

The useful human-readable A6 finding is grounded: actual command01 gets11 tests/one FileNotFoundError for the hardcoded `/workspace`; command06 copies to `/tmp`, changes test cwd and gets11 passing tests. The real application CLI works. Finding line176 identifies the subprocess call, although “critical” overstates this bounded test-workflow defect. Final response05 contains fenced JSON and appended prose, so strict refusal is correct. Its broad “all other requirements verified” claim exceeds the finite executed probes; several shell/Python probes failed independently and are preserved. Detailed early analysis remains `qa-cases-early.md`.

## Case02

Actual first command passes all12 tests on the corrected control; second confirms tree/runtime. Response02 reaches4096 completion tokens with finish_reason length while constructing a large tool request. Neither proposed command from that response executes. There is no final verdict and no observed candidate defect. Classify incomplete, not false reject or pass.

## Case03

The corrected control receives a human-readable pass with no invented blocking finding, supported by11 passing generated tests, actual README example output, CLI/error and selected boundary/rename/nonmutation probes. Command08 runs discovery from `/tmp` against `/candidate` and again passes11 tests. However response06 starts with explanatory prose before its JSON object. JSONDecodeError leaves it incomplete; do not extract/rescore the trailing object.

Final narrative slightly overstates its probes: “README example reproduces byte-for-byte” was not a recorded byte comparison, and the listed broad rule checks combine generated tests and selected probes rather than exhaustively proving all inputs. Its “invalid UTF-8” experiment uses shell printf text whose byte interpretation was not independently attested, so only the observed invalid-input error is established. These qualifications do not reveal a blocking defect in the corrected candidate.

## Case04

Valid final response07 reports the required **major A6 README defect** at README.md line51. Command03 runs the literal malformed example and gets errorJSON/exit2; command05 independently measures62/60-character hashes; command06 locates the exact four literals at51–54; command08 substitutes valid64-character hashes and reproduces documented result/exit0. Grounding and counterexample/control distinction are sound, candidate unchanged. This is independently accepted useful defect detection.

The extra minor finding at line43 (`echo 2` prints a literal instead of showing prior status) is accurate and nonblocking. Some surrounding line references in the final narrative are imprecise: its claim of success status at line65 does not match the saved README layout (65 is a later malformed-input command). The primary line51 citation and actual command evidence fully support the major defect; this citation imprecision does not reverse classification. The minor finding does not invent a new blocking requirement.

## Interpretation

Both known defects were noticed in human-readable reasoning, but only one produced an admissible grounded verdict. One conforming control had a plausible pass embedded after prose; the other exhausted output before classification. This is a failed protocol discriminator, not four successful reviews with cosmetic formatting issues. Preserve original costs, errors and tool outputs. Any protocol successor must be separately frozen and labelled, without silently salvaging or retrying this batch. Successful execution and strict refusal demonstrate bounded wiring, not reliable local review completion.
