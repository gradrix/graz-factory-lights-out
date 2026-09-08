# GFLO model-serving dependency

Small launcher, not the factory worker engine. Python 3.10+ standard library on Linux/macOS; no Python packages to install. Run commands from the repository root.

Local models are first-class. **External** means the server is managed elsewhere, not necessarily in the cloud: an existing local SGLang/vLLM server or an SSH-forwarded GPU host is the primary use case. No automatic cloud fallback, provider selection, or repository upload is implemented.

## Existing local endpoint (default)

```sh
python3 scripts/serve.py config
python3 scripts/serve.py doctor
python3 scripts/serve.py up
python3 scripts/serve.py smoke-test --structured
```

The example expects `http://127.0.0.1:30000/v1` to advertise model ID `gflo-local`. Copy `infra/serving/external.example.json` to `infra/serving/external.local.json` and set the actual URL/model if different; pass `--config infra/serving/external.local.json` to each command. Local configuration files are ignored by Git.

`config` validates configuration without connecting. `doctor` and `status` check `/v1/models`; `up` waits for that readiness check and does not provision anything in external mode. Model-list readiness does not prove the GPU is warm or inference works. `smoke-test` explicitly sends one fixed synthetic prompt to `/v1/chat/completions`, with a 256-token output cap. `--structured` also requests JSON-schema output. The response must finish normally and contain exactly the requested JSON. A reasoning model exhausting that small cap may fail this probe without being unusable; investigate its response mode before changing the probe budget. A passing probe is not a coding-quality or comprehensive schema benchmark.

External `down` refuses to stop or modify the server. For providers without a compatible model-list/chat endpoint or supported request fields, this initial client is insufficient: add and validate a focused integration rather than pretending protocol compatibility.

## Remote endpoint (explicit opt-in)

Set `allow_remote: true`, an HTTPS `base_url`, and optionally `api_key_env` to the **name** of an environment variable containing the credential. Do not put the token itself in JSON. Provide the variable through your shell/secret manager. Missing configured credentials fail without falling back to anonymous access.

For a private GPU server using HTTP, prefer an SSH tunnel and the loopback configuration. The launcher does not establish SSH sessions. Non-loopback HTTP is rejected; TLS verification remains enabled. HTTP redirects and ambient proxy environment variables are deliberately disabled to avoid unintentionally forwarding credentials. HTTPS host names and certificates must be trusted by the operator; `allow_remote` is not a general egress-security mechanism.

Remote smoke tests may incur provider charges. Readiness checks send no generation prompt, but provider-specific billing policies are outside this script's control. No product source is read or transmitted. Future factory use of remote models must separately authorize what product data may leave the host; enabling this dependency alone does not grant that authority.

## Selected RTX 5090 profile

**Keep vLLM as the working default for the first worker pilot.** Both engines passed conservative synthetic 8K/16K checks; neither was tuned to establish a performance winner. Free VRAM differs with cache reservation and memory fractions, so the earlier headroom-based ranking is withdrawn. The existing vLLM service has managed-lifecycle/recovery evidence. Further tuning follows representative Worker turns; see the [tuning review](../../.scratch/local-lights-out-factory/serving-tuning-review.md).

```sh
python3 scripts/serve.py up --config infra/serving/vllm-5090.example.json
python3 scripts/serve.py smoke-test --structured --config infra/serving/vllm-5090.example.json
python3 scripts/serve.py status --config infra/serving/vllm-5090.example.json
python3 scripts/serve.py down --config infra/serving/vllm-5090.example.json
```

The [vLLM profile](vllm-5090.example.json) and [SGLang alternative](sglang-5090.example.json) pin the measured image and Inferact checkpoint. Both expect this target's existing `local-vllm-huggingface-cache` volume, mounted read-only with offline model/tokenizer loading. They share port 30000 and one GPU: stop the active engine before switching. The selected managed vLLM service is `gflo-vllm`. Its launcher path is live-qualified. The SGLang alternative is configuration-validated; the live comparison used direct pinned-snapshot containers.

