# RTX 5090 local model study

This study compares practical coding, tool use, speed and context capacity on MONSTER-GAMING-PC. It uses synthetic prompts and a fixed public coding dataset. No repository code, credentials or personal documents are sent to the models.

## Files

- `RESULTS.md`: final recommendations, measured comparisons and restoration evidence.
- `model-research.md`: primary-source research, candidate selection, pinned downloads and runtime requirements.
- `inventory.json`: sanitized hardware and original serving configuration.
- `results/*.jsonl`: raw requests, responses, timings and grades. Preserve failures as well as successes.
- `summary.json`: computed summary of those results.
- `profiles/` and `logs/`: exact temporary launch commands and runtime evidence.
- `EXPERIMENT-NOTES.md`: protocol details and limitations.
- `restoration-check.json`: original container, model revision and API readback after testing.
- `grading-environment.json` and `random-grading-audit.json`: exact grader image and seeded replay evidence.
- `humaneval-subset32.json` and `humaneval-LICENSE.txt`: dataset provenance, fixed task selection and license.

## Reproduce on the rig

The experiment directory on the rig is `/home/gradrix/benchmark-5090`. The original server remains in the `local-vllm` container. Candidate containers use `benchmark-5090-server` and host loopback port 18000. Model files and runtime binaries stay in the experiment directory.

To repeat a full comparison after the model files are present:

```bash
cd /home/gradrix/benchmark-5090
bash run-comparison.sh bonsai 32768 f16
bash run-comparison.sh qwen 32768 f16
bash run-comparison.sh flash 8192 f16
bash run-comparison.sh flash 131072 q4_0 512
bash run-comparison.sh vllm 65536 fp8
STUDY_KV_CACHE_BYTES=4831838208 bash run-comparison.sh vllm 131072 fp8
```

Each invocation temporarily stops the original service. It runs the tests in sequence and restores the original container on exit. It creates timestamped result files. Do not run several GPU comparisons at once.

The optional fourth argument selects Flash's batch and microbatch size; the fifth selects experimental YaRN scaling. `STUDY_KV_CACHE_BYTES` selects an explicit vLLM KV budget. Context beyond 262144 requires an explicit scale and separate quality qualification; the runner increases the request timeout for large windows. See the final results for which configurations were actually validated. The profiles trade away the original four sequence slots for one sequence, so these are single-user comparisons.

To restore the original server directly:

```bash
python3 /home/gradrix/benchmark-5090/profiles.py restore
```

`profiles.py` reuses the original image by digest and retains the original container. Its private restore metadata and environment file remain on the rig with mode 0600; they are intentionally excluded from this repository.

## Benchmark protocol

`benchmark.py` measures three fixed 256-token text generations, twelve custom correctness checks and two small agent repair workflows. Compare the final two speed runs after warmup. Tool-call buffering makes token-rate estimates on tool responses unsuitable for throughput comparisons.

`humaneval_benchmark.py` uses 32 tasks selected with seed 5090 before seeing candidate responses. All canonical solutions passed in the grading environment. Chat prompts request complete Python source; this is an adaptation of HumanEval, not an official full benchmark score. Non-thinking runs allow 1,024 output tokens; medium-thinking runs allow 4,096 including reasoning. Temperature is zero. Tests and canonical solutions are not included in prompts.

Generated code is graded in disposable Python 3.11.15 containers pinned to the recorded image digest (`grading-environment.json`) with no network or host mounts, a read-only filesystem, dropped capabilities, and process, memory, CPU and execution-time limits. The only selected randomized published test is addition; `audit_random_grading.py` replays it with a fixed seed against stored answers.

`context_stress.py` creates unique random distractors, places three independent facts at different depths, and asks for those facts plus an absent-key result. It counts tokens through the active server before sending the request. Exact JSON correctness is the primary result. This establishes retrieval for these probes, not general reasoning quality across an entire large window. The context limit includes input, formatting, reasoning and output.

Long-context example after starting the corresponding candidate:

```bash
python3 context_stress.py --port 18000 --llama \
  --label bonsai-native-context --sizes 32000,65536,131072,262144 --seeds 1,2
```

Run `python3 summarize.py` in the local study directory after copying completed result files from the rig. Reports distinguish measured results, published claims and untested possibilities.
