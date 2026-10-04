# Independent early executable-review audit

**Actual outcomes: case-01 INCOMPLETE; case-02 INCOMPLETE.** Neither is a successful classification under the frozen contract. Review is read-only against completed local immutable copies; no candidate execution, rig/model calls, changes or feedback to remaining cases.

For both copies, independently checked each candidate file hash and file/directory permission mode against saved input facts; all match. Evidence root `.gflo/executable-review-trial-1/{case-01,case-02}`; paths below relative to each case.

## Case-01: correct useful defect, invalid final format

Expected: grounded blocking repair for original arm1 A6 test-path defect. Actual: five requests, six executed commands, then JSONDecodeError. `requests/05/response.json` has finish_reason stop and800 completion tokens, but content starts with a Markdown JSON fence and appends prose. Strict complete-content JSON parsing correctly refuses it. No cleanup/parser salvage or manual rescore is applied.

The human-readable finding is substantively grounded: `commands/01/stdout.body` shows11 tests with one FileNotFoundError for `/workspace`, tied to `tests/test_manifest_tool.py:176–178`; request05 cites line176, a real subprocess-call line. `commands/06` copies source to writable `/tmp`, changes only test cwd and obtains11 passing tests. Candidate source remains unchanged. This is meaningful defect detection with a paired control, despite protocol failure. Calling this bounded test defect “critical” overstates severity; it is a blocking A6 workflow issue, with working application logic.

Other probe evidence is mixed and preserved. Command02 fails shell syntax (`<<<` under sh). Command03 genuinely demonstrates ping exit0 and malformed JSON exit2 via absolute main.py. Command04's manually assembled compare request rejects; command05 then constructs a valid request in Python and demonstrates the rename result plus selected size/count/ambiguity checks. That Python probe ends with an uncaught ValueError for extra ping fields, so its process exit1 is a probe-handling issue rather than a newly discovered implementation bug.

The final prose says “All other requirements were verified by direct execution.” Existing generated tests plus the limited probes cover many listed examples, but this statement is broader than the evidence: no exhaustive direct verification of all requirements or every arbitrary cwd is established. The narrow reported test-path defect and its repair experiment are supported. No extra blocking implementation defect is asserted.

## Case-02: passing control left unclassified by output exhaustion

Expected: pass for corrected arm2 control. Actual: two requests, two executed commands; request02 reaches4096 completion tokens and finish_reason length. It contains tool-call material including a large literal CLI test-input list. The driver rejects the entire incomplete tool completion before dispatch: only command01/02 records exist. Proposed commands in request02 are not executed evidence.

`commands/01/stdout.body` shows all12 generated tests pass. Command02 lists the source and confirms Python3.12.13. No valid final verdict or grounded blocking finding exists. This is an incomplete correct-control review, not a false reject or a pass. The lack of final classification is caused by the observed truncated completion/protocol stop; no runtime failure or candidate defect is demonstrated by this case.

## Interpretation boundary

The first case provides evidence that read-only executable review can discover the known test-path defect. It does not satisfy the frozen valid-verdict gate. The second demonstrates that the same bounded workflow can fail to finish on a conforming control. Neither result permits the planned four-correct-classification conclusion. Remaining cases are outside this early report; originals, raw outputs and consumed budgets remain unchanged.