These target-specific profiles are not automatic provisioning recipes for an empty machine. Verify the cache volume on a new host. For an intentional first download, select an owned model-cache volume and set `offline` to false in a local configuration. Offline mode requires an existing cache and forbids Hub credentials; it applies to model/tokenizer access, while the launcher still checks/pulls the pinned Docker image when creating a container. No checkpoint conversion or editing is performed.

The service supports a 16K total context envelope; Worker views should still use the accepted 8K routine policy until the pilot calibrates them. BF16 KV cache avoids the uncalibrated FP8-scale warning observed with this checkpoint. A cold first generation can compile kernels for around a minute even after `/models` is ready, so the measured profiles allow 120-second requests and use explicit synthetic warm-up. Do not treat API readiness alone as warmed inference.

To repeat the serial synthetic workload against the running service, copy the external example into an ignored local configuration and use a 120-second request timeout:

```sh
python3 scripts/benchmark_serving.py --config infra/serving/benchmark.local.json \
  --context-tier 16384 --output .gflo/evidence/new-serving-run
```

The output directory must be new. The script retains requests, responses, verdicts, latency and sampled total-device VRAM. Tool calls are checked but not executed; no product source is sent. To compare the 8K tier, start the engine with an 8,192-token limit first.

## Managed inference on the NVIDIA host

Managed mode is Linux/NVIDIA only. The Docker daemon must be local to that GPU host; remote Docker contexts are not supported by this initial launcher. Docker, the NVIDIA driver and the container toolkit must already be provisioned. This script does not install drivers, change Docker configuration, or attempt CPU fallback.

1. Copy `managed.example.json` to `managed.local.json`.
2. Set `managed.image` to a selected SGLang `repository@sha256:digest`, or supply it through `GFLO_SERVING_IMAGE`. A mutable tag or `latest` is rejected. **The supplied placeholder intentionally cannot launch.** Select the image against the exact checkpoint and GPU during target verification.
3. Review the pinned model repository/revision, GPU index, context length, memory fraction and server options. The example checkpoint revision comes from prior research; it has not been downloaded or verified on this host. Settings are experimental starting points, not a working RTX 5090 recipe. Additional allowed options include `quantization`, `kv-cache-dtype`, and `attention-backend`; tune them only against measured compatibility and quality.
4. Run:

```sh
python3 scripts/serve.py doctor --config infra/serving/managed.local.json
python3 scripts/serve.py up --config infra/serving/managed.local.json
python3 scripts/serve.py status --config infra/serving/managed.local.json
python3 scripts/serve.py smoke-test --structured --config infra/serving/managed.local.json
```

On first start, Docker pulls the exact image digest and the selected backend downloads/loads the pinned Hub checkpoint, unless offline model loading is configured. A named Docker volume retains the Hub cache across container replacement. `--revision` pins the checkpoint; selecting an image/checkpoint that actually works together is still required. The launcher does not enable `trust_remote_code`. Public checkpoints need no token. For gated/private ones, configure `managed.hf_token_env` with the variable name; its value is passed via the child environment, not command arguments. Docker administrators can inspect container environment secrets, so use scoped credentials and do not expose the daemon to workers. Credential values are not part of the configuration fingerprint; rotating one requires deliberate container recreation, not merely rerunning `up`.

The service binds only `127.0.0.1`, exposes one GPU, serializes inference, drops capabilities, avoids host IPC/privileged mode and has bounded Docker log rotation. Host resource defaults are 36 GiB memory with no extra swap allowance, three CPUs and 1,024 PIDs; the managed profile can set explicit limits. Kernel/runtime caches persist in service-owned volumes. This is infrastructure, **not the sandbox for untrusted coding workers**. Loopback is not per-user authentication. Local users with host access may reach it. The preflight checks host Docker/driver/GPU visibility but do not prove container GPU access, model fit, sufficient Docker-volume space, or enforced host resource limits. Verify those on the target before an unattended workload. Disk reserves and complete resource admission belong to the later factory stage.

