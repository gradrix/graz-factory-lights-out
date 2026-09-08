# RTX 5090 target verification — 2026-09-08

Status: initial Stage 0 target qualified for the fixed Python broker and conservative vLLM profile; see the latest checkpoint below. Earlier observations are historical.

## Observations

The current checkout runs under Debian 13 / WSL2, kernel 6.6.87.2-microsoft-standard-WSL2. Docker 28.5.1 exposes four CPUs and 47,346,573,312 bytes of memory (about 44.1 GiB); do not use the planned physical 64 GB as the container allocation budget. The workspace filesystem has about 818 GiB free.

Host and disposable GPU container both report NVIDIA GeForce RTX 5090, driver 610.88, and 32,607 MiB total VRAM. Approximately 2,994 MiB was already occupied on the host before model loading. No running Docker containers were present at the initial inventory.

The sandbox probe confirmed UID 65534, no effective capabilities, no-new-privileges, seccomp filtering, read-only root filesystem, only the loopback network interface, and no Docker socket. Its cgroup v2 files reported 128 MiB memory, zero swap, 32 PIDs and one CPU. These are observed kernel settings, not destructive OOM/fork-exhaustion tests or proof of a complete worker security boundary. Docker is not reporting rootless mode.

## Reproduce

Run from the repository root with these already installed image digests:

```sh
python3 scripts/check_target.py \
  --sandbox-image python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca \
  --gpu-image vllm/vllm-openai@sha256:ac259a0111c6cf462a72e449962b84f7a624b5cbec24bd7d9ec3b67d40ffd1bf
```

The command resolves each image to its local immutable ID, starts bounded disposable probes, and removes only its own uniquely named containers, including after a timeout. It refuses non-local Docker endpoints and never pulls images or starts inference. Exit zero means these probes passed; `stage_0_complete` remains false. Raw JSON from this checkout is retained privately in `.gflo/evidence/target-check-2026-09-08.json`; it is ignored by Git.

## Remaining target work

The default loopback endpoint failed `python3 scripts/serve.py doctor` with an unreachable/timeout result. No model was loaded by these checks. Existing vLLM image availability does not select it as the permanent backend.

Rechecked the [vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B) and located the [SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B). The vLLM recipe still documents eager execution for its single-5090 NVFP4 configuration. This is recipe evidence, not a local inference result.

Next: verify a compatible checkpoint/tokenizer revision and serving image, configure bounded serving resources, start one backend, and retain startup/readiness/synthetic structured-output evidence. Then verify restart/cache/drift behavior and compare SGLang/vLLM at 8K and 16K, concurrency one. Coding comparison follows the durable loop. Execution-broker qualification also needs bounded enforcement tests and actual worker/validator separation.

## Software validation

29 unit tests passed with ResourceWarning treated as an error, including probe cleanup on timeout and refusal to pass missing/unlimited controls. The real container probes passed separately. No model weights or images were downloaded by this work.

## Broker qualification checkpoint — 2026-09-08

The [broker verification manifest](broker-verification-results.json) records 121 passing tests and 23 subtests with all eight live Docker checks enabled. Actual bounded probes confirmed that a 256 MiB allocation in the 128 MiB/no-swap container triggers OOM exit 137, and that its 32-PID ceiling blocks excess children. The bootstrap verifies effective UID/capabilities/seccomp/no-new-privileges, cgroup limits, loopback-only network and read-only root before any candidate code runs.

Separate clean candidate and validation containers, host/credential exclusion, timeout/output bounds, interruption cleanup and owned-resource reconciliation passed. A real two-case process gate accepted an exact published candidate and survived ledger reopen. The original output-flood cleanup failure and subsequent successful runs are retained under `.gflo/evidence/broker-qualification-*`. The final evidence manifest pins source and artifact hashes; raw local data is ignored by Git.

The existing vLLM service remains running; no model/configuration change was made in this slice. The initial Stage 0 prerequisite is complete for these exact profiles. General repository/build capabilities, source-scope validation, the model worker loop, broad security evaluation and unattended supervision remain outside this qualification.
