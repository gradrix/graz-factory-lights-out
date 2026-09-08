# Twelve-task development pilot — 2026-09-08

The eager vLLM baseline accepted all twelve tasks, eleven on the first Attempt. No human repaired a candidate. Each category contained three tasks: implementation, defect repair, consumer migration, and requirements-derived test data. Test generation is deliberately bounded to JSON cases: an immutable driver checks the known-good implementation and three seeded defects per task. All nine defects were detected.

The workload and reference gates were frozen before scoring. All twelve references passed and all twelve initial implementations failed at least one gate in clean broker containers. The fixture SHA256 is `4f0fb9eadb5e3b4213419cbb76fab484f678673dadc864fc7e6942e247d18826`.

Baseline totals: 17 Model turns, 12,148 prompt tokens and 2,135 completion tokens; maximum actual turn size 1,085 tokens. Median generation HTTP latency was 9.71 seconds, maximum 42.44 seconds. Task execution summed to 295.46 seconds, excluding reference preflight. Sampled peak total GPU memory was 31,302 MiB, including other GPU users. No ledger-referenced artifact was missing or corrupt.

The paging migration's first Attempt requested a file already present in its expanded Worker view. The controller rejected the duplicate read and a fresh Attempt succeeded. This is a context/tool-protocol failure, retained in the ledger, not a failed correctness gate or a manually repaired result. A prospective policy improvement should explicitly tell the worker to use files already in `source_files`; it must be evaluated separately from this frozen baseline.

Raw baseline evidence: `.gflo/evidence/twelve-task-pilot-v1/`, including frozen manifest, preflight, ledger/artifacts, environment, sampled resources, results, summary and checksums. Run using `PYTHONPATH=. .venv/bin/python scripts/run_pilot.py --output NEW_DIRECTORY`; summarize completed runs with `scripts/summarize_pilot.py DIRECTORY`.

This is a small, synthetic development set with three Attempts allowed per task. It is not held out, a campaign success-rate estimate, a general test-generation benchmark, or evidence of unattended product completion. Ordinary checks overlapped some preflight/early scoring; timings are diagnostic rather than isolated hardware benchmarks. vLLM versus SGLang coding quality remains unmeasured.

## Eager versus graphs on the same coding workload

| Measurement | Eager baseline | Graphs |
|---|---:|---:|
| Accepted | 12/12 | 12/12 |
| First Attempt accepted | 11/12 | 11/12 |
| Model turns | 17 | 17 |
| Completion tokens | 2,135 | 2,061 |
| Median generation HTTP | 9.71 s | 1.94 s |
| Maximum generation HTTP | 42.44 s | 7.49 s |
| Sum of task durations | 295.46 s | 111.38 s |
| Sampled total GPU memory peak | 31,302 MiB | 30,828 MiB |

The manifests confirm identical fixtures, RunPlans apart from deployment/profile identity, and worker source/prompt. The same pinned image/checkpoint, 16K context, BF16 KV, single sequence and resource limits were used. Removing `--enforce-eager` enables both compilation and CUDA graphs, so this is a serving-mode comparison, not isolation of individual compiler/kernel effects. Outputs and token lengths differed despite deterministic sampling settings. Median generation was about 5.0 times faster; aggregate useful-task time about 2.65 times faster. GPU memory readings include desktop usage and are not a controlled memory superiority claim.

Graph startup completed within the five-minute bound. Logs show full decode graph capture and approximately 0.17 GiB graph pool memory. The first captured coding replay took 22.45 seconds HTTP: 20.71 seconds prefill and 1.29 seconds decode for 75 output tokens. Retain this cold-request cost; warm pilot timing does not include it. CPU quota counters showed negligible throttling, which rules against quota exhaustion as the dominant explanation but does not prove the underlying kernel-launch bottleneck.

Graph pilot raw evidence: `.gflo/evidence/twelve-task-pilot-graphs-v1/`. Startup, logs and fixed-request replays: `.gflo/evidence/graph-comparison/`. The graph pilot also had one duplicate-read failure, in the price migration. Both failures are preserved. The prospective `bounded-python-v2` prompt explicitly forbids re-reading visible files; a separate paging replay passed in one Attempt. This is a bounded development improvement, not proof duplicate reads are eliminated.

Use `infra/serving/vllm-5090-graphs.example.json` for further local development. It preserves the eager profile as a fallback. The running container is `gflo-vllm-graphs`; `gflo-vllm` is stopped. Never start both together. Graph-specific restart/crash recovery and broader performance qualification remain open under task 20; the earlier eager recovery evidence does not transfer automatically.

The warm fixed-request replay took 1.44 seconds HTTP: 0.103 seconds prefill and 1.333 seconds decode for 75 tokens (about 56 tokens/second). Both paging and price migrations passed in one Attempt under the prospective prompt policy. Repeated launcher `up` accepted the existing graph container without drift. Final checks: 163 tests and 25 subtests passed, eight optional Docker tests skipped; Ruff, mypy and whitespace checks passed. See [verification manifest](pilot-verification-results.json).