## Lifecycle behavior

- Matching running container: reuse and check readiness; do not pull or restart.
- Matching stopped container: start the existing container.
- Different configuration while running: refuse replacement. Drain active clients, then explicitly `down` before `up`.
- Different configuration while stopped: pull the new image first, remove only the verified GFLO-owned container by ID, and create its replacement. The old container is removed (not recoverable as a container); its named model cache remains. This is not a rollback mechanism.
- Existing foreign container with the same name: refuse to adopt, stop or remove it.
- Repeated `down`: safe no-op once stopped; never remove volumes or use Docker prune.
- Concurrent local launcher calls: a per-user/per-service advisory lock prevents overlapping mutations. It does not coordinate other users or independent Docker tools.

`down` is an explicit stop, not automatic request draining. `up` never drains clients or restarts a matching unhealthy server automatically. Docker's `unless-stopped` policy did recover an internal vLLM EngineCore crash in the target test; an explicit manual `docker kill` suppressed that policy and required `up` to resume. Investigate failures using `docker logs --tail 100 gflo-sglang` on the GPU host; do not paste secrets into reports. Interrupted startup can be resumed with `up`, but a configuration drift still follows the rules above. Startup/readiness deadlines are configurable. Docker command failures suppress output to avoid printing credentials; inspect Docker directly when troubleshooting.

## Verification performed here

```sh
python3 -m unittest discover -s tests -p 'test_serving.py' -v
python3 scripts/serve.py config
```

Tests use fake Docker responses and a loopback HTTP fixture. They cover configuration restrictions, idempotent reuse, stopped-container restart, running drift rejection, ownership checks, request shape, key handling, redirect rejection and startup failures. They do **not** launch SGLang, pull images/weights, test GPU access, or qualify Qwen/RTX performance. No factory implementation stage is marked complete by these tests.

## Primary references

- [SGLang Docker installation](https://docs.sglang.io/docs/get-started/install)
- [SGLang server arguments](https://sgl-project.github.io/advanced_features/server_arguments.html)
- [SGLang structured outputs](https://docs.sglang.io/docs/advanced_features/structured_outputs)

Two focused managed profiles are implemented: SGLang (the legacy default when `backend` is omitted) and vLLM. This is not a general backend plugin system. vLLM uses eager text-only execution, one request in flight, 2K prefill chunks, no prefix caching, and an explicitly pinned tokenizer revision. SGLang's additional allowlisted options/flags cover the measured hybrid-attention profile. Configuration fingerprints include backend, caches, options and limits.

The unit tests remain GPU-free. Actual startup, synthetic inference, context and recovery observations are recorded separately in the [serving comparison](../../.scratch/local-lights-out-factory/serving-comparison.md).

The opt-in `vllm-5090-graphs.example.json` profile uses the same model/runtime
and limits, with `managed.enforce_eager: false` enabling vLLM compilation and
CUDA-graph defaults. The default remains eager when the key is absent.
Do not run both GPU containers together; stop the active profile before starting
the other. Graph startup/coding measurements are in
[the pilot report](../../.scratch/local-lights-out-factory/pilot-results.md).

To deliberately qualify an idle owned vLLM service's stopped restart, configuration
drift refusal and internal engine-crash recovery:

```sh
python3 scripts/check_serving_recovery.py \
  --config infra/serving/vllm-5090-graphs.example.json \
  --output .gflo/evidence/NEW_RECOVERY_RUN
```

This interrupts the service and holds launcher/local-worker endpoint locks. It
retains snapshots and smoke results in a new directory and attempts to leave the
service ready even after failure. It does not qualify an in-flight Work atom or
host reboot. [Measured graph recovery](../../.scratch/local-lights-out-factory/graph-recovery-verification.json)
passed; the broader fault campaign remains separate.
