# Independent retained API candidate checks

**Verdict: both retained API candidates remain failed. No rescore or candidate changes.** Actual offline checks ran only after the four timed arms ended. No model or service calls occurred.

## Identity and execution

Decomposed arm3: child `300151e5e413`. Direct arm4: child `a8aac6d4726e`. Exact per-file retained-source hashes, commands, creation receipts, outputs and absence readbacks are under `qa-api-results/`. `qa-api-evidence-manifest.json` binds the executable probes and every evidence file. Rig staging: `/home/gradrix/gflo-planning-postqa-api-1`.

The resolver verified canonical API snapshot `e591c2d6f97b02fc2a99ecef01848a4e74d743e499aeec3b4d4d7d6c6c400acb`. Actual creation receipts confirm image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, explicit runc, network none, uid1000, read-only root/project/dependencies, no devices, cap-drop ALL, 1GiB memory/swap,2CPU,128pids,16MiB shm and192MiB temporary space. Script asserts CPython3.12.13, builds/installs a copied package offline and exercises real loopback HTTP. Original project hashes remained unchanged; every started container has a creation receipt and confirmed absence.

## Paired controls and candidate outcomes

| Project | Supplemental checks | Result |
| --- | --- | --- |
| Frozen conforming reference | 67/67 pass | All new assertions have conforming control. |
| Scalar-depth mutant | 6 targeted failures | Scalar depth7 and shape-priority effects detected; depth6 passes. |
| Missing Body mutant | 13 failures | Valid HTTP requests fail; direct domain controls pass. |
| Lazy validation mutant | 6 failures | Later invalid request must precede earlier conflict. |
| Decomposed retained candidate | 51/67 pass | 16 failures across depth, HTTP binding and generated tests. |
| Direct retained candidate | 61/67 pass | Six exact-operation-shape failures. |

Each mutant's named expected failures **and** unaffected positive controls were checked against the paired-control manifest; nonzero exit alone was not treated as detection. Supplemental candidate checks took2.906s/3.006s. These check counts are diagnostic coverage, not qualification scores or reliability estimates.

## Confirmed findings

1. **Decomposed HTTP route binds payload as a query argument.** `src/config_preview/routes.py:20` lacks Body binding. Valid JSON previews produce422 with `loc:["query","payload"]`; required success200 and conflict409 requests never reach the domain. The missing-Body mutant reproduces this while the conforming reference passes. The generated installed-package suite also fails its successful-preview and conflict HTTP tests.
2. **Decomposed depth validation checks objects but misses scalar depth.** `validation.py:57` checks the current object depth and increments only for object children (`:77`); scalar children are counted but their depth is not tested. A scalar at depth7 is accepted. Inserting an independently valid `{"x":0}` value at a depth6 path also yields scalar depth7 and is incorrectly accepted instead of indexed `limit`. An earlier missing remove then wins over a later value invalid in isolation, violating complete-input validation priority. The scalar-depth mutant and reference establish the paired distinction.
3. **Direct operation fields are not conditioned on the operation.** `validation.py:99` accepts either `{op,path}` or `{op,path,value}` for every op. `domain.py:21` uses `.get("value")`, so missing set.value silently writes null (HTTP200); missing test.value conflicts (HTTP409); remove with extra value is accepted (HTTP200). All must reject with ValueError/HTTP422. The same six assertions pass the frozen conforming reference. Contrary to the preliminary static hypothesis, this retained candidate does **not** raise KeyError: measured results follow `.get`.
4. **Both README server commands fail in the approved environment.** Both prescribe bare `uvicorn config_preview.app:app ...` after target installation; neither makes the console script available on PATH. Focused actual checks report FileNotFoundError for `uvicorn`, while `python -m uvicorn config_preview.app:app ...` starts the same installed candidate and returns correct `/health`. This is a scoped approved-profile documentation defect, not a claim about a different environment with globally installed uvicorn. Exact focused outputs are in `qa-api-results/results-docs/`.

The direct candidate's five generated tests pass from arbitrary cwd after wheel installation and include ordinary behavior, edge cases, nonmutation and HTTP. Their passing does not cover the exact operation-field defect above. Its README has a concrete matching request/response example and a workable installed-package unittest command; the server-command issue remains. Static review found no need for broader speculation beyond these reproduced failures.

## Probe lineage, failures and limits

Original probe `d030e97e...` remains unchanged. Supplemental v2 `1fe0c86a...` adds missing test.value and forbidden remove.value to the existing missing set.value check, directly justified by B1; no objective relaxation. The control generator was versioned correspondingly. Neither generated candidate was edited.

The first rig wrapper invocation failed **before container creation** because the guardian subprocess could not import gflo; its full error and absence/source readbacks remain in `qa-api-results/results/`. Versioned wrapper-v2 sets the guardian module path; subsequent controls/candidates and focused documentation checks all have creation/cleanup evidence. No model retry, score adjustment or hidden candidate repair occurred.

These narrow probes complement frozen acceptance and semantic review. They do not establish all B1–B5 behavior. Preserved baseline endpoints were covered by existing frozen checks; this supplemental run did not duplicate every baseline assertion. Error detail is bounded in probe JSON, while container output and execution receipts are retained. The evidence supports keeping planning advisory and evaluating a narrowly bounded reviewer that can actually run installed tests, documented commands and discriminating counterexamples before making acceptance claims; it does not authorize such a maintained feature here.
