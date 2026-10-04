# Successor case01 independent early audit

**Runtime: completed valid repair. Required defect classification: correct. Strict evidence-truth gate: not clean.** No reclassification of runtime outcome and no candidate execution, rig/model calls or feedback to active cases.

Evidence `.gflo/executable-review-protocol-trial-1/case-01`: six charged requests, seven commands,172.890seconds; saved cleanup/idle confirmed. Independently rehashed candidate files and checked file/directory modes against input facts: all match.

The blocking test-path finding is supported. Command02 shows11 tests with one FileNotFoundError from hardcoded `/workspace`, grounded at test file line176. Command07 independently repeats the four CLI assertions using `/candidate` as cwd and observes correct results. This establishes the narrow A6 test-helper defect and a useful prospective correction. “Critical” severity overstates a bounded regression-test workflow defect, but it is legitimately blocking under A6.

**Unsupported executed-test claim:** final verdict says the corrected “suite then reports11/11 passing.” No command runs the corrected full suite. Only the original failing suite and four separately reproduced CLI assertions were executed. Inferring that those results would make the full suite pass is reasonable, but presenting it as an observed suite report violates the frozen requirement against unexecuted-test claims. Preserve the actual valid repair while recording this semantic evidence-quality failure.

**Unsupported extra minor finding:** the verdict blames bare `python` and recommends `python3` because arbitrary hosts may map it differently. The approved environment has both executables (command01), and command07 itself successfully uses bare `python` for all four CLI checks. The public objective explicitly gives a `python -m unittest` command. Thus this is a speculative portability suggestion outside the demonstrated defect, not an established requirement violation. It is minor/nonblocking, so it does not create a false blocking classification. README line41 also does not precisely locate every command quoted in this finding.

The correct blocking diagnosis survives these qualifications; the stronger all-four-cases-with-truthful-evidence gate is not established by structural completion alone. Remaining cases will be audited independently when their immutable evidence arrives. No output salvage, retry or source repair is proposed within the active trial.

## Case02: corrected arm2 control

**Runtime completed pass; independent expected classification PASS.** Seven requests, nine attested commands, approximately185.17seconds. Candidate files and directory/file modes independently match saved input facts. No execution or rig/model calls during audit.

Command01 runs12 generated tests successfully. Command05 reproduces the corrected README compare result/exit0. Other actual commands exercise malformed CLI requests, value/path/count limits, ambiguity, nonmutation, totals and100 unique rename pairs. Command06 fails on an invalid probe input; later command07 supplies a corrected bounded scenario. These preserved exploratory failures do not demonstrate a candidate defect.

Exploratory response06 is fenced JSON plus a detailed prose summary; it is correctly treated only as context. Separately charged final response07 is strict `pass` JSON with no findings or unsupported executed-test claims. Its expected corrected-control classification is supported; no invented blocking requirements.

The exploratory prose's “byte-for-byte” README claim describes matching displayed output without an explicit recorded byte-comparison assertion. Treat it as observed agreement of the displayed example, not evidence of an automated exact-byte check. Unlike case01, the final verdict does not claim a nonexistent corrected-suite execution. Twelve passing tests are actually recorded. Case02 does not resolve case01's independently identified truthfulness defect or establish the overall four-case gate.

## Case03: corrected arm1 control

**Runtime completed pass; independent expected classification PASS.** Five requests, five attested commands,127.516seconds. Independently verified all saved candidate file hashes and directory/file modes against input facts. No candidate execution during audit.

Command01 records11 passing generated tests; command04 runs ping/invalid inputs and the README compare example with expected results. Commands03/05 exercise asymmetric ambiguity, exact API keys, failed-validation nonmutation,100 rename pairs, input-order invariance, totals and deterministic sorting. Command02 confirms Python3.12.13/tree. These are real finite probes, not exhaustive correctness proof.

Exploratory response04 and separately charged final response05 both contain plain pass JSON, but only final response05 is the verdict. It has no findings, unsupported repair claims or invented blocking policy. Observed tests support the expected corrected-control pass. Source remains unchanged. This case adds no new truthfulness finding and does not erase case01's unsupported corrected-suite claim.
