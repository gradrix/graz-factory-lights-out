# Environment coding fixture v2 recheck — PASS

Private manifest `858384ee7ca74724efe1ee4247c69cc039d88e8b53b344ef42c5f6c6d6e9989b`; public identity remains `c479e671e6a4bdc06f8b58cfcf8a5f520c50f2859387ec7894f97039f43ab374`. Bound hashes verified. Original private v1 and its bound files remain unchanged; all reference witnesses and starter source files match v1.

| Independent real-container recheck | Result |
|---|---|
| Node reference at `/different-source`, unrelated `/tmp` working directory | PASS |
| Python API reference, offline wheel build/install and loopback HTTP | PASS |
| Exact original early-filter Node mutant | REJECTED |
| Exact original changed approved-lock mutant | REJECTED |

Both confirmed v1 findings are closed. Filtered-invalid records now pass through API, CLI and input-immutability assertions. Lock hashing enforces the stated unchanged-lock requirement. Added dependency/backend assertions preserve the already declared approved versions; strict/CommonJS checks correspond to the explicit compile contract. No new business rule, dependency version, objective, reference, runtime or budget was introduced. The checks preserve the starter's explicit CommonJS packaging convention.

Scope: targeted repaired-oracle recheck; v1 stdlib/path/type evidence remains applicable because that oracle and reference are unchanged. Semantic test/documentation quality, complete unsupported-input coverage, model results, environment publication and Stage 3 acceptance remain separate requirements.

Reproduce: `python3 .gflo/environment-coding-qa-v2/probe.py` (exit 0). Full captured command outcomes/stdout/stderr: `.gflo/environment-coding-qa-v2/results.json`; compact output: `probe.log`. Containers used pinned Python3.12.13 / Node22.23.3 images, explicit runc, network none, read-only source/dependency mounts and capped scratch/resources. No target models, GPU, rig/runtime changes or maintained test edits.
