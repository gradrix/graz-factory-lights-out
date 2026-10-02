# Environment coding fixture preparation

Prepared 2026-10-02 while Stage 2 cohort D was running. This is independent Stage 3 preparation only. No maintained environment runtime, model/GPU invocation or rig mutation was performed. Existing artifact acceptance corpus and prior coding cohorts were not changed.

## Frozen inputs

| Artifact | SHA-256 |
| --- | --- |
| Public `evaluations/environment-coding/manifest.json` | `c479e671e6a4bdc06f8b58cfcf8a5f520c50f2859387ec7894f97039f43ab374` |
| Private `.gflo/environment-coding-qualification/manifest.json` | `9b944ac5efc83e89d54e22843fd2425ae6ca7fe227bb117870fa54ff3fcb9c8c` |

Public inputs contain three objectives and starter projects, complete approved Python dependency lock, unchanged Node lock, runtime facts and isolation instructions. Private inputs bind three clean starter commits, protected oracles, reference witnesses, approved lock hashes, dependency-tree inventories and actual validation evidence. Public manifest binds 22 files; private manifest binds 31 files. Freeze occurred before any target-model exposure.

Tasks: Python stdlib expense reconciliation across domain/API/CLI; installable FastAPI reservation preview; strict CommonJS TypeScript deployment report. Each adds useful behavior while preserving existing public behavior. Three attempts, 24 turns per attempt, 900 seconds per task remain fixed. Each requires meaningful tests and new usage/error documentation. No reference implementation belongs in coder or reviewer context.

## Executed verification

Three starter failures were confirmed specifically at the missing feature, after retained behavior passed. Each reference passed the immutable external oracle twice in fresh containers, once with source at `/input/project` and once at `/var/task-source`, while the container started from unrelated `/tmp`. Thus six reference passes and three expected baseline failures were observed.

- Python stdlib: actual Python 3.12.13; direct API, CLI from an unrelated working directory, strict JSON types, rejection/immutability checks, discovered unittest tests and README usage.
- Python API: actual Python 3.12.13; copied source to capped scratch, built with setuptools 78.1.0 offline using `--no-build-isolation --no-deps --no-index`, installed the resulting wheel without dependency resolution, and exercised real loopback HTTP health/sum/new-route/422/404 behavior. Repeated preview verified no persisted reservation state. Generated unittest tests ran against the installed package.
- Node: actual Node v22.23.3, npm 10.9.9, TypeScript 5.8.3 and @types/node 22.15.3; strict CommonJS compilation, API/CLI exact comparisons and rejection/immutability checks, node:test execution and README usage. Approved lock also pins undici-types 6.21.0.

The private validation JSON retains output, effective HostConfig, mounts and environment for all nine containers. All used explicit `runc`, `network=none`, no GPU requests, non-root UID/GID, read-only root and read-only selected binds, all capabilities dropped, no-new-privileges, memory=swap 1 GiB, one CPU, 128 PIDs, `/work` 480 MiB, `/tmp` 16 MiB and shared memory 16 MiB. In-container `/dev` checks reported no NVIDIA/DRI devices. Containers were removed after each attempt. No Docker sockets, source-host homes, model configuration or credentials were mounted.

Python image: `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`. Node image: `sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0`. Existing local dependency trees from `.gflo/environment-locks` were mounted read-only at controller-selected profile paths. Dependency inventory records actual installed Python metadata and byte/mode hashes without changing those trees.

## Limits and next use

This establishes that the bounded tasks, oracles and private witnesses are feasible under the approved prepared profiles. It does not establish cold-cache preparation, immutable receipt publication, archive security, public-only fetch, owner-death/cancellation behavior, full device isolation beyond these observed settings, real 5090 model performance or Stage 3 completion. Base images and dependency snapshots were reused. No future environment receipt was invented.

Independent fixture QA should inspect these frozen inputs before exposure. After the Stage 2 gate and maintained preparer/security acceptance, bind each task to the real returned environment receipt, retain trusted runtime facts in reviewer context, and run the target model with the original budgets. A passing reference is not a model result. Any later correction creates a new version preserving this frozen evidence.

## Pre-exposure revision 2

Independent QA found two concrete v1 false passes: an early Node filter skipped validation of invalid events below minAttempts, and changing the npm lock did not affect tests because prepared dependencies were mounted independently. Original public/private directories remain unchanged; complete additional snapshots, including this report before revision, are preserved under `.gflo/environment-coding-qualification-v1`.

Public inputs remain unchanged at manifest `c479e671e6a4bdc06f8b58cfcf8a5f520c50f2859387ec7894f97039f43ab374`. Corrected protected fixtures are `.gflo/environment-coding-qualification-v2`, manifest `858384ee7ca74724efe1ee4247c69cc039d88e8b53b344ef42c5f6c6d6e9989b` (33 bound files). Objectives, source commits, budgets, runtime and reference implementations are unchanged.

The Node oracle now rejects invalid rows even when all rows would be filtered, through both API and CLI while checking unchanged input. It also binds the approved npm lock bytes, dependency declarations and strict CommonJS configuration. The Python API oracle verifies approved runtime/build dependency fields while allowing unrelated metadata changes.

Focused v2 verification on the same approved offline runc profiles confirmed 11 outcomes: two missing-feature starters, two conforming reference passes, and seven rejected mutants (Node early-filter, CLI-only filter, lock change, dependency change, disabled strict checking; Python runtime dependency change and build dependency change). Revalidation SHA-256: `201e1128d58873687c29d67bff3495fd367d90c4c9eb7cd51f6a0678d0e1ffc2`. The unchanged stdlib oracle retains its original evidence. No model calls, rig changes or maintained product edits occurred. Independent QA recheck is pending; this remains fixture preparation rather than Stage 3 acceptance.
