# Arm 2 independent static review

**Core implementation appears conforming; A6's documented successful example is invalid.** Static review only; no candidate execution, Docker, inference or edits. Historical Factory result remains accepted.

Arm `2-manifest-reconcile-decomposed`, final child `037a513a8192`, first child `b90b66156d7f`. Independently reconstructed fingerprint matches `f3170468840e203ac45fe8e2f563a736b774ad25794bbca53c41197825f9742a`. Frozen evidence root `.gflo/planning-trial-1/2-manifest-reconcile-decomposed`. Recorded 494.785 seconds, 36 calls: 31 implementation, three code review, planner and plan review once each.

## A6 finding: concrete README example contradicts validation

Final workspace `README.md:51–54` contains four digest literals of lengths **62, 60, 62, 60**, independently counted without executing candidate code. The advertised request is followed by successful rename/modification output and exit 0. `manifest_tool/validation.py` requires `len(sha)==64`; `cli.py` maps the resulting ValueError to error JSON and exit 2. Thus copying this example cannot yield its claimed response, even at the documented `/workspace` mount.

A6 explicitly requires a concrete JSON request/response example and working run commands. This is a direct documentation defect, not an additional portability policy. Preserve the example unchanged for a pinned-container confirmation after all timed arms finish. Both model reviews and final acceptance missed it. README's `echo 2` following the first invalid-action example also prints a literal rather than inspecting exit status; later examples correctly use `echo $?`.

## Requirements and handoff

| Scope | Static assessment |
|---|---|
| A1 | Correct exact entry fields, 100-entry/120-character/size bounds, ASCII paths, strict bool/float rejection, unique paths, 64-lowercase digest, copied outputs/nonmutation. |
| A2 | Shared-path signatures compared before rename; modified sizes and stable sorted lists correct. |
| A3 | Original unmatched sets grouped by complete signature; only one-to-one groups renamed, ambiguity retained, input order irrelevant. |
| A4 | Totals sum all entries, delta signed; exact API fields and ping preserved. Redundant totals validation is harmless. |
| A5 | Absolute main.py imports package correctly; JSON errors map to fixed error/exit2. No application data-file access. Broad exception list is unnecessary but no observed wrong result. |
| A6 | Twelve meaningful tests cover classifications, rename sorting, asymmetric ambiguity, shared-path exclusion, permutation invariance, invalid inputs/nonmutation, API and subprocess CLI. Invalid README example above prevents a clean documentation verdict. |
| Plan | Exactly two ordered tasks; task1 IDs A1/A2, task2 A3–A6, dependency task1. Both generated child objectives preserve the complete original objective before scoped additions. Fixed milestone/full commands retained. |
| Checkpoint | Saved mode restoration before/after fingerprints both `c92f041bfcb070b1b0e0fc1b70af108ce5ea66e98048da817526912c66849872`; checkpoint and base/tree receipts retained. No static evidence of omitted requirement or altered acceptance authority. |

Compared with arm1, tests compute `ROOT=Path(__file__).resolve().parents[1]`, use absolute MAIN and `sys.executable`, and run subprocesses from `/tmp`; arm1's hardcoded test cwd defect is absent. README commands still use `/workspace` explicitly, so their literal paths describe that environment; this alone is not scored as an additional defect. No consequential filler/overengineering observed; several tests overlap but exercise real behavior.

## Deferred confirmation

Run the exact README compare payload in the pinned offline container; expect current candidate's exit2/error rather than documented success. Also run generated tests with project mounted `/candidate` and the corresponding original A6 project-root command, plus the same narrow upper-bound/asymmetric-signature probes used for arm1. Do not repair candidate or feed findings back to the local model. Static semantic findings and historical Factory acceptance remain separate.
