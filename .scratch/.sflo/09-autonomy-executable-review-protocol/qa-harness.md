# Independent protocol-successor QA

**PASS for local controlled scope; actual rig synthetic phase wiring pending root execution.** Mechanism SHA256 `c69e90f8359603b9bf6636fa02a6b0887a4ba2af38f9f481243f9c8e831530a8`; contract `f4381c22e730f53bd5bab1af93e4794aa4c83fe0ce31c2a1a2767fc9a51a076f`. No rig or model calls by this verifier.

Thirteen independent tests pass (`qa-harness/independent-controls-final.txt`, invocation `python3 ops/test_executable_review_qa.py`). Seven carried/adapted checks cover ledger/command limits, reset refusal, tool authority, malformed whole-batch rejection, grounded/no-attestation verdicts, public manifest/mode binding and hostile tool text remaining data. Six successor checks exercise real ReviewClient with controlled transport:

- Exploratory prose, including malformed-looking JSON fencing, is not parsed as a verdict; a separately charged final request has json_object response format and no tools/tool_choice.
- Truncated mixed valid/malformed tool batch executes zero commands; one recovery succeeds without adding partial assistant calls to history.
- Second truncation terminates; malformed final terminates without retry; no attested command refuses completion.
- Seven exploratory requests preserve the eighth for finalization, with seven real controlled command results.
- Clock control at181seconds closes exploration while preserving119seconds of overall budget; final request remains one-use across ledger reconstruction, forbids commands, and overall expiry refuses further work.

Earlier partial-write observations are retained in `qa-harness/draft-observation.txt`; final explicit-ready source passed. They are not reported as frozen defects. No fixture or mechanism code changed by QA. Separate security/lifecycle evidence remains separately attributed; unchanged helper execution is not falsely claimed as newly measured here.

## Synthetic driver ready for root

`ops/executable_review_vertical_qa.py` SHA256 `2721efe4b87e031dab0e69835ac74ff61195a95bc96a1ae3c1f616c65b6c430b`. Production300-second ledger; mandatory in-memory transport and controller socket denial; actual case_work/approved Docker command verifies readonly source, no/workspace, nonroot and runtime. Three responses deliberately exercise actual tool output, exploratory prose, and a separately charged JSON final with no tools. Driver asserts three calls, one attested command, unchanged fixture and confirmed cleanup. Root should use explicit stage cwd/PYTHONPATH as before. It has not been staged or executed by QA.

Test source SHA256 `2cb0d8134c5823df3af646b23196d56e195ffe35a95f13074a0657b6515630eb`. Frozen public fixture remains `05de766048d96216865b8e5d0c817166ac1635391a6ed496b9ce6c3b0b6bdb37`. Local pass is not live-review admission or a claim that prior three incomplete cases are repaired; historical outcomes remain immutable.

Final narrow recheck: all13 existing independent controls pass after non-list tool_calls is refused before length recovery. Prior bcde-source results remain in independent-controls.txt. No test/driver changes, scope expansion or rig calls.

## Independent readback of root-run actual rig evidence

**PASS.** Root executed the synthetic driver against frozen prototype `847f90e9d4fe515e6c6eada9eb200008b6441fd2`, mechanism `c69e90f8…`, driver `2721efe4…`. Independently read complete `qa-rig-vertical` receipts; no rerun or rig/model calls by QA.

Recomputed request/response file hashes agree with all three durable ledger entries: explore, explore, final. First two requests offer run tools; final has json_object response format and neither tools nor tool_choice. Actual command output is present as tool feedback before exploratory prose and the explicit final transition. Final response is strict valid JSON and one command is attested; final_reserved=true, no recovery used.

Creation evidence records pinned image `fb1118f1…`, runc, network none, readonly root/mounts, uid1000:1000. Actual command ran0.401s and reports Python3.12.13, cwd/candidate, absent/workspace and rejected candidate write. Independently recomputed copied candidate file hashes and directory/file modes match saved input facts. Cleanup receipt confirms owned container `gflo-review-2cb21a0612644873b702f966` absent. Synthetic accepted verdict and tree hash match final evidence. Full records remain under `qa-rig-vertical/`; staging/launch/download evidence is separately retained by root.

This closes actual phase-wiring verification. It is synthetic transport evidence, not actual model correctness or authorization to reinterpret the failed predecessor trial. Admission and any real repeat remain coordinator decisions under the successor contract.
