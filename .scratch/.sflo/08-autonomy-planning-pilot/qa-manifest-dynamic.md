# Independent manifest dynamic verdict

**Both suspected A6 defects confirmed with passing conforming controls.** Historical Factory acceptance stays accepted for both arms; independent full requirement quality is not a clean pass. No candidate changes or model calls.

Four fresh actual rig containers ran after all timed arms completed: pinned Python3.12.13 image `fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, explicit runc/no-pull, network none, read-only root/source/probe mounts, nonroot, capabilities dropped, no-new-privileges, 512MiB memory/swap, one CPU,64PIDs,64MiB tmpfs. Candidate mounted `/candidate`, no `/workspace`. All owned containers removed and absence confirmed. Original content/mode maps match before/after.

| Run | Measured result |
|---|---|
| Arm1 original,0.582s | Probe exit1. README root unittest discovers11tests; CLI test errors with FileNotFoundError `/workspace`. Other checks pass. |
| Arm1 control,0.721s | Exit0, all checks pass; only generated test helper path/interpreter changed, assertions untouched. |
| Arm2 original,0.802s | Probe exit1. Twelve generated tests pass after relocation, but literal README compare request returns exit2/errorJSON instead of documented exit0/result. Digest lengths62/60/62/60. |
| Arm2 control,0.794s | Exit0, all checks pass; only four README digest literals corrected to64characters, expected result unchanged. |

Both originals pass valid upper bounds, invalid boundary/nonmutation, asymmetric ambiguous rename/permutation and absolute CLI invocation from unrelated cwd. Arm1's actual application CLI and README compare example pass. Arm2's test portability passes. Failures are therefore bounded to the documented defects rather than general algorithm failure.

A6 explicitly requires working unittest commands and a concrete request/response example. Arm1 uses the exact advertised project-root command from its actual root; no arbitrary-cwd test rule was added. Arm2 substitutes only executable location to isolate its literal payload/result mismatch. No surprising probe artifacts or correction reruns occurred.

Reproduction: `qa-manifest-run.py` stages conforming copies through `qa-manifest-controls.py` and executes unchanged `qa-manifest-probes.py`. Complete compact receipts/output/container identities/source maps are under `qa-manifest-execution/`; originals remain untouched on rig under `/home/gradrix/gflo-planning-d186b93/trial-1`, separate proof staging `/home/gradrix/gflo-planning-postqa-manifest-1`. Control source copies are diagnostic only and cannot replace or rescore actual arm artifacts. Prior static reports supply exact source lines and candidate fingerprints.
